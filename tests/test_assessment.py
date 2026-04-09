"""Tests for end-to-end assessment."""
from ccr import CompoundFloodAssessment

def test_full_assessment():
    a = CompoundFloodAssessment(island="Jamaica", scenario="ssp245", time_horizon=2050)
    surge = a.model_storm_surge(category=3)
    rain = a.model_extreme_rainfall(return_period=100)
    slr = a.get_sea_level_rise()
    compound = a.compound_analysis(surge, rain, slr)
    risk = a.assess_risk(compound)
    assert risk.ead >= 0
    assert risk.population_exposed >= 0
    assert risk.risk_rating in ("Low", "Moderate", "High", "Extreme")

def test_different_islands():
    for island in ["Jamaica", "Barbados", "Trinidad"]:
        a = CompoundFloodAssessment(island=island)
        surge = a.model_storm_surge(category=2)
        assert surge.peak_surge_m > 0
