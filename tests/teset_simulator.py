import statistics

import pytest

from seshat.contract import DetectorEvent
from seshat.sources.simulator import (
    Detector,
    Source,
    apply_dead_time,
    simulate,
    true_rate_cps,
)


def counts_of(events):
    return [e.counts for e in events]


def test_event_count_and_type():
    dets = [Detector("a", 0, 0), Detector("b", 5, 0)]
    events = list(simulate(dets, [], n_intervals=10))
    assert len(events) == 20
    assert all(isinstance(e, DetectorEvent) for e in events)


def test_same_seed_same_output():
    dets = [Detector("a", 0, 0)]
    first = counts_of(simulate(dets, [], n_intervals=50, seed=1))
    second = counts_of(simulate(dets, [], n_intervals=50, seed=1))
    assert first == second


def test_background_is_poisson():
    # Poisson: mean and variance are equal. 2 cps * 10 s = 20 counts expected.
    det = Detector("a", 0, 0, background_cps=2.0)
    data = counts_of(simulate([det], [], n_intervals=2000, interval_s=10.0))
    assert statistics.mean(data) == pytest.approx(20, abs=0.5)
    assert statistics.variance(data) == pytest.approx(20, abs=4)


def test_rate_follows_inverse_square():
    det = Detector("a", 0, 0, background_cps=0.0)
    at_1m = true_rate_cps(det, [Source(x0=1, y0=0, strength_cps=20)], t=0)
    at_2m = true_rate_cps(det, [Source(x0=2, y0=0, strength_cps=20)], t=0)
    assert at_1m / at_2m == pytest.approx(4.0)


def test_source_raises_counts():
    det = Detector("a", 0, 0)
    src = Source(x0=1, y0=0, strength_cps=20)
    with_src = statistics.mean(counts_of(simulate([det], [src], n_intervals=100)))
    without = statistics.mean(counts_of(simulate([det], [], n_intervals=100)))
    assert with_src > 10 * without


def test_decay_halves_rate_after_one_half_life():
    det = Detector("a", 0, 0, background_cps=0.0)
    src = Source(x0=1, y0=0, strength_cps=20, half_life_s=100)
    assert true_rate_cps(det, [src], t=100) == pytest.approx(
        true_rate_cps(det, [src], t=0) / 2
    )


def test_dead_time_lowers_measured_rate():
    assert apply_dead_time(100, 0.0) == pytest.approx(100)
    assert apply_dead_time(100, 0.01) == pytest.approx(50)


def test_dead_detector_reads_zero():
    det = Detector("a", 0, 0, fault="dead")
    assert set(counts_of(simulate([det], [], n_intervals=20))) == {0}


def test_stuck_detector_repeats_value():
    det = Detector("a", 0, 0, fault="stuck", stuck_value=7)
    assert set(counts_of(simulate([det], [], n_intervals=20))) == {7}


def test_fault_starts_at_given_time():
    det = Detector("a", 0, 0, fault="dead", fault_start_s=100)
    data = counts_of(simulate([det], [], n_intervals=20, interval_s=10.0))
    assert any(c > 0 for c in data[:10])   # works normally before t = 100 s
    assert all(c == 0 for c in data[10:])  # dead afterwards