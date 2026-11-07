package app

import (
	"bytes"
	"context"
	"encoding/hex"
	"encoding/json"
	"fmt"
	"math"
	"sort"
	"strings"
	"sync"

	abcitypes "github.com/cometbft/cometbft/abci/types"
)

const (
	statusSuccess         = "success"
	statusFailedConsensus = "failed_consensus"

	reasonInconsistentView   = "inconsistent_view"
	currentSchemaVersion     = "current-consensus-v2"
	currentMeasurementDomain = "loop_current_ma"
	currentSpanMA            = 16.0
)

type sensorOrder struct {
	Name string
	Unit string
}

type ConsensusApplication struct {
	statePath          string
	mu                 sync.Mutex
	state              PersistedState
	pendingRounds      map[string]CommittedRound
	pendingBlockHeight int64
	pendingAppHash     []byte
}

var _ abcitypes.Application = (*ConsensusApplication)(nil)

func NewConsensusApplication(statePath string) (*ConsensusApplication, error) {
	state, err := loadState(statePath)
	if err != nil {
		return nil, err
	}
	return &ConsensusApplication{
		statePath:     statePath,
		state:         state,
		pendingRounds: map[string]CommittedRound{},
	}, nil
}

func (app *ConsensusApplication) Info(_ context.Context, _ *abcitypes.InfoRequest) (*abcitypes.InfoResponse, error) {
	app.mu.Lock()
	defer app.mu.Unlock()
	return &abcitypes.InfoResponse{
		LastBlockHeight:  app.state.LastBlockHeight,
		LastBlockAppHash: app.state.LastAppHash,
	}, nil
}

func (app *ConsensusApplication) Query(_ context.Context, req *abcitypes.QueryRequest) (*abcitypes.QueryResponse, error) {
	app.mu.Lock()
	defer app.mu.Unlock()

	roundID := string(req.Data)
	round, ok := app.state.Rounds[roundID]
	if !ok {
		return &abcitypes.QueryResponse{Code: 1, Log: "round not found"}, nil
	}
	raw, err := json.Marshal(round)
	if err != nil {
		return nil, err
	}
	return &abcitypes.QueryResponse{Code: 0, Value: raw}, nil
}

func (app *ConsensusApplication) CheckTx(_ context.Context, req *abcitypes.CheckTxRequest) (*abcitypes.CheckTxResponse, error) {
	var tx RoundInputTx
	if err := json.Unmarshal(req.Tx, &tx); err != nil {
		return &abcitypes.CheckTxResponse{Code: 1, Log: err.Error()}, nil
	}
	if err := validateRoundInput(tx); err != nil {
		return &abcitypes.CheckTxResponse{Code: 1, Log: err.Error()}, nil
	}
	app.mu.Lock()
	defer app.mu.Unlock()
	if app.hasLegacyRounds() {
		return &abcitypes.CheckTxResponse{Code: 1, Log: "legacy state requires a fresh current-domain session"}, nil
	}
	return &abcitypes.CheckTxResponse{Code: 0}, nil
}

func (app *ConsensusApplication) InitChain(_ context.Context, _ *abcitypes.InitChainRequest) (*abcitypes.InitChainResponse, error) {
	return &abcitypes.InitChainResponse{}, nil
}

func (app *ConsensusApplication) PrepareProposal(_ context.Context, req *abcitypes.PrepareProposalRequest) (*abcitypes.PrepareProposalResponse, error) {
	return &abcitypes.PrepareProposalResponse{Txs: req.Txs}, nil
}

func (app *ConsensusApplication) ProcessProposal(_ context.Context, _ *abcitypes.ProcessProposalRequest) (*abcitypes.ProcessProposalResponse, error) {
	return &abcitypes.ProcessProposalResponse{Status: abcitypes.PROCESS_PROPOSAL_STATUS_ACCEPT}, nil
}

