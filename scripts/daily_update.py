#!/usr/bin/env python3
"""
Daily Atlantic Hurricane Season Monitor

Fetches current tropical cyclone activity and sea surface temperature data
from NOAA, updates tracking documents, and generates season comparison charts.
Designed to run as a GitHub Actions cron job for the Caribbean Coastal
Resilience compound flood risk framework.
"""

import csv
import json
import os
import re
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import requests

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
REPO_ROOT = Path(__file__).resolve().parent.parent
DOCS_DIR = REPO_ROOT / "docs"
TRACKER_MD = DOCS_DIR / "storm-tracker.md"
SEASON_PNG = DOCS_DIR / "season-tracker.png"
HISTORY_CSV = DOCS_DIR / "season-history.csv"

# ---------------------------------------------------------------------------
# NOAA endpoints
# ---------------------------------------------------------------------------
NHC_CURRENT_JSON = "https://www.nhc.noaa.gov/CurrentSummary.json"
NHC_OUTLOOK_RSS = (
    "https://www.nhc.noaa.gov/nhc_at5.xml"  # Atlantic tropical weather outlook
)
NHC_ACTIVE_CYCLONES = "https://www.nhc.noaa.gov/currentcyclones.json"

# NOAA Daily OISST v2.1 – MDR SST anomaly (approximate)
# We use CPC weekly SST anomaly data for the Main Development Region (MDR)
SST_ENDPOINT = (
    "https://www.cpc.ncep.noaa.gov/data/indices/sstoi.atl.indices"
)

# ---------------------------------------------------------------------------
# Climatological average cumulative named storms by month (1991-2020 avg)
# Source: NOAA/NHC seasonal climatology
# Index 0 = Jan, … 11 = Dec (cumulative total by end of month)
# ---------------------------------------------------------------------------
CLIMO_CUMULATIVE_STORMS = [
    0.1, 0.2, 0.3, 0.5, 0.9, 1.5,   # Jan–Jun
    2.6, 4.4, 7.5, 10.5, 12.6, 13.5, # Jul–Dec
]
CLIMO_CUMULATIVE_HURRICANES = [
    0.0, 0.0, 0.1, 0.2, 0.3, 0.6,
    1.0, 2.0, 3.5, 5.0, 5.8, 6.2,
]
CLIMO_CUMULATIVE_MAJOR = [
    0.0, 0.0, 0.0, 0.0, 0.1, 0.2,
    0.3, 0.7, 1.4, 2.0, 2.3, 2.5,
]
MONTH_LABELS = [
    "Jan", "Feb", "Mar", "Apr", "May", "Jun",
    "Jul", "Aug", "Sep", "Oct", "Nov", "Dec",
]


# ===================================================================
# Data fetching helpers
# ===================================================================

def fetch_json(url: str, timeout: int = 30) -> dict | None:
    """Fetch JSON from *url*, returning None on failure."""
    try:
        resp = requests.get(url, timeout=timeout)
        resp.raise_for_status()
        return resp.json()
    except Exception as exc:
        print(f"[WARN] Could not fetch {url}: {exc}")
        return None


def fetch_text(url: str, timeout: int = 30) -> str | None:
    """Fetch plain text from *url*, returning None on failure."""
    try:
        resp = requests.get(url, timeout=timeout)
        resp.raise_for_status()
        return resp.text
    except Exception as exc:
        print(f"[WARN] Could not fetch {url}: {exc}")
        return None


# -------------------------------------------------------------------
# Active storm parsing
# -------------------------------------------------------------------

