"""IPCC AR6 sea level rise projections.

Provides global and regionally adjusted sea level rise
estimates for Caribbean islands under SSP scenarios.
"""
from __future__ import annotations
import logging
import numpy as np
from dataclasses import dataclass

logger = logging.getLogger(__name__)

# IPCC AR6 global mean SLR (meters, median) by year and scenario
IPCC_AR6_SLR = {
    "ssp126": {2030: 0.08, 2050: 0.15, 2100: 0.32, 2150: 0.47},
    "ssp245": {2030: 0.09, 2050: 0.19, 2100: 0.56, 2150: 0.85},
    "ssp370": {2030: 0.09, 2050: 0.21, 2100: 0.68, 2150: 1.10},
    "ssp585": {2030: 0.10, 2050: 0.23, 2100: 0.77, 2150: 1.32},
}

# Regional adjustment factors for Caribbean (relative to global mean)
CARIBBEAN_SLR_FACTOR = 1.10  # Caribbean typically 10% above global mean

@dataclass
class SeaLevelRiseResult:
    """Sea level rise projection output."""
    rise_m: float
    scenario: str
    year: int
    global_mean_m: float
    regional_factor: float
    uncertainty_range_m: tuple[float, float]

class SeaLevelRiseModel:
    """IPCC AR6 sea level rise projections for Caribbean.

    Provides median and uncertainty range SLR estimates
    with regional adjustment for Caribbean basin.
    """

    def __init__(self, regional_factor: float = CARIBBEAN_SLR_FACTOR) -> None:
        self.regional_factor = regional_factor

    def project(
        self,
        scenario: str = "ssp245",
        year: int = 2050,
    ) -> SeaLevelRiseResult:
        """Get SLR projection for a given scenario and target year.

        Parameters
        ----------
        scenario : str
            SSP scenario (ssp126, ssp245, ssp370, ssp585).
        year : int
            Target year (2030-2150).
        """
        if scenario not in IPCC_AR6_SLR:
            raise ValueError(f"Unknown scenario: {scenario}")

        slr_data = IPCC_AR6_SLR[scenario]
        years = sorted(slr_data.keys())
        values = [slr_data[y] for y in years]

        global_slr = float(np.interp(year, years, values))
        regional_slr = global_slr * self.regional_factor

        # Approximate uncertainty (5th-95th percentile)
        low = regional_slr * 0.6
        high = regional_slr * 1.7

        logger.info(
            "SLR %s @%d: %.3fm (global: %.3fm, range: %.3f-%.3fm)",
            scenario, year, regional_slr, global_slr, low, high,
        )

        return SeaLevelRiseResult(
            rise_m=regional_slr,
            scenario=scenario,
            year=year,
            global_mean_m=global_slr,
            regional_factor=self.regional_factor,
            uncertainty_range_m=(low, high),
        )
