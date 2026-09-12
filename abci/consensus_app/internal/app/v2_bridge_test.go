package app

import (
	"context"
	"crypto/sha256"
	"encoding/hex"
	"encoding/json"
	"errors"
	"testing"
)

type v2TestEvaluator struct {
	decision []byte
	err      error
	called   bool
}

func (e *v2TestEvaluator) EvaluateConsensusV2(_ context.Context, _ ConsensusV2Envelope) ([]byte, error) {
	e.called = true
	return e.decision, e.err
}

func TestConsensusV2ShadowBridgeAcceptsOnlyCanonicalClosedEnvelope(t *testing.T) {
	round := v2TestRound()
	envelope := map[string]any{"schema_version": consensusV2EnvelopeSchema, "route": consensusV2ShadowRoute, "round_input": round, "parameter_set_id": v2ID("parameters"), "operation_registry_id": v2ID("registry"), "authorization_effect": "none"}
	raw := v2JSON(envelope)
	decoded, err := DecodeConsensusV2Envelope(raw)
	if err != nil {
		t.Fatalf("DecodeConsensusV2Envelope() error = %v", err)
	}
	if decoded.Route != consensusV2ShadowRoute || string(decoded.RoundInput) != string(v2JSON(round)) {
		t.Fatal("closed v2 envelope was not preserved")
	}
}

func TestConsensusV2ShadowBridgeRejectsLegacyUnknownAndNonCanonicalTraffic(t *testing.T) {
	valid := v2TestEnvelope()
	cases := [][]byte{
		[]byte(`{"round_id":"legacy","participating_edges":["edge"]}`),
		append(valid[:len(valid)-1], []byte(`,"unknown":"value"}`)...),
		append([]byte(" "), valid...),
	}
	for _, raw := range cases {
		if _, err := DecodeConsensusV2Envelope(raw); err == nil {
			t.Fatalf("DecodeConsensusV2Envelope(%s) unexpectedly succeeded", raw)
		}
	}
}

func TestConsensusV2ShadowBridgeNeverPersistsAndReturnsExplicitFailure(t *testing.T) {
	evaluator := &v2TestEvaluator{err: errors.New("unavailable")}
	adapter, err := NewConsensusV2ShadowAdapter(evaluator)
	if err != nil {
		t.Fatal(err)
	}
	response := adapter.Execute(context.Background(), v2TestEnvelope())
	if response.Code != 1 || response.Log != "CV2_EVALUATION_FAILED" || !response.ShadowOnly || len(response.DecisionBytes) != 0 || !evaluator.called {
		t.Fatalf("unexpected shadow failure: %#v", response)
	}
}

func TestConsensusV2ShadowBridgeEmitsOnlyCanonicalNoRankingFailure(t *testing.T) {
	round := v2TestRound()
	rawRound := v2JSON(round)
	decision := map[string]any{
		"schema_version": consensusV2Schema, "round_input_id": round["input_content_id"], "round_input_hash": "sha256:" + v2DigestText(rawRound), "comparison_basis": round["comparison_basis"], "outcome": "failure",
		"participant_ids": []any{v2ID("edge-a")}, "included_ids": []any{}, "excluded": []any{}, "ranking": []any{}, "diagnostics": []any{"CV2_NO_RANKING"}, "decision_content_id": v2ID("decision"), "authorization_effect": "none",
	}
	evaluator := &v2TestEvaluator{decision: v2JSON(decision)}
	adapter, _ := NewConsensusV2ShadowAdapter(evaluator)
	response := adapter.Execute(context.Background(), v2TestEnvelope())
	if response.Code != 0 || response.Log != "CV2_SHADOW_DECISION" || !response.ShadowOnly || string(response.DecisionBytes) != string(v2JSON(decision)) {
		t.Fatalf("unexpected shadow response: %#v", response)
	}
}

func v2TestEnvelope() []byte {
	return v2JSON(map[string]any{"schema_version": consensusV2EnvelopeSchema, "route": consensusV2ShadowRoute, "round_input": v2TestRound(), "parameter_set_id": v2ID("parameters"), "operation_registry_id": v2ID("registry"), "authorization_effect": "none"})
}
func v2TestRound() map[string]any {
	basisBytes := `{"basis":"fixed"}`
	basis := map[string]any{"basis_id": v2ID("basis"), "schema_version": "ComparisonBasis.v2", "canonical_bytes": basisBytes, "canonical_bytes_hash": "sha256:" + v2DigestText([]byte(basisBytes)), "kind": "same_profile_raw_current", "unit": "mA", "profile_ids": []any{v2ID("profile")}, "uncertainty_parameter_ids": []any{}}
	round := map[string]any{"schema_version": consensusV2Schema, "experiment_id": v2ID("experiment"), "run_id": v2ID("run"), "round_id": v2ID("round"), "qualification_result_id": v2ID("qualification"), "comparison_basis": basis, "quality_policy_ids": []any{v2ID("quality")}, "parameter_ids": []any{}, "observations": []any{map[string]any{"edge_id": v2ID("edge-a"), "observation_id": v2ID("observation"), "observation_canonical_hash": v2ID("observation-hash"), "profile_id": v2ID("profile"), "source_sequence": json.Number("1"), "correlation_id": v2ID("correlation"), "raw_current_unit": "mA"}}, "authorization_effect": "none"}
	round["input_content_id"] = "sha256:" + v2DigestText(v2JSON(round))
	return round
}
func v2ID(value string) string { return "sha256:" + v2DigestText([]byte(value)) }
func v2DigestText(value []byte) string {
	sum := sha256.Sum256(value)
	return hex.EncodeToString(sum[:])
}
func v2JSON(value any) []byte {
	raw, err := json.Marshal(value)
	if err != nil {
		panic(err)
	}
	return raw
}
