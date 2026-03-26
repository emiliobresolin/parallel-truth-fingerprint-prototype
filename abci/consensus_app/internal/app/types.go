package app

type RoundInputTx struct {
	RoundID            string            `json:"round_id"`
	WindowStartedAt    string            `json:"window_started_at"`
	WindowEndedAt      string            `json:"window_ended_at"`
	ParticipatingEdges []string          `json:"participating_edges"`
	ReplicatedStates   []ReplicatedState `json:"replicated_states"`
}

type ReplicatedState struct {
	OwnerEdgeID  string                 `json:"owner_edge_id"`
	SensorValues map[string]SensorValue `json:"sensor_values"`
}

type SensorValue struct {
	Value float64 `json:"value"`
	Unit  string  `json:"unit"`
}

type TrustRankEntry struct {
	EdgeID string  `json:"edge_id"`
	Score  float64 `json:"score"`
}

type ExclusionDecision struct {
	EdgeID string `json:"edge_id"`
	Reason string `json:"reason"`
	Detail string `json:"detail,omitempty"`
}

type SensorDeviationEvidence struct {
	SensorName     string  `json:"sensor_name"`
	DeviationValue float64 `json:"deviation_value"`
	Unit           string  `json:"unit"`
}

type PairwiseDistanceEvidence struct {
	PeerEdgeID    string  `json:"peer_edge_id"`
	SensorName    string  `json:"sensor_name"`
	DistanceValue float64 `json:"distance_value"`
	Unit          string  `json:"unit"`
}

type PerEdgeTrustEvidence struct {
	EdgeID                     string                     `json:"edge_id"`
	Score                      float64                    `json:"score"`
	CompatiblePeerCount        int                        `json:"compatible_peer_count"`
	OverallNormalizedDeviation float64                    `json:"overall_normalized_deviation"`
	SensorDeviations           []SensorDeviationEvidence  `json:"sensor_deviations"`
	PairwiseDistances          []PairwiseDistanceEvidence `json:"pairwise_distances"`
}

type ConsensusedValidState struct {
	SourceEdges  []string           `json:"source_edges"`
	SensorValues map[string]float64 `json:"sensor_values"`
}

type CommittedRound struct {
	RoundID               string                 `json:"round_id"`
	WindowStartedAt       string                 `json:"window_started_at"`
	WindowEndedAt         string                 `json:"window_ended_at"`
	ParticipatingEdges    []string               `json:"participating_edges"`
	ReplicatedStates      []ReplicatedState      `json:"replicated_states"`
	TrustRanking          []TrustRankEntry       `json:"trust_ranking"`
	Exclusions            []ExclusionDecision    `json:"exclusions"`
	TrustEvidence         []PerEdgeTrustEvidence `json:"trust_evidence"`
	FinalStatus           string                 `json:"final_status"`
	ConsensusedValidState *ConsensusedValidState `json:"consensused_valid_state"`
	CommitHeight          int64                  `json:"commit_height"`
}

type PersistedState struct {
	LastBlockHeight int64                     `json:"last_block_height"`
	LastAppHash     []byte                    `json:"last_app_hash"`
	Rounds          map[string]CommittedRound `json:"rounds"`
}
