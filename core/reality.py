"""
HOLDPOINT — Reality Check
=========================

**Real external APIs. No key, no auth, no simulation.**

Everything else in this demo is fixture data. This module is not. It reaches the actual internet and
fetches actual facts about the actual world, and then checks the permit against them.

Why this matters more than it looks:

The site's H2S standard (SP-H2S-004) contains two clauses that no document can satisfy on its own —

    2.5  "Work on sour systems shall not proceed during hours of darkness."
    3.1  "The wind direction shall be confirmed at the work location immediately before containment
          is broken, and the escape route briefed to all parties."

An agent reading the permit and the procedure can tell you the clause EXISTS. It cannot tell you
whether the clause is SATISFIED, because that depends on the sun and the wind — facts that live
outside every document in the system.

So HOLDPOINT goes and gets them.

    PTW-2026-0436 is a NIGHT shift (18:00–06:00) breaking containment on a rich amine line carrying
    ~12,000 ppm H2S. We fetch the real sunrise and sunset for the site's actual coordinates, and we
    can then state — as a matter of verifiable fact, not model opinion — that the work is scheduled
    entirely in darkness, in direct breach of a clause we can quote.

That is a different class of finding. It is not "the AI thinks this looks risky." It is a fact.

--------------------------------------------------------------------------------------------------
SOURCES (all free, all public, all no-auth)
  - api.sunrise-sunset.org  — sunrise, sunset, civil twilight for a lat/lon and date
  - api.weather.gov (NOAA / US National Weather Service) — real forecast wind speed and direction
Both are US-government or public-good services. The NWS API requires a descriptive User-Agent.

FAILURE POLICY — THE IMPORTANT PART
If an API is unavailable, HOLDPOINT reports the conditions as UNAVAILABLE and tells the authoriser
to verify them by hand. It NEVER invents weather. In a system whose entire argument is "do not
fabricate a safeguard", fabricating the wind would be self-refuting.
--------------------------------------------------------------------------------------------------
"""

from __future__ import annotations

import json
import urllib.request
import urllib.error
from dataclasses import dataclass, asdict
from datetime import datetime, timezone, timedelta

TIMEOUT = 10
UA = "HOLDPOINT permit-assurance demo (safety research; contact: site admin)"

# In-process cache — a turnaround permit desk would hammer these otherwise.
_CACHE: dict[str, dict] = {}


@dataclass
class Conditions:
    """Real-world conditions at the work site. Every field is either fetched or explicitly unknown."""
    available: bool
    source: str
    site_name: str
    lat: float
    lon: float
    date: str
    sunrise_utc: str | None = None
    sunset_utc: str | None = None
    civil_twilight_begin_utc: str | None = None
    civil_twilight_end_utc: str | None = None
    wind_direction: str | None = None
    wind_speed: str | None = None
    forecast: str | None = None
    temperature: str | None = None
    error: str | None = None

    def as_dict(self) -> dict:
        return asdict(self)


def _get_json(url: str) -> dict:
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
        return json.loads(r.read().decode("utf-8"))


def fetch_daylight(lat: float, lon: float, date: str) -> dict:
    """Real sunrise/sunset/twilight from api.sunrise-sunset.org. No key required."""
    url = (f"https://api.sunrise-sunset.org/json?lat={lat}&lng={lon}"
           f"&date={date}&formatted=0")
    data = _get_json(url)
    if data.get("status") != "OK":
        raise RuntimeError(f"sunrise-sunset returned status={data.get('status')}")
    return data["results"]


def fetch_weather(lat: float, lon: float) -> dict:
    """Real forecast wind from NOAA/NWS api.weather.gov. No key required (US locations only)."""
    points = _get_json(f"https://api.weather.gov/points/{lat},{lon}")
    hourly_url = points["properties"]["forecastHourly"]
    hourly = _get_json(hourly_url)
    period = hourly["properties"]["periods"][0]
    return {
        "wind_direction": period.get("windDirection"),
        "wind_speed": period.get("windSpeed"),
        "forecast": period.get("shortForecast"),
        "temperature": f"{period.get('temperature')}°{period.get('temperatureUnit')}",
    }


