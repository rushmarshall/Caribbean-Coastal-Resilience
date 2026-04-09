"""End-to-end compound flood risk assessment for Caribbean SIDS."""
from __future__ import annotations
import logging
from dataclasses import dataclass, field
from typing import Any

import numpy as np

from ccr.islands import get_island, IslandConfig
from ccr.hazards.surge import HollandSurgeModel, StormSurgeResult
from ccr.hazards.rainfall import ExtremeRainfallModel, ExtremeRainfallResult
from ccr.hazards.sea_level import SeaLevelRiseModel, SeaLevelRiseResult
from ccr.risk.compound import CompoundFloodModel, CompoundFloodResult
from ccr.vulnerability.damage_curves import estimate_damage

logger = logging.getLogger(__name__)

WARMING_BY_SCENARIO = {
    "ssp126": {2030: 0.5, 2050: 0.8, 2100: 1.0},
    "ssp245": {2030: 0.6, 2050: 1.2, 2100: 2.0},
    "ssp370": {2030: 0.7, 2050: 1.4, 2100: 3.0},
    "ssp585": {2030: 0.8, 2050: 1.6, 2100: 4.0},
}

@dataclass
class RiskResult:
    """Complete compound flood risk assessment output."""
    island: str
    scenario: str
    time_horizon: int
    compound_flood: CompoundFloodResult
    ead: float  # Expected Annual Damage (USD)
    population_exposed: int
    damage_ratio: float
    risk_rating: str
    components: dict[str, Any] = field(default_factory=dict)

    def export_report(self, filepath: str) -> None:
        """Export a summary report."""
        report = [
            f"Compound Flood Risk Assessment: {self.island}",
            f"Scenario: {self.scenario} | Horizon: {self.time_horizon}",
            f"---",
            f"Total Flood Depth: {self.compound_flood.total_flood_depth_m:.2f} m",
            f"  Surge: {self.compound_flood.surge_component_m:.2f} m",
            f"  Pluvial: {self.compound_flood.rainfall_component_m:.2f} m",
            f"  SLR: {self.compound_flood.slr_component_m:.2f} m",
            f"Joint Probability: {self.compound_flood.joint_probability:.6f}",
            f"Expected Annual Damage: ${self.ead:,.0f}",
            f"Population Exposed: {self.population_exposed:,}",
            f"Damage Ratio: {self.damage_ratio:.1%}",
            f"Risk Rating: {self.risk_rating}",
        ]
        with open(filepath, "w") as f:
            f.write("\n".join(report))
        logger.info("Report exported: %s", filepath)


class CompoundFloodAssessment:
    """End-to-end compound flood risk assessment for Caribbean islands.

    Integrates storm surge, extreme rainfall, sea level rise,
    and social vulnerability into a unified risk metric.
    """

    def __init__(
        self,
        island: str,
        scenario: str = "ssp245",
        time_horizon: int = 2050,
    ) -> None:
        self.island_config = get_island(island)
        self.scenario = scenario
        self.time_horizon = time_horizon

        warming_table = WARMING_BY_SCENARIO.get(scenario, WARMING_BY_SCENARIO["ssp245"])
        years = sorted(warming_table.keys())
        values = [warming_table[y] for y in years]
        self.warming = float(np.interp(time_horizon, years, values))

        self.surge_model = HollandSurgeModel()
        self.rainfall_model = ExtremeRainfallModel(island=island)
        self.slr_model = SeaLevelRiseModel()
        self.compound_model = CompoundFloodModel()

    def model_storm_surge(self, category: int = 3, **kwargs: Any) -> StormSurgeResult:
        """Model storm surge for a hurricane of given category."""
        return self.surge_model.estimate_surge(category=category, **kwargs)

    def model_extreme_rainfall(self, return_period: int = 100, duration_hours: int = 24) -> ExtremeRainfallResult:
        """Model extreme rainfall with climate scaling."""
        return self.rainfall_model.estimate(
            return_period=return_period,
            duration_hours=duration_hours,
            warming_degrees=self.warming,
        )

    def get_sea_level_rise(self) -> SeaLevelRiseResult:
        """Get sea level rise projection for configured scenario and horizon."""
        return self.slr_model.project(scenario=self.scenario, year=self.time_horizon)

    def compound_analysis(
        self,
        surge: StormSurgeResult,
        rainfall: ExtremeRainfallResult,
        sea_level_rise: SeaLevelRiseResult,
        copula: str = "gumbel",
    ) -> CompoundFloodResult:
        """Perform compound flood analysis combining all hazards."""
        self.compound_model = CompoundFloodModel(copula=copula)
        return self.compound_model.analyze(
            surge_m=surge.peak_surge_m,
            rainfall_depth_mm=rainfall.depth_mm,
            sea_level_rise_m=sea_level_rise.rise_m,
            return_period=rainfall.return_period_years,
        )

    def assess_risk(
        self,
        compound_flood: CompoundFloodResult,
        include_vulnerability: bool = True,
        damage_function: str = "caribbean_residential",
    ) -> RiskResult:
        """Full risk assessment with damage and exposure estimation."""
        # Estimate population exposed (simplified: fraction of coastal pop below flood depth)
        flood_depth = compound_flood.total_flood_depth_m
        elevation_m = self.island_config.mean_elevation_m
        exposed_fraction = min(flood_depth / (elevation_m * 0.1), 0.5)
        pop_exposed = int(self.island_config.coastal_population * exposed_fraction)

        # Damage estimation
        n_buildings = int(pop_exposed / 3.5)  # avg household size
        damage = estimate_damage(flood_depth, damage_function, n_buildings)

        # EAD = damage * annual probability
        ead = damage.estimated_cost_usd * compound_flood.joint_probability

        # Risk rating
        if ead > 10_000_000:
            rating = "Extreme"
        elif ead > 1_000_000:
            rating = "High"
        elif ead > 100_000:
            rating = "Moderate"
        else:
            rating = "Low"

        return RiskResult(
            island=self.island_config.name,
            scenario=self.scenario,
            time_horizon=self.time_horizon,
            compound_flood=compound_flood,
            ead=ead,
            population_exposed=pop_exposed,
            damage_ratio=damage.damage_ratio,
            risk_rating=rating,
            components={
                "surge": compound_flood.surge_component_m,
                "rainfall": compound_flood.rainfall_component_m,
                "slr": compound_flood.slr_component_m,
                "warming": self.warming,
            },
        )
