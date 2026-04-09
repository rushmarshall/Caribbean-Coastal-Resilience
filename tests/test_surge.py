"""Tests for storm surge modeling."""
import pytest
from ccr.hazards.surge import HollandSurgeModel

def test_surge_increases_with_category():
    model = HollandSurgeModel()
    s1 = model.estimate_surge(category=1)
    s3 = model.estimate_surge(category=3)
    s5 = model.estimate_surge(category=5)
    assert s1.peak_surge_m < s3.peak_surge_m < s5.peak_surge_m

def test_invalid_category():
    model = HollandSurgeModel()
    with pytest.raises(ValueError):
        model.estimate_surge(category=6)

def test_surge_profile_shape():
    model = HollandSurgeModel()
    result = model.estimate_surge(category=3)
    assert len(result.surge_profile) == len(result.distances_km)
    assert result.peak_surge_m > 0
