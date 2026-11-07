package app

import (
	"context"
	"encoding/json"
	abcitypes "github.com/cometbft/cometbft/abci/types"
	"math"
	"path/filepath"
	"strings"
	"testing"
)

func TestWireRequiresNumericCurrentPresence(t *testing.T) {
	for _, raw := range []string{
		`{"unit":"mA","source_event_id":"event"}`,
		`{"value":null,"unit":"mA","source_event_id":"event"}`,
		`{"value":"12","unit":"mA","source_event_id":"event"}`,
		`{"value":true,"unit":"mA","source_event_id":"event"}`,
	} {
		var value SensorValue
		if err := json.Unmarshal([]byte(raw), &value); err == nil {
			t.Fatalf("invalid current accepted: %s", raw)
		}
	}
	var zero SensorValue
	if err := json.Unmarshal([]byte(`{"value":0,"unit":"mA","source_event_id":"event"}`), &zero); err != nil || zero.Value != 0 {
		t.Fatalf("explicit zero rejected: %v", err)
	}
	app, err := NewConsensusApplication(filepath.Join(t.TempDir(), "state.json"))
	if err != nil {
		t.Fatal(err)
	}
	raw, _ := json.Marshal(fourSensorRound())
	for _, replacement := range []string{`"value":null`, `"absent_value":12`} {
		malformed := []byte(strings.Replace(string(raw), `"value":12`, replacement, 1))
		checked, _ := app.CheckTx(context.Background(), &abcitypes.CheckTxRequest{Tx: malformed})
		if checked.Code == 0 {
			t.Fatal("CheckTx accepted absent/null current")
		}
		finalized, err := app.FinalizeBlock(context.Background(), &abcitypes.FinalizeBlockRequest{Height: 1, Txs: [][]byte{malformed}})
		if err != nil || finalized.TxResults[0].Code == 0 {
			t.Fatalf("FinalizeBlock accepted absent/null current: %v", err)
		}
	}
}

func TestFiniteCurrentDiagnosticOverflowFailsClosed(t *testing.T) {
	for _, currents := range [][4]float64{
		{1e308, -1e308, 1e308, 1e308},
		{0, 1e308, 1e308, 1e308},
	} {
		tx := fourSensorRound()
		for i, current := range currents {
			for name, value := range tx.ReplicatedStates[i].SensorValues {
				value.Value = current
				tx.ReplicatedStates[i].SensorValues[name] = value
			}
		}
		if _, err := evaluateRound(tx, 1); err == nil {
			t.Fatal("overflowing current diagnostics accepted")
		}
	}
}

func TestLargeFiniteAgreedCurrentRetainsPrecision(t *testing.T) {
	tx := fourSensorRound()
	for i := range tx.ReplicatedStates {
		for name, value := range tx.ReplicatedStates[i].SensorValues {
			value.Value = 1e308
			tx.ReplicatedStates[i].SensorValues[name] = value
		}
	}
	result, err := evaluateRound(tx, 1)
	if err != nil || result.FinalStatus != statusSuccess || result.ConsensusedValidState.SensorValues["rpm"] != 1e308 {
		t.Fatalf("large finite agreed current rejected: %v", err)
	}
	if rounded := round(1e308); rounded != 1e308 {
		t.Fatalf("round overflowed: %v", rounded)
	}
}

func TestCurrentDomainValidation(t *testing.T) {
	for _, change := range []func(*RoundInputTx){
		func(tx *RoundInputTx) { tx.MeasurementDomain = "" },
		func(tx *RoundInputTx) { tx.SchemaVersion = "" },
		func(tx *RoundInputTx) {
			v := tx.ReplicatedStates[0].SensorValues["rpm"]
			v.Unit = "rpm"
			tx.ReplicatedStates[0].SensorValues["rpm"] = v
		},
		func(tx *RoundInputTx) {
			v := tx.ReplicatedStates[0].SensorValues["rpm"]
			v.SourceEventID = ""
			tx.ReplicatedStates[0].SensorValues["rpm"] = v
		},
		func(tx *RoundInputTx) {
			v := tx.ReplicatedStates[0].SensorValues["rpm"]
			v.Value = math.Inf(1)
			tx.ReplicatedStates[0].SensorValues["rpm"] = v
		},
		func(tx *RoundInputTx) { tx.ParticipatingEdges[1] = tx.ParticipatingEdges[0] },
	} {
		tx := fourSensorRound()
		change(&tx)
		if _, err := evaluateRound(tx, 1); err == nil {
			t.Fatal("invalid current transaction accepted")
		}
	}
}

func TestSplitTwoAgainstTwoFails(t *testing.T) {
	tx := fourSensorRound()
	for i := 2; i < 4; i++ {
		v := tx.ReplicatedStates[i].SensorValues["rpm"]
		v.Value += 0.000001
		tx.ReplicatedStates[i].SensorValues["rpm"] = v
	}
	result, err := evaluateRound(tx, 1)
	if err != nil || result.FinalStatus != statusFailedConsensus || result.ConsensusedValidState != nil {
		t.Fatalf("split accepted: %+v %v", result, err)
	}
}

func TestSourceIdentityControlsCompatibility(t *testing.T) {
	tx := fourSensorRound()
	v := tx.ReplicatedStates[3].SensorValues["rpm"]
	v.SourceEventID = "different-event"
	tx.ReplicatedStates[3].SensorValues["rpm"] = v
	result, err := evaluateRound(tx, 1)
	if err != nil || result.FinalStatus != statusSuccess || len(result.Exclusions) != 1 || result.Exclusions[0].Reason != reasonInconsistentView {
		t.Fatalf("identity disagreement accepted: %+v %v", result, err)
	}
	if result.TrustEvidence[3].OverallNormalizedDeviation != 0 {
		t.Fatal("identity mismatch must not fabricate an analog distance")
	}
	if result.MeasurementDomain != currentMeasurementDomain || result.SchemaVersion != currentSchemaVersion || result.ConsensusedValidState.MeasurementDomain != currentMeasurementDomain {
		t.Fatal("missing current domain")
	}
}

func TestCurrentDistanceUsesSixteenMASpan(t *testing.T) {
	tx := fourSensorRound()
	v := tx.ReplicatedStates[3].SensorValues["rpm"]
	v.Value += 16
	tx.ReplicatedStates[3].SensorValues["rpm"] = v
	d, err := normalizedPairDistance(tx.ReplicatedStates[0], tx.ReplicatedStates[3])
	if err != nil || d != 0.25 {
		t.Fatalf("distance=%v err=%v", d, err)
	}
}

func TestLegacyStateCannotMixWithCurrentSession(t *testing.T) {
	path := filepath.Join(t.TempDir(), "state.json")
	_, err := persistState(path, PersistedState{Rounds: map[string]CommittedRound{"old": {RoundID: "old"}}})
	if err != nil {
		t.Fatal(err)
	}
	app, err := NewConsensusApplication(path)
	if err != nil {
		t.Fatal(err)
	}
	raw, _ := json.Marshal(fourSensorRound())
	checked, _ := app.CheckTx(context.Background(), &abcitypes.CheckTxRequest{Tx: raw})
	if checked.Code == 0 {
		t.Fatal("legacy state accepted new tx")
	}
	result, err := app.FinalizeBlock(context.Background(), &abcitypes.FinalizeBlockRequest{Height: 2, Txs: [][]byte{raw}})
	if err != nil || result.TxResults[0].Code == 0 {
		t.Fatal("legacy finalize accepted new tx")
	}
	if _, ok := app.state.Rounds["old"]; !ok {
		t.Fatal("legacy state lost")
	}
}
