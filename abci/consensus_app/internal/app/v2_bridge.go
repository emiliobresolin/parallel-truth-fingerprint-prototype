package app

// This file is deliberately not wired into ConsensusApplication.  It is the
// versioned, in-memory shadow boundary for Consensus.v2; v1 ABCI state and
// AppHash are consequently unable to observe or mutate v2 traffic.

import (
	"bytes"
	"context"
	"crypto/sha256"
	"encoding/hex"
	"encoding/json"
	"errors"
	"io"
	"regexp"
	"sort"
	"strings"
)

const (
	consensusV2EnvelopeSchema = "ConsensusABCI.v2"
	consensusV2Schema         = "Consensus.v2"
	consensusV2ShadowRoute    = "consensus_v2_shadow"
)

var v2Digest = regexp.MustCompile(`^sha256:[0-9a-f]{64}$`)

// ConsensusV2Envelope is a closed transaction wrapper.  Each identity is
// pinned by content hash; labels, aliases and current-state lookups have no
// representation at this boundary.
type ConsensusV2Envelope struct {
	SchemaVersion       string          `json:"schema_version"`
	Route               string          `json:"route"`
	RoundInput          json.RawMessage `json:"round_input"`
	ParameterSetID      string          `json:"parameter_set_id"`
	OperationRegistryID string          `json:"operation_registry_id"`
	AuthorizationEffect string          `json:"authorization_effect"`
}

// ConsensusV2Evaluator is injected by the caller. It must be a closed,
// pinned evaluator; the bridge never resolves a plugin, service, state or
// mutable external reference itself.
type ConsensusV2Evaluator interface {
	EvaluateConsensusV2(context.Context, ConsensusV2Envelope) ([]byte, error)
}

// ConsensusV2ShadowAdapter decodes and evaluates one v2 transaction without
// ABCI state, Query, persistence, control authority, or route activation.
type ConsensusV2ShadowAdapter struct{ evaluator ConsensusV2Evaluator }

func NewConsensusV2ShadowAdapter(evaluator ConsensusV2Evaluator) (*ConsensusV2ShadowAdapter, error) {
	if evaluator == nil {
		return nil, errors.New("CV2_EVALUATOR_REQUIRED")
	}
	return &ConsensusV2ShadowAdapter{evaluator: evaluator}, nil
}

func DecodeConsensusV2Envelope(raw []byte) (ConsensusV2Envelope, error) {
	value, err := decodeCanonicalJSON(raw)
	if err != nil {
		return ConsensusV2Envelope{}, err
	}
	root, ok := value.(map[string]any)
	if !ok || !exactKeys(root, "schema_version", "route", "round_input", "parameter_set_id", "operation_registry_id", "authorization_effect") {
		return ConsensusV2Envelope{}, errors.New("CV2_ENVELOPE_FIELDS")
	}
	round, ok := root["round_input"].(map[string]any)
	if !ok {
		return ConsensusV2Envelope{}, errors.New("CV2_ROUND_INPUT_OBJECT")
	}
	roundRaw, err := json.Marshal(round)
	if err != nil {
		return ConsensusV2Envelope{}, errors.New("CV2_ROUND_INPUT_ENCODING")
	}
	envelope := ConsensusV2Envelope{
		SchemaVersion: stringValue(root["schema_version"]), Route: stringValue(root["route"]),
		RoundInput: roundRaw, ParameterSetID: stringValue(root["parameter_set_id"]),
		OperationRegistryID: stringValue(root["operation_registry_id"]), AuthorizationEffect: stringValue(root["authorization_effect"]),
	}
	if envelope.SchemaVersion != consensusV2EnvelopeSchema || envelope.Route != consensusV2ShadowRoute || envelope.AuthorizationEffect != "none" {
		return ConsensusV2Envelope{}, errors.New("CV2_ENVELOPE_VERSION")
	}
	if !v2Digest.MatchString(envelope.ParameterSetID) || !v2Digest.MatchString(envelope.OperationRegistryID) {
		return ConsensusV2Envelope{}, errors.New("CV2_ENVELOPE_IDENTITY")
	}
	if err := validateV2RoundInput(round); err != nil {
		return ConsensusV2Envelope{}, err
	}
	return envelope, nil
}

