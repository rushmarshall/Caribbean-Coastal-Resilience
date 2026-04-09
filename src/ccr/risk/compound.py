"""Copula-based compound flood probability analysis.

Models the joint probability of multiple flood drivers
(surge, rainfall, sea level rise) using copula functions.
"""
from __future__ import annotations
import logging
import numpy as np
from dataclasses import dataclass
from typing import Any

logger = logging.getLogger(__name__)

@dataclass
class CompoundFloodResult:
    """Compound flood analysis output."""
    total_flood_depth_m: float
    surge_component_m: float
    rainfall_component_m: float
    slr_component_m: float
    joint_probability: float
    copula_type: str

class CompoundFloodModel:
    """Copula-based compound flood analysis.

    Models dependence between flood drivers using Archimedean
    copulas (Gumbel, Clayton, Frank) to estimate joint exceedance
    probabilities of compound flood events.
    """

    def __init__(self, copula: str = "gumbel", theta: float = 2.5) -> None:
        valid = {"gumbel", "clayton", "frank", "independence"}
        if copula not in valid:
            raise ValueError(f"Copula must be one of {valid}")
        self.copula = copula
        self.theta = theta

    def analyze(
        self,
        surge_m: float,
        rainfall_depth_mm: float,
        sea_level_rise_m: float,
        drainage_capacity_mm_hr: float = 25.0,
        return_period: int = 100,
    ) -> CompoundFloodResult:
        """Compute compound flood depth and joint probability.

        Parameters
        ----------
        surge_m : float
            Storm surge height in meters.
        rainfall_depth_mm : float
            Total rainfall depth in millimeters.
        sea_level_rise_m : float
            Sea level rise in meters.
        drainage_capacity_mm_hr : float
            Urban drainage capacity (excess becomes pluvial flooding).
        return_period : int
            Design return period for marginal probabilities.
        """
        # Convert rainfall excess to pluvial flood depth (simplified)
        excess_rainfall_mm = max(rainfall_depth_mm - drainage_capacity_mm_hr * 24, 0)
        pluvial_depth_m = excess_rainfall_mm / 1000.0

        # Total compound flood depth
        total = surge_m + pluvial_depth_m + sea_level_rise_m

        # Marginal exceedance probabilities
        p_surge = 1.0 / return_period
        p_rainfall = 1.0 / return_period

        # Joint probability via copula
        if self.copula == "gumbel":
            joint_p = self._gumbel_copula(p_surge, p_rainfall)
        elif self.copula == "clayton":
            joint_p = self._clayton_copula(p_surge, p_rainfall)
        elif self.copula == "frank":
            joint_p = self._frank_copula(p_surge, p_rainfall)
        else:
            joint_p = p_surge * p_rainfall  # independence

        logger.info(
            "Compound flood: %.2fm (surge=%.2f + pluvial=%.2f + SLR=%.2f), P=%.6f",
            total, surge_m, pluvial_depth_m, sea_level_rise_m, joint_p,
        )

        return CompoundFloodResult(
            total_flood_depth_m=float(total),
            surge_component_m=surge_m,
            rainfall_component_m=pluvial_depth_m,
            slr_component_m=sea_level_rise_m,
            joint_probability=float(joint_p),
            copula_type=self.copula,
        )

    def _gumbel_copula(self, u: float, v: float) -> float:
        """Gumbel copula: C(u,v) = exp(-[(-ln u)^theta + (-ln v)^theta]^(1/theta))"""
        u = max(u, 1e-10)
        v = max(v, 1e-10)
        a = (-np.log(u)) ** self.theta
        b = (-np.log(v)) ** self.theta
        return float(np.exp(-((a + b) ** (1.0 / self.theta))))

    def _clayton_copula(self, u: float, v: float) -> float:
        """Clayton copula: C(u,v) = (u^-theta + v^-theta - 1)^(-1/theta)"""
        u = max(u, 1e-10)
        v = max(v, 1e-10)
        val = u ** (-self.theta) + v ** (-self.theta) - 1
        return float(max(val, 1e-10) ** (-1.0 / self.theta))

    def _frank_copula(self, u: float, v: float) -> float:
        """Frank copula."""
        a = np.exp(-self.theta * u) - 1
        b = np.exp(-self.theta * v) - 1
        c = np.exp(-self.theta) - 1
        return float(-np.log(1 + a * b / c) / self.theta)