func (app *ConsensusApplication) FinalizeBlock(_ context.Context, req *abcitypes.FinalizeBlockRequest) (*abcitypes.FinalizeBlockResponse, error) {
	app.mu.Lock()
	defer app.mu.Unlock()

	txResults := make([]*abcitypes.ExecTxResult, len(req.Txs))
	app.pendingRounds = map[string]CommittedRound{}
	app.pendingBlockHeight = req.Height
	app.pendingAppHash = nil

	for idx, rawTx := range req.Txs {
		var tx RoundInputTx
		if err := json.Unmarshal(rawTx, &tx); err != nil {
			txResults[idx] = &abcitypes.ExecTxResult{Code: 1, Log: err.Error()}
			continue
		}

		if app.hasLegacyRounds() {
			txResults[idx] = &abcitypes.ExecTxResult{Code: 1, Log: "legacy state requires a fresh current-domain session"}
			continue
		}
		round, err := evaluateRound(tx, req.Height)
		if err != nil {
			txResults[idx] = &abcitypes.ExecTxResult{Code: 1, Log: err.Error()}
			continue
		}
		app.pendingRounds[tx.RoundID] = round
		txResults[idx] = &abcitypes.ExecTxResult{
			Code: 0,
			Log:  fmt.Sprintf("committed round %s status=%s", round.RoundID, round.FinalStatus),
		}
	}

	pendingState := PersistedState{
		LastBlockHeight: req.Height,
		Rounds:          cloneRounds(app.state.Rounds),
	}
	for roundID, round := range app.pendingRounds {
		pendingState.Rounds[roundID] = round
	}
	appHash, err := computeAppHash(pendingState)
	if err != nil {
		return nil, err
	}
	app.pendingAppHash = appHash

	fmt.Printf(
		"ABCI_PRECOMMIT state_path=%s height=%d app_hash=%s pending_rounds=%s\n",
		app.statePath,
		req.Height,
		hex.EncodeToString(appHash),
		strings.Join(sortedCommittedRoundIDs(app.pendingRounds), ","),
	)

	return &abcitypes.FinalizeBlockResponse{
		TxResults: txResults,
		AppHash:   appHash,
	}, nil
}

func (app *ConsensusApplication) Commit(_ context.Context, _ *abcitypes.CommitRequest) (*abcitypes.CommitResponse, error) {
	app.mu.Lock()
	defer app.mu.Unlock()

	for roundID, round := range app.pendingRounds {
		app.state.Rounds[roundID] = round
	}
	app.state.LastBlockHeight = app.pendingBlockHeight

	appHash, err := persistState(app.statePath, app.state)
	if err != nil {
		return nil, err
	}
	if len(app.pendingAppHash) > 0 && !bytes.Equal(appHash, app.pendingAppHash) {
		return nil, fmt.Errorf(
			"persisted app hash %s does not match precommit app hash %s",
			hex.EncodeToString(appHash),
			hex.EncodeToString(app.pendingAppHash),
		)
	}
	app.state.LastAppHash = appHash
	fmt.Printf(
		"ABCI_COMMIT state_path=%s height=%d app_hash=%s rounds=%s\n",
		app.statePath,
		app.state.LastBlockHeight,
		hex.EncodeToString(appHash),
		strings.Join(sortedCommittedRoundIDs(app.state.Rounds), ","),
	)
	return &abcitypes.CommitResponse{RetainHeight: app.state.LastBlockHeight}, nil
}

func (app *ConsensusApplication) ListSnapshots(_ context.Context, _ *abcitypes.ListSnapshotsRequest) (*abcitypes.ListSnapshotsResponse, error) {
	return &abcitypes.ListSnapshotsResponse{}, nil
}

func (app *ConsensusApplication) OfferSnapshot(_ context.Context, _ *abcitypes.OfferSnapshotRequest) (*abcitypes.OfferSnapshotResponse, error) {
	return &abcitypes.OfferSnapshotResponse{}, nil
}

func (app *ConsensusApplication) LoadSnapshotChunk(_ context.Context, _ *abcitypes.LoadSnapshotChunkRequest) (*abcitypes.LoadSnapshotChunkResponse, error) {
	return &abcitypes.LoadSnapshotChunkResponse{}, nil
}