// Execute decodes first and turns every rejection or evaluator failure into a
// bounded no-ranking shadow result. The returned bytes are never persisted.
func (a *ConsensusV2ShadowAdapter) Execute(ctx context.Context, raw []byte) V2ShadowResponse {
	envelope, err := DecodeConsensusV2Envelope(raw)
	if err != nil {
		return V2ShadowResponse{Code: 1, Log: err.Error(), ShadowOnly: true}
	}
	decision, err := a.evaluator.EvaluateConsensusV2(ctx, envelope)
	if err != nil {
		return V2ShadowResponse{Code: 1, Log: "CV2_EVALUATION_FAILED", ShadowOnly: true}
	}
	if err := validateV2Decision(decision, envelope.RoundInput); err != nil {
		return V2ShadowResponse{Code: 1, Log: err.Error(), ShadowOnly: true}
	}
	return V2ShadowResponse{Code: 0, Log: "CV2_SHADOW_DECISION", DecisionBytes: append([]byte(nil), decision...), ShadowOnly: true}
}

type V2ShadowResponse struct {
	Code          uint32
	Log           string
	DecisionBytes []byte
	ShadowOnly    bool
}

func validateV2RoundInput(round map[string]any) error {
	if !exactKeys(round, "schema_version", "experiment_id", "run_id", "round_id", "qualification_result_id", "comparison_basis", "quality_policy_ids", "parameter_ids", "observations", "input_content_id", "authorization_effect") {
		return errors.New("CV2_INPUT_FIELDS")
	}
	if stringValue(round["schema_version"]) != consensusV2Schema || stringValue(round["authorization_effect"]) != "none" {
		return errors.New("CV2_INPUT_VERSION")
	}
	for _, key := range []string{"experiment_id", "run_id", "round_id", "qualification_result_id", "input_content_id"} {
		if !v2Digest.MatchString(stringValue(round[key])) {
			return errors.New("CV2_INPUT_IDENTITY")
		}
	}
	for _, key := range []string{"quality_policy_ids", "parameter_ids"} {
		if err := sortedDigests(round[key], key == "quality_policy_ids"); err != nil {
			return err
		}
	}
	basis, ok := round["comparison_basis"].(map[string]any)
	if !ok {
		return errors.New("CV2_BASIS_OBJECT")
	}
	if err := validateV2Basis(basis); err != nil {
		return err
	}
	observations, ok := round["observations"].([]any)
	if !ok || len(observations) == 0 {
		return errors.New("CV2_OBSERVATION_CLOSURE")
	}
	last := ""
	edges := map[string]bool{}
	for _, raw := range observations {
		item, ok := raw.(map[string]any)
		if !ok || !exactKeys(item, "edge_id", "observation_id", "observation_canonical_hash", "profile_id", "source_sequence", "correlation_id", "raw_current_unit") {
			return errors.New("CV2_OBSERVATION_FIELDS")
		}
		for _, key := range []string{"edge_id", "observation_id", "profile_id", "correlation_id", "observation_canonical_hash"} {
			if !v2Digest.MatchString(stringValue(item[key])) {
				return errors.New("CV2_OBSERVATION_IDENTITY")
			}
		}
		sequence, ok := item["source_sequence"].(json.Number)
		if !ok || !positiveInteger(sequence) || stringValue(item["raw_current_unit"]) != "mA" {
			return errors.New("CV2_OBSERVATION_VALUE")
		}
		order := stringValue(item["edge_id"]) + "\x00" + sequence.String() + "\x00" + stringValue(item["observation_id"])
		if order <= last || edges[stringValue(item["edge_id"])] {
			return errors.New("CV2_OBSERVATION_ORDER")
		}
		last, edges[stringValue(item["edge_id"])] = order, true
	}
	canonical, _ := json.Marshal(withoutKey(round, "input_content_id"))
	sum := sha256.Sum256(canonical)
	if stringValue(round["input_content_id"]) != "sha256:"+hex.EncodeToString(sum[:]) {
		return errors.New("CV2_INPUT_CONTENT_HASH")
	}
	return nil
}

