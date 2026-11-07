package app

import "testing"

func fourSensorRound() RoundInputTx {
	ids := []string{"edge-1", "edge-2", "edge-3", "edge-4"}
	states := []ReplicatedState{}
	for _, id := range ids {
		states = append(states, ReplicatedState{OwnerEdgeID: id, SensorValues: map[string]SensorValue{
			"temperature": {Value: 12, Unit: "mA", SourceEventID: "temp-event"}, "pressure": {Value: 8, Unit: "mA", SourceEventID: "pressure-event"},
			"rpm": {Value: 16, Unit: "mA", SourceEventID: "rpm-event"}, "mass_flow": {Value: 12.123456, Unit: "mA", SourceEventID: "flow-event"},
		}})
	}
	return RoundInputTx{SchemaVersion: currentSchemaVersion, MeasurementDomain: currentMeasurementDomain, RoundID: "four-sensors", ParticipatingEdges: ids, ReplicatedStates: states}
}

func TestMassFlowParticipatesInConsolidation(t *testing.T) {
	round, err := evaluateRound(fourSensorRound(), 1)
	if err != nil || round.ConsensusedValidState == nil {
		t.Fatalf("four-sensor evaluation failed: %v", err)
	}
	if len(round.ConsensusedValidState.SourceEdges) != 4 || round.ConsensusedValidState.SensorValues["mass_flow"] != 12.123456 {
		t.Fatal("mass flow or fourth edge was dropped")
	}
}

func TestMassFlowDisagreementExcludesFourthView(t *testing.T) {
	tx := fourSensorRound()
	tx.ReplicatedStates[3].SensorValues["mass_flow"] = SensorValue{Value: 19, Unit: "mA", SourceEventID: "flow-event"}
	round, err := evaluateRound(tx, 1)
	if err != nil || round.ConsensusedValidState == nil {
		t.Fatalf("expected three agreeing views: %v", err)
	}
	if len(round.Exclusions) != 1 || round.Exclusions[0].EdgeID != "edge-4" || len(round.ConsensusedValidState.SourceEdges) != 3 {
		t.Fatal("fourth mass-flow disagreement not handled by three-of-four selection")
	}
}

func TestMissingMassFlowInOneViewFailsClosed(t *testing.T) {
	tx := fourSensorRound()
	delete(tx.ReplicatedStates[3].SensorValues, "mass_flow")
	if _, err := evaluateRound(tx, 1); err == nil {
		t.Fatal("incompatible sensor schemas accepted")
	}
}
