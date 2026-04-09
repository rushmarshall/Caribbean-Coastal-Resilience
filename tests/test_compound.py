"""Tests for compound flood analysis."""
from ccr.risk.compound import CompoundFloodModel

def test_compound_analysis():
    model = CompoundFloodModel(copula="gumbel")
    result = model.analyze(surge_m=2.0, rainfall_depth_mm=300, sea_level_rise_m=0.2)
    assert result.total_flood_depth_m > 2.0
    assert result.joint_probability > 0

def test_independence_copula():
    model = CompoundFloodModel(copula="independence")
    result = model.analyze(surge_m=1.0, rainfall_depth_mm=100, sea_level_rise_m=0.1)
    assert result.copula_type == "independence"

def test_slr_contribution():
    model = CompoundFloodModel()
    r1 = model.analyze(surge_m=1.0, rainfall_depth_mm=100, sea_level_rise_m=0.0)
    r2 = model.analyze(surge_m=1.0, rainfall_depth_mm=100, sea_level_rise_m=0.5)
    assert r2.total_flood_depth_m > r1.total_flood_depth_m
