"""Example: Compound flood risk assessment for Jamaica under SSP2-4.5 (2050)."""
from ccr import CompoundFloodAssessment

assessment = CompoundFloodAssessment(island="Jamaica", scenario="ssp245", time_horizon=2050)

surge = assessment.model_storm_surge(category=3)
print(f"Storm Surge (Cat 3): {surge.peak_surge_m:.2f} m")

rainfall = assessment.model_extreme_rainfall(return_period=100, duration_hours=24)
print(f"100-yr 24h Rainfall: {rainfall.depth_mm:.1f} mm")

slr = assessment.get_sea_level_rise()
print(f"Sea Level Rise (SSP2-4.5, 2050): {slr.rise_m:.3f} m")

compound = assessment.compound_analysis(surge, rainfall, slr, copula="gumbel")
print(f"Compound Flood Depth: {compound.total_flood_depth_m:.2f} m")

risk = assessment.assess_risk(compound)
print(f"Expected Annual Damage: ${risk.ead:,.0f}")
print(f"Population Exposed: {risk.population_exposed:,}")
print(f"Risk Rating: {risk.risk_rating}")