func (app *ConsensusApplication) ApplySnapshotChunk(_ context.Context, _ *abcitypes.ApplySnapshotChunkRequest) (*abcitypes.ApplySnapshotChunkResponse, error) {
	return &abcitypes.ApplySnapshotChunkResponse{Result: abcitypes.APPLY_SNAPSHOT_CHUNK_RESULT_ACCEPT}, nil
}

func (app *ConsensusApplication) ExtendVote(_ context.Context, _ *abcitypes.ExtendVoteRequest) (*abcitypes.ExtendVoteResponse, error) {
	return &abcitypes.ExtendVoteResponse{}, nil
}

func (app *ConsensusApplication) VerifyVoteExtension(_ context.Context, _ *abcitypes.VerifyVoteExtensionRequest) (*abcitypes.VerifyVoteExtensionResponse, error) {
	return &abcitypes.VerifyVoteExtensionResponse{Status: abcitypes.VERIFY_VOTE_EXTENSION_STATUS_ACCEPT}, nil
}

func evaluateRound(tx RoundInputTx, height int64) (CommittedRound, error) {
	if err := validateRoundInput(tx); err != nil {
		return CommittedRound{}, err
	}
	stateByEdge := map[string]ReplicatedState{}
	for _, state := range tx.ReplicatedStates {
		stateByEdge[state.OwnerEdgeID] = state
	}

	pairwise := map[string]float64{}
	for _, edgeID := range tx.ParticipatingEdges {
		for _, peerID := range tx.ParticipatingEdges {
			if edgeID == peerID {
				continue
			}
			distance, err := normalizedPairDistance(stateByEdge[edgeID], stateByEdge[peerID])
			if err != nil {
				return CommittedRound{}, err
			}
			pairwise[edgeID+"->"+peerID] = distance
		}
	}

	quorum := 2*len(tx.ParticipatingEdges)/3 + 1
	ranking := make([]TrustRankEntry, 0, len(tx.ParticipatingEdges))
	exclusions := []ExclusionDecision{}
	trustEvidence := make([]PerEdgeTrustEvidence, 0, len(tx.ParticipatingEdges))

	for _, edgeID := range tx.ParticipatingEdges {
		state := stateByEdge[edgeID]
		peerIDs := []string{}
		for _, peerID := range tx.ParticipatingEdges {
			if peerID != edgeID {
				peerIDs = append(peerIDs, peerID)
			}
		}
		sort.Strings(peerIDs)

		sensorNames := []string{}
		for sensorName := range state.SensorValues {
			sensorNames = append(sensorNames, sensorName)
		}
		sort.Strings(sensorNames)

		sensorDeviations := []SensorDeviationEvidence{}
		pairwiseDistances := []PairwiseDistanceEvidence{}
		for _, sensorName := range sensorNames {
			selfSensor := state.SensorValues[sensorName]
			totalDistance := 0.0
			for _, peerID := range peerIDs {
				peerSensor := stateByEdge[peerID].SensorValues[sensorName]
				distance := math.Abs(selfSensor.Value - peerSensor.Value)
				if math.IsInf(distance, 0) || math.IsInf(totalDistance+distance, 0) {
					return CommittedRound{}, fmt.Errorf("current diagnostic distance overflow")
				}
				totalDistance += distance
				pairwiseDistances = append(pairwiseDistances, PairwiseDistanceEvidence{
					PeerEdgeID:    peerID,
					SensorName:    sensorName,
					DistanceValue: round(distance),
					Unit:          selfSensor.Unit,
				})
			}
			meanDistance := 0.0
			if len(peerIDs) > 0 {
				meanDistance = totalDistance / float64(len(peerIDs))
			}
			sensorDeviations = append(sensorDeviations, SensorDeviationEvidence{
				SensorName:     sensorName,
				DeviationValue: round(meanDistance),
				Unit:           selfSensor.Unit,
			})
		}

		compatiblePeers := 0
		totalPairwise := 0.0
		for _, peerID := range peerIDs {
			normalized := pairwise[edgeID+"->"+peerID]
			totalPairwise += normalized
			if math.IsInf(totalPairwise, 0) {
				return CommittedRound{}, fmt.Errorf("current diagnostic aggregate overflow")
			}
			if compatibleStates(state, stateByEdge[peerID]) {
				compatiblePeers++
			}
		}
		overallDeviation := 0.0
		if len(peerIDs) > 0 {
			overallDeviation = round(totalPairwise / float64(len(peerIDs)))
		}
		score := round(1.0 / (1.0 + overallDeviation))
		ranking = append(ranking, TrustRankEntry{EdgeID: edgeID, Score: score})

		evidence := PerEdgeTrustEvidence{
			EdgeID:                     edgeID,
			Score:                      score,
			CompatiblePeerCount:        compatiblePeers,
			OverallNormalizedDeviation: overallDeviation,
			SensorDeviations:           sensorDeviations,
			PairwiseDistances:          pairwiseDistances,
		}
		trustEvidence = append(trustEvidence, evidence)

		if compatiblePeers+1 < quorum {
			reason := reasonInconsistentView
			details := []string{
				fmt.Sprintf("compatible_peers=%d", compatiblePeers),
				fmt.Sprintf("overall_normalized_deviation=%.3f", overallDeviation),
			}
			for _, deviation := range sensorDeviations {
				scale := currentSpanMA
				details = append(
					details,
					fmt.Sprintf(
						"%s:%.3f%s(norm=%.3f)",
						deviation.SensorName,
						deviation.DeviationValue,
						deviation.Unit,
						deviation.DeviationValue/scale,
					),
				)
			}
			exclusions = append(exclusions, ExclusionDecision{
				EdgeID: edgeID,
				Reason: reason,
				Detail: strings.Join(details, ", "),
			})
		}
	}

	sort.Slice(ranking, func(i, j int) bool {
		if ranking[i].Score == ranking[j].Score {
			return ranking[i].EdgeID < ranking[j].EdgeID
		}
		return ranking[i].Score > ranking[j].Score
	})
	sort.Slice(trustEvidence, func(i, j int) bool { return trustEvidence[i].EdgeID < trustEvidence[j].EdgeID })
	sort.Slice(exclusions, func(i, j int) bool { return exclusions[i].EdgeID < exclusions[j].EdgeID })

	excludedEdges := map[string]struct{}{}
	for _, exclusion := range exclusions {
		excludedEdges[exclusion.EdgeID] = struct{}{}
	}

	validEdges := []string{}
	for _, edgeID := range tx.ParticipatingEdges {
		if _, excluded := excludedEdges[edgeID]; !excluded {
			validEdges = append(validEdges, edgeID)
		}
	}
	sort.Strings(validEdges)

	finalStatus := statusFailedConsensus
	var validState *ConsensusedValidState
	if len(validEdges) >= quorum {
		finalStatus = statusSuccess
		validState = buildValidState(stateByEdge, validEdges)
	}

	return CommittedRound{
		SchemaVersion: currentSchemaVersion, MeasurementDomain: currentMeasurementDomain,
		RoundID:               tx.RoundID,
		WindowStartedAt:       tx.WindowStartedAt,
		WindowEndedAt:         tx.WindowEndedAt,
		ParticipatingEdges:    append([]string(nil), tx.ParticipatingEdges...),
		ReplicatedStates:      append([]ReplicatedState(nil), tx.ReplicatedStates...),
		TrustRanking:          ranking,
		Exclusions:            exclusions,
		TrustEvidence:         trustEvidence,
		FinalStatus:           finalStatus,
		ConsensusedValidState: validState,
		CommitHeight:          height,
	}, nil
}