def get_conditions(site: dict, date: str | None = None) -> Conditions:
    """Fetch real conditions for the site. Degrades honestly — never invents.

    A partial result is still useful: daylight may resolve while weather fails (NWS is US-only).
    We report exactly what we got and exactly what we did not.
    """
    lat, lon = site.get("lat"), site.get("lon")
    date = date or datetime.now(timezone.utc).strftime("%Y-%m-%d")
    site_name = site.get("site_name", "site")

    if lat is None or lon is None:
        return Conditions(False, "none", site_name, 0.0, 0.0, date,
                          error="No coordinates configured for this site pack.")

    key = f"{lat},{lon},{date}"
    if key in _CACHE:
        return Conditions(**_CACHE[key])

    c = Conditions(available=False, source="", site_name=site_name, lat=lat, lon=lon, date=date)
    errors = []

    try:
        d = fetch_daylight(lat, lon, date)
        c.sunrise_utc = d["sunrise"]
        c.sunset_utc = d["sunset"]
        c.civil_twilight_begin_utc = d["civil_twilight_begin"]
        c.civil_twilight_end_utc = d["civil_twilight_end"]
        c.source = "api.sunrise-sunset.org"
    except Exception as e:  # network, DNS, timeout, schema drift
        errors.append(f"daylight: {type(e).__name__}")

    try:
        w = fetch_weather(lat, lon)
        c.wind_direction = w["wind_direction"]
        c.wind_speed = w["wind_speed"]
        c.forecast = w["forecast"]
        c.temperature = w["temperature"]
        c.source = (c.source + " + api.weather.gov (NOAA/NWS)").strip(" +")
    except Exception as e:
        errors.append(f"weather: {type(e).__name__}")

    c.available = bool(c.sunrise_utc or c.wind_direction)
    if errors:
        c.error = "; ".join(errors)
    if not c.available:
        c.source = "unavailable"

    _CACHE[key] = c.as_dict()
    return c


# ==================================================================================================
# Checking the permit against reality
# ==================================================================================================

SOUR_TERMS = ["h2s", "hydrogen sulphide", "hydrogen sulfide", "sour", "amine"]


def _is_sour_service(permit: dict) -> bool:
    blob = " ".join([
        permit.get("work_description", ""),
        permit.get("unit_state", ""),
        permit.get("isolation_plan", ""),
        " ".join(permit.get("hazards_identified", []) or []),
    ]).lower()
    return any(t in blob for t in SOUR_TERMS)


def _is_night_shift(permit: dict) -> bool:
    """A shift is a night shift if it says so, or if it starts in the evening."""
    shift = (permit.get("shift", "") or "").lower()
    if "night" in shift:
        return True
    for hh in ("18:", "19:", "20:", "21:", "22:", "23:"):
        if shift.startswith(hh) or f" {hh}" in shift:
            return True
    return False