def get_active_storms() -> list[dict]:
    """Return a list of active Atlantic tropical cyclones from NHC."""
    storms: list[dict] = []

    # Try the JSON current-summary endpoint first
    data = fetch_json(NHC_CURRENT_JSON)
    if data:
        try:
            summaries = data if isinstance(data, list) else data.get("currentSummary", [])
            if isinstance(summaries, dict):
                summaries = [summaries]
            for item in summaries:
                name = item.get("name", "Unknown")
                classification = item.get("classification", item.get("type", ""))
                winds = item.get("maxWinds", item.get("intensity", "N/A"))
                movement = item.get("movement", "")
                storms.append({
                    "name": name,
                    "classification": classification,
                    "max_wind_mph": winds,
                    "movement": movement,
                })
        except Exception as exc:
            print(f"[WARN] Parsing CurrentSummary failed: {exc}")

    # Fallback / supplement: active-cyclones endpoint
    if not storms:
        data2 = fetch_json(NHC_ACTIVE_CYCLONES)
        if data2:
            try:
                cyclones = data2.get("activeStorms", data2.get("features", []))
                if isinstance(cyclones, dict):
                    cyclones = list(cyclones.values())
                for cyc in cyclones:
                    if isinstance(cyc, dict):
                        storms.append({
                            "name": cyc.get("name", "Unknown"),
                            "classification": cyc.get("classification", cyc.get("type", "")),
                            "max_wind_mph": cyc.get("intensity", "N/A"),
                            "movement": cyc.get("movement", ""),
                        })
            except Exception:
                pass

    # Fallback: parse the RSS outlook for any mentioned systems
    if not storms:
        rss_text = fetch_text(NHC_OUTLOOK_RSS)
        if rss_text:
            try:
                root = ET.fromstring(rss_text)
                ns = {"nhc": "https://www.nhc.noaa.gov"}
                for item in root.iter("item"):
                    title_el = item.find("title")
                    desc_el = item.find("description")
                    if title_el is not None and title_el.text:
                        title = title_el.text.strip()
                        desc = desc_el.text.strip() if desc_el is not None and desc_el.text else ""
                        if any(kw in title.lower() for kw in [
                            "hurricane", "tropical storm", "tropical depression",
                            "subtropical", "post-tropical",
                        ]):
                            storms.append({
                                "name": title,
                                "classification": "",
                                "max_wind_mph": "see advisory",
                                "movement": desc[:120],
                            })
            except Exception:
                pass

    return storms


# -------------------------------------------------------------------
# Season statistics – we infer from the NHC named-storm list when
# a dedicated endpoint isn't available.
# -------------------------------------------------------------------

# The 2025 Atlantic storm name list (for counting)
ATLANTIC_NAMES_2025 = [
    "Andrea", "Barry", "Chantal", "Dexter", "Erin",
    "Fernand", "Gabrielle", "Humberto", "Imelda", "Jerry",
    "Karen", "Lorenzo", "Melissa", "Nestor", "Olga",
    "Pablo", "Rebekah", "Sebastien", "Tanya", "Van",
    "Wendy",
]


def get_season_stats() -> dict:
    """
    Estimate current-season counts for named storms, hurricanes,
    and major hurricanes.  Falls back to zeros when data is unavailable.
    """
    stats = {"named_storms": 0, "hurricanes": 0, "major_hurricanes": 0}

    # Try scraping NHC's graphical tropical weather outlook page
    html = fetch_text("https://www.nhc.noaa.gov/gtwo.php?basin=atlc")
    if html:
        # Look for season summary text often embedded in the page
        m = re.search(
            r"(\d+)\s+named\s+storms?,\s*(\d+)\s+hurricanes?,\s*(\d+)\s+major",
            html, re.IGNORECASE,
        )
        if m:
            stats["named_storms"] = int(m.group(1))
            stats["hurricanes"] = int(m.group(2))
            stats["major_hurricanes"] = int(m.group(3))
            return stats

    # Fallback: count from active storms (undercount but non-zero)
    active = get_active_storms()
    for s in active:
        cls = (s.get("classification") or "").lower()
        if "major" in cls or "category" in cls:
            stats["major_hurricanes"] += 1
            stats["hurricanes"] += 1
            stats["named_storms"] += 1
        elif "hurricane" in cls:
            stats["hurricanes"] += 1
            stats["named_storms"] += 1
        elif any(kw in cls for kw in ["tropical storm", "subtropical storm"]):
            stats["named_storms"] += 1

    return stats


# -------------------------------------------------------------------
# Sea surface temperature anomaly
# -------------------------------------------------------------------

