#!/usr/bin/env python3
"""
Add additional information to MPC Code list and save it to a local file.

Usage:
    mpccode.py
    mpccode.py --refresh-geocode

Default:
    Uses cached geocoding only. No live reverse-geocoding requests are made.

Optional:
    --refresh-geocode
        For entries missing from cache, perform live reverse geocoding
        slowly/politely and save the results to cache.

(C) Quanzhi Ye
"""

from urllib.request import urlopen
from bs4 import BeautifulSoup
from geopy.geocoders import Nominatim
from geopy.extra.rate_limiter import RateLimiter
from geopy.exc import GeocoderRateLimited, GeocoderServiceError, GeocoderTimedOut
import argparse
import json
import math
import os
import re
import time
import requests
from typing import Optional, Dict, Any

# ============================================================================
# Constants
# ============================================================================

EARTH_MAJOR_AXIS = 6378137.0
EARTH_MINOR_AXIS = 6356752.314140347

API_URL = "https://data.minorplanetcenter.net/api/obscodes"
API_FIELDS = ["firstdate", "lastdate", "observations_type", "old_names", "web_link"]

MPCCODE_URL = "https://www.minorplanetcenter.net/iau/lists/ObsCodes.html"
OUTPUT_JSON = "mpccode.json"
GEOCODE_CACHE_FILE = "mpccode_geocode_cache.json"

# Public Nominatim settings.
# Keep these conservative. Even with this, live bulk refresh may still be throttled.
GEOCODE_MIN_DELAY_SECONDS = 1.2
GEOCODE_ERROR_WAIT_SECONDS = 10.0
GEOCODE_MAX_RETRIES = 1

# Save cache every N new geocode lookups
CACHE_SAVE_EVERY = 20

# Light throttling for MPC API requests
MPC_API_DELAY_SECONDS = 0.15


# ============================================================================
# Utility functions
# ============================================================================

def calculate_latitude(rho_sin_phi: float, rho_cos_phi: float) -> float:
    """
    Convert MPC rho*sin(phi) and rho*cos(phi) values to geodetic latitude (deg).
    """
    a = 1.0
    b = EARTH_MINOR_AXIS / EARTH_MAJOR_AXIS
    fy = abs(rho_sin_phi)
    fx = abs(rho_cos_phi)

    if rho_cos_phi == 0:
        lat = math.pi / 2
    else:
        c_squared = a * a - b * b
        e = (b * fy - c_squared) / (a * fx)
        f = (b * fy + c_squared) / (a * fx)
        p = (4.0 / 3.0) * (e * f + 1.0)
        q = 2.0 * (e * e - f * f)
        d = p * p * p + q * q

        if d >= 0:
            sqrt_d = math.sqrt(d)
            v = math.pow(sqrt_d - q, 1 / 3) - math.pow(sqrt_d + q, 1 / 3)
        else:
            sqp = math.sqrt(-p)
            temp_ang = math.acos(q / (sqp * p))
            v = 2.0 * sqp * math.cos(temp_ang / 3.0)

        g = (math.sqrt(e * e + v) + e) * 0.5
        t = math.sqrt(g * g + (f - v * g) / (2.0 * g - e)) - g
        lat = math.atan2(a * (1.0 - t * t), 2.0 * b * t)

    if rho_sin_phi < 0:
        lat = -lat
    if rho_cos_phi < 0:
        lat = math.pi - lat

    return math.degrees(lat)


def load_json_file(path: str, default: Any) -> Any:
    if not os.path.exists(path):
        return default

    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"[WARN] Could not read {path}: {e}")
        return default


def save_json_file(path: str, data: Any) -> None:
    tmp = f"{path}.tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    os.replace(tmp, path)


def normalize_cache_key(latitude: float, longitude: float) -> str:
    return f"{latitude:.5f},{longitude:.5f}"


def extract_city(address: Dict[str, Any]) -> str:
    for key in ("city", "town", "village", "municipality", "locality", "hamlet"):
        if key in address:
            return address.get(key, "")
    return ""


