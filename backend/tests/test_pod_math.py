"""Tests for POD (Probability of Detection) calculations."""

import math

from app.models.search import calculate_pod, coverage_from_esw, cumulative_pod


def test_pod_zero_coverage():
    assert calculate_pod(0.0) == 0.0


def test_pod_high_coverage():
    pod = calculate_pod(3.0)
    assert pod > 0.95


def test_pod_one_coverage():
    pod = calculate_pod(1.0)
    expected = 1.0 - math.exp(-1.0)
    assert abs(pod - expected) < 1e-10


def test_pod_formula():
    """POD = 1 - e^(-C) where C is coverage."""
    for c in [0.0, 0.5, 1.0, 1.5, 2.0, 3.0]:
        assert abs(calculate_pod(c) - (1.0 - math.exp(-c))) < 1e-10


def test_cumulative_pod_two_passes():
    """Two 50% POD passes should give 75% cumulative."""
    result = cumulative_pod(0.5, 0.5)
    assert abs(result - 0.75) < 1e-10


def test_cumulative_pod_from_zero():
    result = cumulative_pod(0.0, 0.6)
    assert abs(result - 0.6) < 1e-10


def test_cumulative_pod_approaches_one():
    pod = 0.0
    for _ in range(10):
        pod = cumulative_pod(pod, 0.5)
    assert pod > 0.999


def test_coverage_from_esw_basic():
    # ESW=10m, walked 1000m, area 10000 sq m -> coverage = 1.0
    c = coverage_from_esw(10.0, 1000.0, 10000.0)
    assert abs(c - 1.0) < 1e-10


def test_coverage_from_esw_zero_area():
    assert coverage_from_esw(10.0, 1000.0, 0.0) == 0.0


def test_coverage_from_esw_half():
    c = coverage_from_esw(5.0, 1000.0, 10000.0)
    assert abs(c - 0.5) < 1e-10


def test_pod_realistic_scenario():
    """Typical grid search: ESW=20m, team walks 5km in 100,000 sq m area."""
    coverage = coverage_from_esw(20.0, 5000.0, 100000.0)
    pod = calculate_pod(coverage)
    assert abs(coverage - 1.0) < 1e-10
    assert abs(pod - (1.0 - math.exp(-1.0))) < 1e-10


def test_multiple_passes_increase_pod():
    """Each additional pass should increase cumulative POD."""
    area = 100000.0
    esw = 15.0
    distance = 3000.0

    pass_coverage = coverage_from_esw(esw, distance, area)
    pass_pod = calculate_pod(pass_coverage)

    cum_pod = pass_pod
    prev_pod = 0.0
    for _ in range(5):
        assert cum_pod > prev_pod
        prev_pod = cum_pod
        cum_pod = cumulative_pod(cum_pod, pass_pod)