func validateV2Basis(basis map[string]any) error {
	if !exactKeys(basis, "basis_id", "schema_version", "canonical_bytes", "canonical_bytes_hash", "kind", "unit", "profile_ids", "uncertainty_parameter_ids") {
		return errors.New("CV2_BASIS_FIELDS")
	}
	if !v2Digest.MatchString(stringValue(basis["basis_id"])) || stringValue(basis["schema_version"]) == "" {
		return errors.New("CV2_BASIS_IDENTITY")
	}
	canonical := stringValue(basis["canonical_bytes"])
	sum := sha256.Sum256([]byte(canonical))
	if stringValue(basis["canonical_bytes_hash"]) != "sha256:"+hex.EncodeToString(sum[:]) {
		return errors.New("CV2_BASIS_HASH")
	}
	profiles := basis["profile_ids"]
	uncertainty := basis["uncertainty_parameter_ids"]
	if err := sortedDigests(profiles, true); err != nil {
		return err
	}
	if err := sortedDigests(uncertainty, false); err != nil {
		return err
	}
	profileCount := len(profiles.([]any))
	uncertaintyCount := len(uncertainty.([]any))
	switch stringValue(basis["kind"]) {
	case "same_profile_raw_current":
		if stringValue(basis["unit"]) != "mA" || profileCount != 1 || uncertaintyCount != 0 {
			return errors.New("CV2_RAW_CURRENT_CLOSURE")
		}
	case "dimensionless_profile_residual":
		if stringValue(basis["unit"]) != "one" || profileCount < 2 || uncertaintyCount == 0 {
			return errors.New("CV2_RESIDUAL_CLOSURE")
		}
	default:
		return errors.New("CV2_BASIS_KIND")
	}
	return nil
}

func validateV2Decision(raw []byte, roundRaw []byte) error {
	value, err := decodeCanonicalJSON(raw)
	if err != nil {
		return err
	}
	decision, ok := value.(map[string]any)
	if !ok || !exactKeys(decision, "schema_version", "round_input_id", "round_input_hash", "comparison_basis", "outcome", "participant_ids", "included_ids", "excluded", "ranking", "diagnostics", "decision_content_id", "authorization_effect") {
		return errors.New("CV2_DECISION_FIELDS")
	}
	if stringValue(decision["schema_version"]) != consensusV2Schema || stringValue(decision["authorization_effect"]) != "none" {
		return errors.New("CV2_DECISION_VERSION")
	}
	basis, ok := decision["comparison_basis"].(map[string]any)
	if !ok {
		return errors.New("CV2_DECISION_BASIS")
	}
	if err := validateV2Basis(basis); err != nil {
		return err
	}
	roundValue, err := decodeCanonicalJSON(roundRaw)
	if err != nil {
		return errors.New("CV2_DECISION_INPUT")
	}
	round, ok := roundValue.(map[string]any)
	if !ok || stringValue(decision["round_input_id"]) != stringValue(round["input_content_id"]) || stringValue(decision["round_input_hash"]) != "sha256:"+hexDigest(roundRaw) {
		return errors.New("CV2_DECISION_INPUT")
	}
	participants, included := decision["participant_ids"], decision["included_ids"]
	if err := sortedDigests(participants, true); err != nil {
		return err
	}
	if err := sortedDigests(included, false); err != nil {
		return err
	}
	includedIDs, includedOK := included.([]any)
	ranking, rankingOK := decision["ranking"].([]any)
	excluded, excludedOK := decision["excluded"].([]any)
	diagnostics, diagnosticsOK := decision["diagnostics"].([]any)
	if !includedOK || !rankingOK || !excludedOK || !diagnosticsOK {
		return errors.New("CV2_DECISION_CLOSURE")
	}
	for _, diagnostic := range diagnostics {
		if stringValue(diagnostic) == "" {
			return errors.New("CV2_DIAGNOSTICS")
		}
	}
	if stringValue(decision["outcome"]) == "failure" && (len(includedIDs) != 0 || len(ranking) != 0) {
		return errors.New("CV2_FAILURE_NO_RANKING")
	}
	if stringValue(decision["outcome"]) == "success" && len(ranking) == 0 {
		return errors.New("CV2_SUCCESS_RANKING")
	}
	for _, exclusion := range excluded {
		if _, ok := exclusion.(map[string]any); !ok {
			return errors.New("CV2_EXCLUSION_CLOSURE")
		}
	}
	if stringValue(decision["outcome"]) != "success" && stringValue(decision["outcome"]) != "failure" {
		return errors.New("CV2_OUTCOME")
	}
	return nil
}