def fetch_mpc_obscode_fields(
    session: requests.Session,
    obscode: str,
    retries: int = 3,
    backoff_s: float = 0.5,
) -> Dict[str, Optional[str]]:
    """
    Query MPC obscodes API for a single code and return only the requested fields.
    Returns a dict with keys in API_FIELDS; values may be None if unavailable.
    """
    payload = {"obscode": obscode}

    for attempt in range(1, retries + 1):
        try:
            resp = session.get(API_URL, json=payload, timeout=15)
            resp.raise_for_status()
            data = resp.json() if resp.content else {}
            return {k: data.get(k, None) for k in API_FIELDS}
        except requests.RequestException as e:
            if attempt == retries:
                print(f"[WARN] MPC API request failed for {obscode}: {e}")
                return {k: None for k in API_FIELDS}
            time.sleep(backoff_s * attempt)

    return {k: None for k in API_FIELDS}


# ============================================================================
# Geocoding cache
# ============================================================================

class GeocodeCache:
    def __init__(self, path: str):
        self.path = path
        self.data: Dict[str, Optional[Dict[str, str]]] = load_json_file(path, {})
        self.new_entries_since_save = 0

    def has_key(self, latitude: float, longitude: float) -> bool:
        key = normalize_cache_key(latitude, longitude)
        return key in self.data

    def get(self, latitude: float, longitude: float) -> Optional[Dict[str, str]]:
        key = normalize_cache_key(latitude, longitude)
        return self.data.get(key)

    def set(self, latitude: float, longitude: float, value: Optional[Dict[str, str]]) -> None:
        key = normalize_cache_key(latitude, longitude)
        self.data[key] = value
        self.new_entries_since_save += 1
        if self.new_entries_since_save >= CACHE_SAVE_EVERY:
            self.save()

    def save(self) -> None:
        save_json_file(self.path, self.data)
        self.new_entries_since_save = 0


def make_reverse_geocoder() -> RateLimiter:
    geolocator = Nominatim(
        user_agent="MPECWatch/1.0 (contact: qye@umd.edu)",
        timeout=10,
    )

    reverse = RateLimiter(
        geolocator.reverse,
        min_delay_seconds=GEOCODE_MIN_DELAY_SECONDS,
        max_retries=GEOCODE_MAX_RETRIES,
        error_wait_seconds=GEOCODE_ERROR_WAIT_SECONDS,
        swallow_exceptions=False,
    )
    return reverse


def reverse_lookup(
    reverse_geocoder: Optional[RateLimiter],
    cache: GeocodeCache,
    latitude: float,
    longitude: float,
    enable_live_geocoding: bool = False,
) -> Optional[Dict[str, str]]:
    """
    Cache-first reverse lookup.

    Behavior:
      - If coordinate exists in cache, return cached value.
      - If not in cache and live geocoding disabled, return None.
      - If not in cache and live geocoding enabled, try reverse geocoding,
        store result (or None) in cache, then return it.
    """
    if cache.has_key(latitude, longitude):
        return cache.get(latitude, longitude)

    if not enable_live_geocoding or reverse_geocoder is None:
        return None

    query = f"{latitude},{longitude}"

    try:
        location = reverse_geocoder(query, language="en")
        if location is None:
            cache.set(latitude, longitude, None)
            return None

        address = location.raw.get("address", {})
        result = {
            "country": address.get("country", ""),
            "state": address.get("state", ""),
            "county": address.get("county", ""),
            "city": extract_city(address),
        }
        cache.set(latitude, longitude, result)
        return result

    except (GeocoderRateLimited, GeocoderTimedOut, GeocoderServiceError) as e:
        print(f"[WARN] Reverse geocoding failed for {query}: {e}")
        return None

    except Exception as e:
        print(f"[WARN] Unexpected geocoding error for {query}: {e}")
        return None


# ============================================================================
# MPC table parsing
# ============================================================================

