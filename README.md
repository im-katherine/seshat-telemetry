# Seshat

> Named after Seshat, the Egyptian goddess of writing and record-keeping.

A telemetry platform for radiation-detector networks. Seshat ingests detector events,
stores them, and flags anomalies using **counting statistics** instead of arbitrary
thresholds.

![status](https://img.shields.io/badge/status-in%20development-yellow)
![python](https://img.shields.io/badge/python-3.11%2B-blue)
![license](https://img.shields.io/badge/license-MIT-green)

> **Disclaimer:** educational and portfolio project. All data is simulated, all models
> are generic, and it is not intended for safety-critical use.

## Motivation

I did an undergraduate research project (IC) on neutron diffraction, where I used
McStas to simulate instruments and work with detector data. That left me interested in
how radiation measurements are produced and what it takes to trust them.

Seshat combines that background with the software skills I was building at the same
time: data pipelines, APIs, statistical analysis and containerized deployment. It treats

radiation monitoring as a telemetry problem where the physics decides how the software should behave.

It is simulation-first, so the whole pipeline can be developed and tested without hardware.

## How it works

```
Simulator ──► Ingestion ──► SQLite ◄── Analysis
                              ▲
                              │
                           FastAPI ──► Dashboard
```

Every source emits the same event format, so the simulator can later be replaced by real
data (for example McStas output or an acquisition node) without touching the rest.

```json
{"type": "detector", "device_id": "det-01", "ts": 1729100000, "kind": "gamma", "counts": 47, "interval_s": 10}
```

Invalid events are rejected at the boundary and logged.

## The physics behind the analysis

| Phenomenon | Handling |
|---|---|
| Poisson counting | Variance equals the mean, so alarms are expressed in σ above background |
| Source passage | Rate follows ~1/r², so peak timing across detectors shows direction of movement |
| Decay | Sources are modeled with a half-life, so decay is not mistaken for a fault |
| Dead time | The simulator loses counts at high rates; the analysis can correct for it |
| Faulty detectors | Variance far below Poisson means stuck, zero counts means dead, slow shifts mean drift |

The false-alarm rate is treated as a design parameter: with many detectors and many
intervals per day, a fixed σ threshold implies a predictable number of false alarms.

## Tech stack

Python · FastAPI · Pydantic · SQLite · pandas · Streamlit · pytest · Docker

## Getting started

Requires Python 3.11 or newer.

```bash
git clone https://github.com/im-katherine/seshat.git
cd seshat
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pytest
```

## Roadmap

**Phase 1: detector network**
- [x] Project setup and test harness
- [ ] Event contract with validation
- [ ] Detector simulator (background, source passage, dead time, faults)
- [ ] Storage and ingestion
- [ ] REST API
- [ ] Statistical anomaly detection
- [ ] Dashboard and Docker Compose

**Phase 2: simulated research reactor**
- [ ] Point-kinetics model with delayed-neutron groups
- [ ] Detector response tied to reactor power, with cross-channel consistency checks

**Phase 3: integrations (optional)**
- [ ] McStas monitor output as a data source
- [ ] Low-cost acquisition node (microcontroller counting Geiger-tube pulses)

## License

MIT