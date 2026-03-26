package app

import (
	"crypto/sha256"
	"encoding/json"
	"os"
)

func loadState(path string) (PersistedState, error) {
	if _, err := os.Stat(path); os.IsNotExist(err) {
		return PersistedState{Rounds: map[string]CommittedRound{}}, nil
	}

	raw, err := os.ReadFile(path)
	if err != nil {
		return PersistedState{}, err
	}
	var state PersistedState
	if err := json.Unmarshal(raw, &state); err != nil {
		return PersistedState{}, err
	}
	if state.Rounds == nil {
		state.Rounds = map[string]CommittedRound{}
	}
	return state, nil
}

func persistState(path string, state PersistedState) ([]byte, error) {
	hash, err := computeAppHash(state)
	if err != nil {
		return nil, err
	}
	state.LastAppHash = hash
	raw, err := json.MarshalIndent(state, "", "  ")
	if err != nil {
		return nil, err
	}
	if err := os.WriteFile(path, raw, 0o644); err != nil {
		return nil, err
	}
	return hash, nil
}

func computeAppHash(state PersistedState) ([]byte, error) {
	canonicalState := PersistedState{
		LastBlockHeight: state.LastBlockHeight,
		Rounds:          state.Rounds,
	}
	raw, err := json.Marshal(canonicalState)
	if err != nil {
		return nil, err
	}
	hash := sha256.Sum256(raw)
	return hash[:], nil
}