func validateRoundInput(tx RoundInputTx) error {
	if tx.SchemaVersion != currentSchemaVersion || tx.MeasurementDomain != currentMeasurementDomain {
		return fmt.Errorf("requires current-consensus-v2 schema and loop_current_ma measurement domain")
	}
	if tx.RoundID == "" || len(tx.ParticipatingEdges) == 0 || len(tx.ReplicatedStates) != len(tx.ParticipatingEdges) {
		return fmt.Errorf("invalid round tx")
	}
	participants := map[string]bool{}
	for _, id := range tx.ParticipatingEdges {
		if strings.TrimSpace(id) == "" || participants[id] {
			return fmt.Errorf("invalid or duplicate participant")
		}
		participants[id] = true
	}
	seen := map[string]bool{}
	var schema map[string]SensorValue
	for _, state := range tx.ReplicatedStates {
		if !participants[state.OwnerEdgeID] || seen[state.OwnerEdgeID] {
			return fmt.Errorf("invalid or duplicate replicated owner")
		}
		seen[state.OwnerEdgeID] = true
		if len(state.SensorValues) == 0 {
			return fmt.Errorf("empty sensor schema")
		}
		if schema == nil {
			schema = state.SensorValues
		}
		if len(schema) != len(state.SensorValues) {
			return fmt.Errorf("replicated sensor schemas differ")
		}
		for name, value := range state.SensorValues {
			if _, ok := schema[name]; !ok || strings.TrimSpace(name) == "" {
				return fmt.Errorf("replicated sensor schemas differ")
			}
			if value.Unit != "mA" || strings.TrimSpace(value.SourceEventID) == "" || math.IsNaN(value.Value) || math.IsInf(value.Value, 0) {
				return fmt.Errorf("sensor %s requires finite acquired mA and source_event_id", name)
			}
		}
	}
	return nil
}