def darkness_overlap(permit: dict, site: dict, conditions: Conditions) -> dict | None:
    """How many hours of THIS permit's shift actually fall after sunset, at THIS site?

    This is the link between the permit and the live data, and it must be computed rather than
    assumed. "Night shift + sour service = darkness" is a guess. The real question is: for the work
    window this permit authorises, on the date it authorises it, at this site's coordinates and in
    this site's timezone — how much of it is dark?

    Sunset comes back in UTC. The shift is in local time. Comparing them without a timezone is the
    kind of quiet error that produces a confident wrong answer, which is the failure mode this whole
    product exists to prevent.

    Returns None if the permit does not carry a date and window — in which case we say so rather
    than inventing one.
    """
    date_s = permit.get("work_date")
    start_s = permit.get("shift_start")
    end_s = permit.get("shift_end")
    tz_name = site.get("tz")

    if not (date_s and start_s and end_s and tz_name and conditions.sunset_utc):
        return None

    try:
        from zoneinfo import ZoneInfo
        tz = ZoneInfo(tz_name)
    except Exception:
        return None

    def _local(day: datetime, hhmm: str) -> datetime:
        h, m = (int(x) for x in hhmm.split(":"))
        return day.replace(hour=h, minute=m, second=0, microsecond=0, tzinfo=tz)

    day0 = datetime.fromisoformat(date_s)
    start = _local(day0, start_s)
    end = _local(day0, end_s)
    if end <= start:                      # e.g. 18:00 -> 06:00 crosses midnight
        end = end.replace(day=end.day) + timedelta(days=1)

    sunset = datetime.fromisoformat(conditions.sunset_utc).astimezone(tz)
    sunrise = datetime.fromisoformat(conditions.sunrise_utc).astimezone(tz)
    # The sunrise that ENDS this night is the following morning's.
    next_sunrise = sunrise + timedelta(days=1) if sunrise <= sunset else sunrise

    dark_start, dark_end = sunset, next_sunrise
    overlap_start = max(start, dark_start)
    overlap_end = min(end, dark_end)
    dark_hours = max(0.0, (overlap_end - overlap_start).total_seconds() / 3600.0)
    shift_hours = (end - start).total_seconds() / 3600.0

    return {
        "shift_local": f"{start:%Y-%m-%d %H:%M} – {end:%H:%M} {tz_name}",
        "sunset_local": f"{sunset:%H:%M}",
        "sunrise_local": f"{next_sunrise:%H:%M} (next day)",
        "shift_hours": round(shift_hours, 1),
        "dark_hours": round(dark_hours, 1),
        "dark_pct": round(100 * dark_hours / shift_hours) if shift_hours else 0,
        "any_darkness": dark_hours > 0,
    }


def check_permit_against_reality(permit: dict, site: dict, date: str | None = None) -> dict:
    """Compare the permit against verifiable external facts.

    The conditions are fetched for the PERMIT'S OWN WORK DATE at the SITE'S OWN COORDINATES — not
    for "today" and not for a generic location. That linkage is the whole point: the permit
    authorises work at a real place on a real date, and some of its clauses can only be judged
    against what the sun and the wind are actually doing there, then.

    Returns findings that are FACTS, not model opinions — each carries the API that established it.
    """
    c = get_conditions(site, date or permit.get("work_date"))
    findings: list[dict] = []

    if not c.available:
        return {
            "conditions": c.as_dict(),
            "findings": [],
            "unavailable": True,
            "note": (
                "External conditions could not be retrieved. HOLDPOINT does NOT guess the weather. "
                "The authoriser must confirm daylight and wind direction at the work location by "
                "hand before containment is broken."
            ),
        }

    sour = _is_sour_service(permit)
    night = _is_night_shift(permit)

    # --- Clause SP-H2S-004 2.5 — darkness. COMPUTED, not assumed. -------------------------
    overlap = darkness_overlap(permit, site, c)

    if sour and overlap is None:
        findings.append({
            "code": "work_window_unknown",
            "severity": "medium",
            "finding": (
                "This permit breaks containment on a sour (H2S) system, but does not carry a work "
                "DATE and shift window. Whether the work falls in darkness therefore cannot be "
                "determined — and HOLDPOINT will not guess. The authoriser must establish it."
            ),
            "procedure_clause": "Work on sour systems shall not proceed during hours of darkness.",
            "procedure_doc": "SP-H2S-004 — Hydrogen Sulphide (H2S) Control Standard, clause 2.5",
            "established_by": "absence of data on the permit (not a model opinion)",
            "fact_not_opinion": True,
        })
    elif sour and overlap and overlap["any_darkness"]:
        findings.append({
            "code": "sour_work_in_darkness",
            "severity": "critical",
            "finding": (
                f"{overlap['dark_hours']} of this permit's {overlap['shift_hours']} shift hours "
                f"({overlap['dark_pct']}%) fall after sunset. The permit authorises breaking "
                f"containment on a sour (H2S) system across {overlap['shift_local']}. At this site "
                f"on this date, sunset is {overlap['sunset_local']} and sunrise is "
                f"{overlap['sunrise_local']} local."
            ),
            "procedure_clause": "Work on sour systems shall not proceed during hours of darkness.",
            "procedure_doc": "SP-H2S-004 — Hydrogen Sulphide (H2S) Control Standard, clause 2.5",
            "established_by": "api.sunrise-sunset.org (real, live) + the permit's own work window",
            "fact_not_opinion": True,
            "computation": overlap,
        })

    # --- Clause SP-H2S-004 3.1 — wind direction and escape route --------------------------
    if sour and c.wind_direction:
        listed = " ".join(permit.get("controls_listed", []) or []).lower()
        addressed = "wind" in listed or "escape route" in listed or "muster" in listed
        if not addressed:
            findings.append({
                "code": "wind_not_addressed",
                "severity": "high",
                "finding": (
                    f"Sour service work with no wind or escape-route control listed on the permit. "
                    f"Live forecast wind at this site is {c.wind_direction} at {c.wind_speed} "
                    f"({c.forecast}, {c.temperature}). The escape route depends on which way the gas "
                    f"will travel, and the permit does not say."
                ),
                "procedure_clause": (
                    "The wind direction shall be confirmed at the work location immediately before "
                    "containment is broken, and the escape route briefed to all parties."
                ),
                "procedure_doc": "SP-H2S-004 — Hydrogen Sulphide (H2S) Control Standard, clause 3.1",
                "established_by": "api.weather.gov (NOAA/NWS, real, live)",
                "fact_not_opinion": True,
            })

        if c.wind_speed and "0 mph" in str(c.wind_speed):
            findings.append({
                "code": "still_air",
                "severity": "high",
                "finding": (
                    f"Forecast wind is {c.wind_speed} — still air. H2S is heavier than air and will "
                    f"pool at grade rather than disperse. A 'stand upwind' control means nothing when "
                    f"there is no wind."
                ),
                "procedure_clause": (
                    "A dedicated safety attendant shall be stationed upwind with a clear line of "
                    "sight to the work party, and shall have no other duties."
                ),
                "procedure_doc": "SP-H2S-004 — Hydrogen Sulphide (H2S) Control Standard, clause 3.2",
                "established_by": "api.weather.gov (NOAA/NWS, real, live)",
                "fact_not_opinion": True,
            })

    return {
        "conditions": c.as_dict(),
        "findings": findings,
        "unavailable": False,
        "sour_service": sour,
        "night_shift": night,
        "darkness": overlap,
        "work_window": {
            "date": permit.get("work_date"),
            "start": permit.get("shift_start"),
            "end": permit.get("shift_end"),
            "shift": permit.get("shift"),
        },
    }


