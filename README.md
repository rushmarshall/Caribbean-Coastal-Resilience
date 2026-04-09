<img width="100%" src="https://capsule-render.vercel.app/api?type=waving&color=0:111111,30:333333,60:666666,100:999999&height=180&section=header&text=Caribbean%20Coastal%20Resilience&fontSize=36&fontColor=FFFFFF&animation=fadeIn&fontAlignY=36&desc=Compound%20Flood%20Risk%20Framework%20for%20Small%20Island%20Developing%20States&descSize=13&descColor=CCCCCC&descAlignY=56"/>

<p align="center">
<img src="https://img.shields.io/badge/Python-3.9+-333333?style=flat-square&logo=python&logoColor=white" alt="Python"/>
<img src="https://img.shields.io/badge/License-MIT-333333?style=flat-square" alt="License"/>
<img src="https://img.shields.io/badge/SIDS-333333?style=flat-square" alt="SIDS"/>
<img src="https://img.shields.io/badge/IPCC_AR6-333333?style=flat-square" alt="IPCC"/>
<img src="https://img.shields.io/badge/CI-passing-333333?style=flat-square" alt="CI"/>
</p>

---

## Overview

**Caribbean Coastal Resilience** is a Python framework for compound flood risk assessment in Caribbean Small Island Developing States (SIDS). It integrates tropical cyclone storm surge, sea level rise projections, extreme rainfall, and socioeconomic vulnerability to quantify multi-hazard coastal flood risk under current and future climate scenarios.

Developed to support climate adaptation planning for island nations where compound flooding — the joint occurrence of storm surge, rainfall, and elevated sea levels — poses an existential threat to communities, infrastructure, and ecosystems.

---

## Motivation

Caribbean SIDS face disproportionate climate risk:

- **Sea level rise** projections of 0.3–1.0m by 2100 (IPCC AR6) threaten low-lying coastal zones
- **Tropical cyclones** are intensifying, with compound surge-rainfall events increasing
- **Limited land area** concentrates population and infrastructure in flood-prone coastal strips
- **Traditional single-hazard assessments** underestimate risk from joint extreme events

This framework addresses these gaps by modeling compound flood interactions and their cascading impacts on socially vulnerable communities.

---

## Features

- **Tropical Cyclone Modeling** — Parametric wind and storm surge estimation using Holland vortex model
- **Sea Level Rise Scenarios** — IPCC AR6 projections (SSP1-2.6 through SSP5-8.5) with local adjustments
- **Extreme Rainfall** — IDF curve analysis, GEV/GPD extreme value fitting, climate-scaled projections
- **Compound Flood Risk** — Copula-based joint probability of surge, rainfall, and sea level drivers
- **Social Vulnerability** — Multi-indicator index incorporating poverty, housing quality, infrastructure access
- **Damage Functions** — Depth-damage curves for Caribbean building typologies
- **Island-Specific** — Pre-configured for 13 Caribbean island nations
- **Scenario Analysis** — Current climate, 2050 mid-century, 2100 end-century projections

---

## Installation

```bash
pip install caribbean-coastal-resilience
```

Or from source:

```bash
git clone https://github.com/rushmarshall/Caribbean-Coastal-Resilience.git
cd Caribbean-Coastal-Resilience
pip install -e ".[dev]"
```

---

## Quick Start

```python
from ccr import CompoundFloodAssessment

assessment = CompoundFloodAssessment(
    island="Jamaica",
    scenario="ssp245",
    time_horizon=2050,
)

# Model individual hazards
surge = assessment.model_storm_surge(
    category=3,
    approach_angle=180,
    forward_speed=20,
)

rainfall = assessment.model_extreme_rainfall(
    return_period=100,
    duration_hours=24,
)

slr = assessment.get_sea_level_rise()

# Compound flood analysis
compound = assessment.compound_analysis(
    surge=surge,
    rainfall=rainfall,
    sea_level_rise=slr,
    copula="gumbel",
)

# Risk assessment with vulnerability
risk = assessment.assess_risk(
    compound_flood=compound,
    include_vulnerability=True,
    damage_function="caribbean_residential",
)

print(f"Expected Annual Damage: ${risk.ead:,.0f}")
print(f"Population at Risk: {risk.population_exposed:,}")
risk.export_report("jamaica_compound_risk_2050.html")
```

---

## Supported Islands

| Island | Area (km2) | Coastal Pop. | Default Tide Gauge |
|:-------|:-----------|:-------------|:------------------|
| Jamaica | 10,991 | 1.2M | Kingston |
| Trinidad | 5,131 | 0.8M | Port of Spain |
| Barbados | 431 | 0.2M | Bridgetown |
| Bahamas | 13,943 | 0.3M | Nassau |
| Haiti | 27,750 | 3.1M | Port-au-Prince |
| Cuba | 109,884 | 4.2M | Havana |
| Dominican Republic | 48,671 | 3.8M | Santo Domingo |
| Puerto Rico | 9,104 | 1.9M | San Juan |
| Guadeloupe | 1,628 | 0.3M | Pointe-a-Pitre |
| Martinique | 1,128 | 0.2M | Fort-de-France |
| St. Lucia | 617 | 0.1M | Castries |
| Grenada | 344 | 0.06M | St. George's |
| Dominica | 751 | 0.04M | Roseau |

---

## Architecture

```
ccr/
├── hazards/            # Individual hazard models
│   ├── surge.py            Parametric storm surge (Holland model)
│   ├── rainfall.py         Extreme rainfall & IDF analysis
│   ├── sea_level.py        IPCC AR6 sea level rise projections
│   └── tropical_cyclone.py Cyclone wind field modeling
├── exposure/           # Asset and population exposure
│   ├── buildings.py        Building stock characterization
│   └── population.py       Population distribution mapping
├── vulnerability/      # Damage and vulnerability
│   ├── damage_curves.py    Depth-damage functions
│   └── social_index.py     Social vulnerability indicators
├── risk/               # Risk integration
│   ├── compound.py         Copula-based compound probability
│   ├── assessment.py       End-to-end risk assessment
│   └── scenarios.py        Climate scenario management
└── islands/            # Island-specific configuration
    └── registry.py         Island metadata and defaults
```

---

## Methodology

The framework follows a multi-hazard risk assessment workflow:

```
Hazard Identification → Exposure Analysis → Vulnerability Assessment → Risk Quantification
         |                     |                      |                       |
   Storm surge           Building stock         Damage curves          Expected Annual
   Extreme rainfall      Population             Social vulnerability   Damage (EAD)
   Sea level rise        Infrastructure         Adaptive capacity      Population at Risk
         |                     |                      |                       |
         └─── Compound probability (Copula) ──────────┘                       │
                                                                              │
                              Scenario Analysis (SSP x Time Horizon) ─────────┘
```

---

## Contributing

Contributions welcome, particularly from Caribbean researchers and practitioners. Please open an issue to discuss proposed changes.

```bash
git clone https://github.com/rushmarshall/Caribbean-Coastal-Resilience.git
cd Caribbean-Coastal-Resilience
pip install -e ".[dev]"
pytest tests/ -v
```

---

<p align="center">
<sub>Developed at Hydrosense Lab, University of Virginia</sub>
<br>
<sub>Supporting climate adaptation for Caribbean Small Island Developing States</sub>
</p>

<img width="100%" src="https://capsule-render.vercel.app/api?type=waving&color=0:999999,30:666666,60:333333,100:111111&height=100&section=footer"/>