def parse_table_entry(
    entry: str,
    reverse_geocoder: Optional[RateLimiter],
    geocode_cache: GeocodeCache,
    enable_live_geocoding: bool = False,
) -> Optional[Dict[str, Any]]:
    """
    Parse one MPC observatory code table entry.
    """
    if len(entry.strip()) < 3:
        return None

    match = re.match(r'(\w{3})\s+(\d+\.\d+)\s*(\d+\.\d+)\s*(\+|-)?(0\.\d+)\s*(.*)', entry)
    match1 = re.match(r'(\w{3})\s+(\w+)', entry)

    if match:
        longitude = float(match.group(2))
        cos_val = float(match.group(3))
        sign = match.group(4) or ""
        sin_val = float(sign + match.group(5))
        name = match.group(6).strip()

        latitude = calculate_latitude(sin_val, cos_val)

        if longitude == 0 and latitude == 0:
            return {
                "name": entry[30:].strip()
            }

        result = {
            "name": name,
            "lon": longitude,
            "lat": latitude,
            "country": "",
            "state": "",
            "county": "",
            "city": "",
        }

        geo = reverse_lookup(
            reverse_geocoder,
            geocode_cache,
            latitude,
            longitude,
            enable_live_geocoding=enable_live_geocoding,
        )
        if geo:
            result.update(geo)

        return result

    elif match1:
        return {
            "name": entry[30:].strip()
        }

    else:
        print(entry)
        raise ValueError("Invalid input format")


# ============================================================================
# Main
# ============================================================================

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Download and enrich MPC observatory codes."
    )
    parser.add_argument(
        "--refresh-geocode",
        action="store_true",
        help="Perform live reverse geocoding for cache misses.",
    )
    args = parser.parse_args()

    enable_live_geocoding = args.refresh_geocode

    # Download MPC code file
    html = urlopen(MPCCODE_URL).read()
    soup = BeautifulSoup(html, features="lxml")
    mpccode_text = soup.get_text()
    mpccode_lines = list(filter(None, mpccode_text.split('\n')))

    geocode_cache = GeocodeCache(GEOCODE_CACHE_FILE)

    reverse_geocoder = None
    if enable_live_geocoding:
        print("Live reverse geocoding enabled for cache misses.")
        reverse_geocoder = make_reverse_geocoder()
    else:
        print("Live reverse geocoding disabled. Using cache only.")

    d: Dict[str, Optional[Dict[str, Any]]] = {}

    # Build base dict from HTML list
    print("Parsing MPC observatory list...")
    for i, line in enumerate(mpccode_lines[1:], start=1):
        code = str(line[0:3])
        try:
            d[code] = parse_table_entry(
                line,
                reverse_geocoder,
                geocode_cache,
                enable_live_geocoding=enable_live_geocoding,
            )
        except Exception as e:
            print(f"[WARN] Failed to parse line for code {code}: {e}")
            d[code] = None

        if i % 100 == 0:
            print(f"Parsed {i} observatories...")

    # Save cache after parsing phase
    geocode_cache.save()

    # Enrich with MPC API fields
    print("Querying MPC API for additional observatory metadata...")
    with requests.Session() as session:
        session.headers.update({"User-Agent": "MPCCodeEnricher/1.0 (qye@umd.edu)"})

        for i, code in enumerate(d.keys(), start=1):
            if not code or len(code) != 3:
                continue

            api_fields = fetch_mpc_obscode_fields(session, code)

            if d[code] is None:
                d[code] = {}

            d[code].update(api_fields)

            time.sleep(MPC_API_DELAY_SECONDS)

            if i % 100 == 0:
                print(f"Processed {i} observatories in MPC API phase...")

    # Final writes
    geocode_cache.save()
    save_json_file(OUTPUT_JSON, d)

    print(f"Done. Wrote {OUTPUT_JSON}")
    print(f"Geocode cache saved to {GEOCODE_CACHE_FILE}")


if __name__ == "__main__":
    main()