func (app *ConsensusApplication) hasLegacyRounds() bool {
	for _, r := range app.state.Rounds {
		if r.SchemaVersion != currentSchemaVersion || r.MeasurementDomain != currentMeasurementDomain {
			return true
		}
	}
	return false
}

func compatibleStates(left, right ReplicatedState) bool {
	if len(left.SensorValues) != len(right.SensorValues) {
		return false
	}
	for name, value := range left.SensorValues {
		other, ok := right.SensorValues[name]
		if !ok || value != other {
			return false
		}
	}
	return true
}

func normalizedPairDistance(left ReplicatedState, right ReplicatedState) (float64, error) {
	if len(left.SensorValues) == 0 || len(left.SensorValues) != len(right.SensorValues) {
		return 0, fmt.Errorf("replicated sensor schemas differ")
	}
	names := make([]string, 0, len(left.SensorValues))
	for name := range left.SensorValues {
		names = append(names, name)
	}
	sort.Strings(names)
	total := 0.0
	for _, name := range names {
		other, ok := right.SensorValues[name]
		if !ok {
			return 0, fmt.Errorf("replicated sensor schemas differ")
		}
		difference := math.Abs(left.SensorValues[name].Value - other.Value)
		if math.IsInf(difference, 0) || math.IsInf(total+difference/currentSpanMA, 0) {
			return 0, fmt.Errorf("current diagnostic distance overflow")
		}
		total += difference / currentSpanMA
	}
	return total / float64(len(names)), nil
}

func buildValidState(stateByEdge map[string]ReplicatedState, validEdges []string) *ConsensusedValidState {
	values := map[string]float64{}
	for name, value := range stateByEdge[validEdges[0]].SensorValues {
		values[name] = value.Value
	}
	return &ConsensusedValidState{MeasurementDomain: currentMeasurementDomain, SourceEdges: append([]string(nil), validEdges...), SensorValues: values}
}

func round(value float64) float64 {
	// At this magnitude adjacent binary64 numbers are farther apart than 0.001.
	// Multiplying such a value by 1000 can overflow without adding precision.
	if math.Abs(value) >= 1<<43 {
		return value
	}
	return math.Round(value*1000) / 1000
}

func cloneRounds(rounds map[string]CommittedRound) map[string]CommittedRound {
	cloned := make(map[string]CommittedRound, len(rounds))
	for roundID, round := range rounds {
		cloned[roundID] = round
	}
	return cloned
}

func sortedCommittedRoundIDs(rounds map[string]CommittedRound) []string {
	roundIDs := make([]string, 0, len(rounds))
	for roundID := range rounds {
		roundIDs = append(roundIDs, roundID)
	}
	sort.Strings(roundIDs)
	return roundIDs
}