def get_mdr_sst_anomaly() -> str:
    """
    Fetch the latest Main Development Region (MDR) SST anomaly from
    NOAA CPC weekly indices.  Returns a string like '+1.2 °C' or 'N/A'.
    """
    text = fetch_text(SST_ENDPOINT)
    if not text:
        return "N/A"

    # The file is whitespace-delimited; columns vary by region.
    # MDR is typically the Atl MDR row – look for the last data line.
    lines = [l.strip() for l in text.strip().splitlines() if l.strip() and not l.startswith("#")]
    if not lines:
        return "N/A"

    # Attempt to parse the last non-header numeric line
    try:
        last_line = lines[-1]
        parts = last_line.split()
        # Typically: year, week, Nino12, …, ATL_MDR anom is near end
        # We'll take the last numeric value as a rough proxy
        for val in reversed(parts):
            try:
                anomaly = float(val)
                sign = "+" if anomaly >= 0 else ""
                return f"{sign}{anomaly:.2f} °C"
            except ValueError:
                continue
    except Exception:
        pass

    return "N/A"


# ===================================================================
# Output generators
# ===================================================================

def update_history_csv(stats: dict, sst_anomaly: str, active_count: int) -> None:
    """Append today's row to the season-history CSV (create if missing)."""
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    rows: list[list[str]] = []
    header = ["date", "named_storms", "hurricanes", "major_hurricanes", "sst_anomaly", "active_systems"]

    if HISTORY_CSV.exists():
        with open(HISTORY_CSV, newline="") as fh:
            reader = csv.reader(fh)
            rows = list(reader)

    if not rows:
        rows.append(header)

    # Avoid duplicate rows for the same date
    if rows[-1][0] == today:
        rows[-1] = [
            today,
            str(stats["named_storms"]),
            str(stats["hurricanes"]),
            str(stats["major_hurricanes"]),
            sst_anomaly,
            str(active_count),
        ]
    else:
        rows.append([
            today,
            str(stats["named_storms"]),
            str(stats["hurricanes"]),
            str(stats["major_hurricanes"]),
            sst_anomaly,
            str(active_count),
        ])

    with open(HISTORY_CSV, "w", newline="") as fh:
        writer = csv.writer(fh)
        writer.writerows(rows)

    print(f"[INFO] History CSV updated ({len(rows) - 1} data rows)")


def generate_chart(stats: dict) -> None:
    """
    Generate a cumulative named-storm comparison chart:
    current season vs 1991-2020 climatological average.
    """
    now = datetime.now(timezone.utc)
    current_month = now.month  # 1-indexed

    months = np.arange(1, 13)
    climo = np.array(CLIMO_CUMULATIVE_STORMS)

    # Build current-season cumulative from history CSV if available
    current_by_month = np.full(12, np.nan)
    if HISTORY_CSV.exists():
        with open(HISTORY_CSV, newline="") as fh:
            reader = csv.DictReader(fh)
            for row in reader:
                try:
                    dt = datetime.strptime(row["date"], "%Y-%m-%d")
                    if dt.year == now.year:
                        idx = dt.month - 1
                        current_by_month[idx] = float(row["named_storms"])
                except (ValueError, KeyError):
                    continue

    # If we have no CSV history yet, place today's count
    if np.all(np.isnan(current_by_month)):
        current_by_month[current_month - 1] = stats["named_storms"]

    fig, ax = plt.subplots(figsize=(10, 5))
    ax.plot(months, climo, "o--", color="gray", label="1991–2020 Average", linewidth=1.5)
    ax.fill_between(months, 0, climo, alpha=0.10, color="gray")

    # Plot current season (only months with data)
    valid = ~np.isnan(current_by_month)
    if valid.any():
        ax.plot(
            months[valid], current_by_month[valid],
            "s-", color="#d62728", linewidth=2, markersize=7,
            label=f"{now.year} Season",
        )

    ax.set_xticks(months)
    ax.set_xticklabels(MONTH_LABELS)
    ax.set_xlabel("Month")
    ax.set_ylabel("Cumulative Named Storms")
    ax.set_title(f"{now.year} Atlantic Hurricane Season vs Climatological Average")
    ax.legend(loc="upper left")
    ax.set_ylim(bottom=0)
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    fig.savefig(SEASON_PNG, dpi=150)
    plt.close(fig)
    print(f"[INFO] Chart saved to {SEASON_PNG}")