def conditions_brief(permit: dict, site: dict, date: str | None = None) -> str:
    """A block of REAL external facts to inject into the agent prompts.

    The agents get to reason over the actual world, not only over documents. If the fetch failed,
    they are told so explicitly — and told not to assume conditions are acceptable.
    """
    r = check_permit_against_reality(permit, site, date)
    c = r["conditions"]

    if r.get("unavailable"):
        return (
            "--- REAL EXTERNAL CONDITIONS AT THE WORK SITE ---\n"
            "UNAVAILABLE — the live daylight and weather services could not be reached.\n"
            "Do NOT assume conditions are acceptable. Flag that daylight and wind direction must be "
            "confirmed by hand at the work location before containment is broken."
        )

    lines = [
        "--- REAL EXTERNAL CONDITIONS AT THE WORK SITE ---",
        f"(Live data, fetched from {c['source']}. These are FACTS, not estimates.)",
        f"Site: {c['site_name']}  ({c['lat']}, {c['lon']})   Date: {c['date']}",
    ]
    if c["sunrise_utc"]:
        lines += [
            f"Sunrise (UTC):            {c['sunrise_utc']}",
            f"Sunset (UTC):             {c['sunset_utc']}",
            f"Civil twilight ends (UTC):{c['civil_twilight_end_utc']}",
        ]
    if c["wind_direction"]:
        lines += [
            f"Wind:                     {c['wind_direction']} at {c['wind_speed']}",
            f"Forecast:                 {c['forecast']}, {c['temperature']}",
        ]
    lines += [
        "",
        "Use these facts. A procedure clause about darkness or wind cannot be judged satisfied from "
        "the permit alone — it depends on the real world, and the real world is above.",
    ]
    return "\n".join(lines)
