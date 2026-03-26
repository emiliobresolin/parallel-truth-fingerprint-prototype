# Prototype Scope Clarification

This document clarifies the approved prototype scope by explicitly distinguishing between real implementation components and simulated environment components. It does not add scope or introduce new system parts.

## Objective

Build a simple, demonstrable prototype of a parallel-truth physical-operational fingerprint architecture for an industrial setting while keeping the core research pillars executable and the surrounding environment intentionally simulated.

## Real Implementation Components

These components must exist as real executable parts of the prototype:

- decentralized edge logic and edge-local state handling
- MQTT broker plus publish/subscribe communication between edges
- consensus execution
- SCADA comparison logic
- local persistence flow
- LSTM training and inference logic
- observability, audit logs, summaries, and alerts

## Simulated Environment Components

These components are intentionally represented through controlled simulation or local stand-ins:

- physical sensors
- compressor/process behavior
- physical edge hardware devices
- SCADA environment, exposed through a fake OPC UA service
- cloud environment, represented locally rather than through a real cloud platform
- broader industrial/plant environment outside the explicit prototype runtime

## Scope Rule

The prototype must use real executable code for the core research pillars while using simulation only for the surrounding environment that would otherwise require field hardware or enterprise infrastructure.

This means:

- the prototype does not need real field sensors
- the prototype does not need a real SCADA platform
- the prototype does not need a real cloud deployment
- the prototype must still execute real messaging, consensus, comparison, persistence, and LSTM paths

## Success Interpretation

The prototype is in scope when it demonstrates:

1. simulated physical behavior feeding the edge layer
2. real inter-edge communication through MQTT
3. real consensus execution producing or refusing valid state
4. real comparison logic operating on consensused state versus simulated SCADA state
5. real persistence of valid data
6. real LSTM training and inference downstream of valid data

This clarification strengthens the academic validity of the prototype without increasing implementation complexity.