func decodeCanonicalJSON(raw []byte) (any, error) {
	dec := json.NewDecoder(bytes.NewReader(raw))
	dec.UseNumber()
	value, err := decodeNoDuplicate(dec)
	if err != nil {
		return nil, errors.New("CV2_STRICT_JSON")
	}
	if _, err := dec.Token(); err != io.EOF {
		return nil, errors.New("CV2_STRICT_JSON")
	}
	canonical, err := json.Marshal(value)
	if err != nil || !bytes.Equal(raw, canonical) {
		return nil, errors.New("CV2_NONCANONICAL_WIRE")
	}
	return value, nil
}
func decodeNoDuplicate(dec *json.Decoder) (any, error) {
	token, err := dec.Token()
	if err != nil {
		return nil, err
	}
	switch t := token.(type) {
	case json.Delim:
		if t == '{' {
			result := map[string]any{}
			seen := map[string]bool{}
			for dec.More() {
				key, err := dec.Token()
				if err != nil {
					return nil, err
				}
				name, ok := key.(string)
				if !ok || seen[name] {
					return nil, errors.New("duplicate")
				}
				seen[name] = true
				child, err := decodeNoDuplicate(dec)
				if err != nil {
					return nil, err
				}
				result[name] = child
			}
			_, err = dec.Token()
			return result, err
		}
		if t == '[' {
			result := []any{}
			for dec.More() {
				child, err := decodeNoDuplicate(dec)
				if err != nil {
					return nil, err
				}
				result = append(result, child)
			}
			_, err = dec.Token()
			return result, err
		}
		return nil, errors.New("delimiter")
	case json.Number:
		return t, nil
	case string, bool, nil:
		return t, nil
	default:
		return nil, errors.New("token")
	}
}
func exactKeys(value map[string]any, keys ...string) bool {
	if len(value) != len(keys) {
		return false
	}
	for _, key := range keys {
		if _, ok := value[key]; !ok {
			return false
		}
	}
	return true
}
func stringValue(value any) string { result, _ := value.(string); return result }
func positiveInteger(value json.Number) bool {
	return !strings.ContainsAny(value.String(), ".eE-") && value.String() != "0"
}
func sortedDigests(value any, nonempty bool) error {
	values, ok := value.([]any)
	if !ok || (nonempty && len(values) == 0) {
		return errors.New("CV2_ID_CLOSURE")
	}
	ids := make([]string, len(values))
	for i, item := range values {
		ids[i] = stringValue(item)
		if !v2Digest.MatchString(ids[i]) {
			return errors.New("CV2_ID_CLOSURE")
		}
	}
	if !sort.StringsAreSorted(ids) {
		return errors.New("CV2_ID_ORDER")
	}
	for i := 1; i < len(ids); i++ {
		if ids[i] == ids[i-1] {
			return errors.New("CV2_ID_ORDER")
		}
	}
	return nil
}
func withoutKey(value map[string]any, key string) map[string]any {
	result := make(map[string]any, len(value)-1)
	for k, v := range value {
		if k != key {
			result[k] = v
		}
	}
	return result
}
func hexDigest(raw []byte) string { sum := sha256.Sum256(raw); return hex.EncodeToString(sum[:]) }