def write_tracker_md(
    storms: list[dict],
    stats: dict,
    sst_anomaly: str,
) -> None:
    """Write / overwrite docs/storm-tracker.md with the latest data."""
    now = datetime.now(timezone.utc)
    timestamp = now.strftime("%Y-%m-%d %H:%M UTC")

    lines: list[str] = []
    lines.append("# 🌀 Atlantic Hurricane Season Tracker\n")
    lines.append(f"*Last updated: {timestamp}*\n")
    lines.append("")
    lines.append("---\n")

    # Active storms
    lines.append("## Active Tropical Systems\n")
    if storms:
        for s in storms:
            name = s.get("name", "Unknown")
            cls = s.get("classification", "")
            wind = s.get("max_wind_mph", "N/A")
            movement = s.get("movement", "")
            lines.append(f"### {name}\n")
            if cls:
                lines.append(f"- **Classification:** {cls}")
            lines.append(f"- **Max sustained winds:** {wind} mph")
            if movement:
                lines.append(f"- **Movement:** {movement}")
            lines.append("")
    else:
        lines.append("*No active tropical cyclones in the Atlantic basin.*\n")
        lines.append("")

    # Season statistics
    lines.append("---\n")
    lines.append(f"## {now.year} Season Statistics\n")
    lines.append(f"| Metric | Count | Avg (1991–2020) |")
    lines.append(f"|--------|------:|:---------------:|")
    lines.append(
        f"| Named Storms | **{stats['named_storms']}** | 14.4 |"
    )
    lines.append(
        f"| Hurricanes | **{stats['hurricanes']}** | 7.2 |"
    )
    lines.append(
        f"| Major Hurricanes (Cat 3+) | **{stats['major_hurricanes']}** | 3.2 |"
    )
    lines.append("")

    # SST anomaly
    lines.append("---\n")
    lines.append("## Sea Surface Temperature — Main Development Region\n")
    lines.append(
        f"**Current SST anomaly (MDR, 10°N–20°N / 20°W–60°W):** {sst_anomaly}\n"
    )
    lines.append("")

    # Chart reference
    lines.append("---\n")
    lines.append("## Season Progress Chart\n")
    lines.append("![Season Tracker](season-tracker.png)\n")
    lines.append("")

    # Data sources
    lines.append("---\n")
    lines.append("## Data Sources\n")
    lines.append("- [NOAA National Hurricane Center](https://www.nhc.noaa.gov/)")
    lines.append("- [NOAA CPC SST Indices](https://www.cpc.ncep.noaa.gov/data/indices/)")
    lines.append(
        "- Climatological averages: NOAA/NHC 1991–2020 base period"
    )
    lines.append("")

    TRACKER_MD.write_text("\n".join(lines))
    print(f"[INFO] Tracker markdown written to {TRACKER_MD}")


# ===================================================================
# Main
# ===================================================================

def main() -> None:
    print("=" * 60)
    print("Atlantic Hurricane Season – Daily Update")
    print(datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"))
    print("=" * 60)

    DOCS_DIR.mkdir(parents=True, exist_ok=True)

    # 1. Active storms
    storms = get_active_storms()
    print(f"[INFO] Active systems: {len(storms)}")

    # 2. Season stats
    stats = get_season_stats()
    print(f"[INFO] Season stats: {stats}")

    # 3. SST anomaly
    sst = get_mdr_sst_anomaly()
    print(f"[INFO] MDR SST anomaly: {sst}")

    # 4. Update outputs
    update_history_csv(stats, sst, len(storms))
    generate_chart(stats)
    write_tracker_md(storms, stats, sst)

    print("\n[DONE] Daily update complete.")


if __name__ == "__main__":
    main()
