# tranay/tools/sumo_handler.py

from __future__ import annotations

import os
import sys
import time
import hashlib
import subprocess
import xml.parsers.expat
from pathlib import Path
from typing import Tuple

import requests
from geopy.geocoders import Nominatim

#––– Configuration –––#
OVERPASS_MIRRORS: Tuple[str, ...] = (
    "https://overpass-api.de/api/interpreter",
    "https://overpass.kumi.systems/api/interpreter",
    "https://overpass.openstreetmap.fr/api/interpreter",
)
OVERPASS_TIMEOUT = 300       # seconds for HTTP requests
MAX_BBOX_AREA = 0.25         # degrees² (~1 000 km²)
SUMO_TOOLS_DIR = os.getenv("SUMO_TOOLS_DIR", "/usr/share/sumo/tools")
PYTHON = sys.executable      # path to the current Python interpreter

#––– Helpers –––#
def get_bbox_from_location_name(location_name: str) -> str:
    """
    Geocode via Nominatim and return bbox as 'south,west,north,east'.
    Raises ValueError if not found.
    """
    locator = Nominatim(user_agent="tranay_sumo_handler")
    place = locator.geocode(location_name, exactly_one=True, addressdetails=False)
    if not place:
        raise ValueError(f"Location '{location_name}' not found")
    south, north, west, east = map(float, place.raw["boundingbox"])
    return f"{south},{west},{north},{east}"

def _download_osm(bbox: str, dest: Path) -> None:
    """
    Download OSM XML for the given bbox, rotating through mirrors and checking content-type.
    Caches result into `dest`.
    """
    south, west, north, east = bbox.split(",")
    query = f"""
[out:xml][timeout:180];
(way[highway]({south},{west},{north},{east});>;);
out body;
"""
    last_err = None
    for url in OVERPASS_MIRRORS:
        try:
            resp = requests.post(url, data={"data": query}, timeout=OVERPASS_TIMEOUT)
            ct = resp.headers.get("Content-Type", "").lower()
            if resp.ok and "xml" in ct:
                dest.write_bytes(resp.content)
                return
            last_err = f"{url} → {resp.status_code} / {resp.headers.get('Content-Type')}"
        except Exception as e:
            last_err = str(e)
        time.sleep(2)
    raise RuntimeError(f"Overpass download failed after {len(OVERPASS_MIRRORS)} mirrors; last error: {last_err}")

def _validate_xml(path: Path) -> None:
    """
    Ensure the downloaded file is well-formed XML via Expat.
    """
    data = path.read_bytes()
    try:
        xml.parsers.expat.ParserCreate().Parse(data, True)
    except xml.parsers.expat.ExpatError as e:
        raise RuntimeError(f"Invalid OSM XML: {e}")

def _build_net(osm: Path, net: Path) -> None:
    """
    Invoke netconvert to turn OSM into a SUMO network.
    """
    cmd = [
        "netconvert",
        "--osm-files", str(osm),
        "-o", str(net),
        "--geometry.remove",
        "--ramps.guess",
        "--junctions.join",
        "--tls.guess-signals",
        "--tls.discard-simple",
        "--tls.join",
    ]
    try:
        subprocess.run(cmd, check=True, capture_output=True, text=True)
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"netconvert failed (code {e.returncode}):\n{e.stderr}")

def _build_routes(net: Path, trips: Path, routes: Path) -> None:
    """
    Generate random trips and convert them into routes.
    """
    # 1) randomTrips.py → trips.xml
    rt_script = Path(SUMO_TOOLS_DIR) / "randomTrips.py"
    rt_cmd = [
        PYTHON,
        str(rt_script),
        "-n", str(net),
        "-o", str(trips),
        "-b", "0", "-e", "3600",
        "-p", "1.0",
        "--trip-attributes", "departLane=\"best\" departSpeed=\"max\"",
        "--seed", "42",
    ]
    try:
        subprocess.run(rt_cmd, check=True, capture_output=True, text=True)
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"randomTrips.py failed (code {e.returncode}):\n{e.stderr}")

    # 2) duarouter → routes.xml
    dr_cmd = [
        "duarouter",
        "-n", str(net),
        "-t", str(trips),
        "-o", str(routes),
    ]
    try:
        subprocess.run(dr_cmd, check=True, capture_output=True, text=True)
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"duarouter failed (code {e.returncode}):\n{e.stderr}")

def generate_sumocfg_text(net_file: str, rou_file: str) -> str:
    """
    Return a complete .sumocfg content, linking net + route files.
    """
    return f"""<configuration>
    <input>
        <net-file value="{net_file}"/>
        <route-files value="{rou_file}"/>
    </input>
    <time>
        <begin value="0"/>
        <end value="3600"/>
    </time>
</configuration>
"""

#––– Orchestrator –––#
def create_scenario_from_bbox(
    *,
    sim_name: str,
    sim_dir: str,
    bbox: str
) -> str:
    """
    1. Validate bbox area
    2. Download & cache OSM
    3. XML validation
    4. netconvert → .net.xml
    5. randomTrips + duarouter → .rou.xml
    6. write .sumocfg
    Returns the path to the generated .sumocfg
    """
    sim_path = Path(sim_dir)
    sim_path.mkdir(parents=True, exist_ok=True)

    # 1) BBOX sanity-check
    south, west, north, east = map(float, bbox.split(","))
    if (north - south) * (east - west) > MAX_BBOX_AREA:
        raise ValueError(f"BBox {bbox} too large (> {MAX_BBOX_AREA}°²)")

    # 2) Download / cache
    cache_name = f"osm_{hashlib.sha1(bbox.encode()).hexdigest()[:8]}.xml"
    osm_path = sim_path / cache_name
    if not osm_path.exists():
        _download_osm(bbox, osm_path)

    # 3) XML validation
    _validate_xml(osm_path)

    # 4) Build network
    net_path = sim_path / f"{sim_name}.net.xml"
    _build_net(osm_path, net_path)

    # 5) Generate routes
    trips_path = sim_path / f"{sim_name}.trips.xml"
    rou_path   = sim_path / f"{sim_name}.rou.xml"
    _build_routes(net_path, trips_path, rou_path)

    # 6) Write SUMO config
    cfg_path = sim_path / f"{sim_name}.sumocfg"
    cfg_text = generate_sumocfg_text(net_path.name, rou_path.name)
    cfg_path.write_text(cfg_text, encoding="utf-8")

    return str(cfg_path)
