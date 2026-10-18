"""Physics-based radiation detector simulator."""

import math
from collections.abc import Iterator
from dataclasses import dataclass

import numpy as np

from seshat.contract import DetectorEvent

MIN_DISTANCE_M = 0.5 #avoids 1/r^2 blowing up when source is on the top of detector

@dataclass(frozen=True)
class Detector:
    """A radiation detector at a fixed location."""
    device_id: str
    x0: float                        #position in meters
    y0: float
    kind: str = "gamma"              #detector type, either "gamma" or "neutron"
    background_cps: float = 0.5      #average background , counts per second
    dead_time_s: float = 0.0         # detector dead time in seconds, during which it cannot record counts
    fault: str | None = None         #when the fault begins
    fault_start_s: float = 0.0      #time when the fault starts
    stuck_value: int = 5            #value repeated by a stuck detector

@dataclass(frozen=True)
class Source:
    x0: float                        #position in meters
    y0: float
    vx: float = 0.0                   #velocity in meters per second
    vy: float = 0.0
    strength_cps: float = 20.0             #rate meadured at 1m from the source
    half_life_s: float | None = None  #half-life in seconds, if decaying

    def position_at(self, t: float) -> tuple[float, float]:
        """Return the position of the source at time t."""
        return self.x0 + self.vx * t, self.y0 + self.vy * t

    def activity_at(self, t: float) -> float:
        """Return the activity of the source at time t."""
        if self.half_life_s is None:
            return 1.0
        else:
            return 0.5 ** (t / self.half_life_s)

def true_rate_cps(det: Detector, sources: list[Source], t: float) -> float:
    """Return the true rate measured by the detector at time t."""
    rate = det.background_cps
    for src in sources:
        x, y = src.position_at(t)
        r = max(math.hypot(x - det.x0, y - det.y0), MIN_DISTANCE_M)
        rate += src.strength_cps * src.activity_at(t) / (r ** 2)
    return rate

def apply_dead_time(rate_cps: float, dead_time_s: float) -> float:
    """Return the measured rate after applying dead time."""
    return rate_cps / (1 + rate_cps * dead_time_s)

def _draw_counts(det, sources, t, interval_s, rng) -> int:
    """Draw a random number of counts for the detector in the given interval."""
    if det.fault is not None and t >= det.fault_start_s:
        return 0 if det.fault == "dead" else det.stuck_value
    rate = apply_dead_time(true_rate_cps(det, sources, t), det.dead_time_s)
    return int(rng.poisson(rate * interval_s))

def simulate(
        detectors: list[Detector],
        sources: list[Source],
        n_intervals: int,
        interval_s: float = 10.0,
        start_ts: int = 1_700_000_000,
        seed: int = 42,
) -> Iterator[DetectorEvent]:
    """Simulate a series of detector events."""
    rng = np.random.default_rng(seed)
    for i in range(n_intervals):
        t = i * interval_s
        for det in detectors:
            count = _draw_counts(det, sources, t, interval_s, rng)
            yield DetectorEvent(
                type="detector",
                device_id=det.device_id,
                ts=start_ts + int(t),
                kind=det.kind,
                counts=count,
                interval_s=interval_s
            )

def demo_scenario() -> tuple[list[Detector], list[Source]]:
    detectors = [
        Detector("det-01", 0, 0),
        Detector("det-02", 10, 0),
        Detector("det-03", 20, 0, dead_time_s=0.02),                    # loses counts at high rate
        Detector("det-04", 30, 0, fault="stuck", fault_start_s=300),    # freezes before the source arrives
    ]
    sources = [Source(x0=-5, y0=1, vx=0.1, strength_cps=20)]           # walks along the detectors
    return detectors, sources


if __name__ == "__main__":
    dets, srcs = demo_scenario()
    for event in simulate(dets, srcs, n_intervals=60):
        print(event.model_dump_json())