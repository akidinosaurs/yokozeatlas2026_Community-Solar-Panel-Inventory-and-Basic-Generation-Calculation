import csv
import json
import math
import sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"

USER_AGENT = "yokozeatlas2026-data-prep/1.0 (GitHub Pages student project)"
YOKOZE_NOMINATIM_URL = (
    "https://nominatim.openstreetmap.org/search?"
    + urlencode(
        {
            "format": "geojson",
            "polygon_geojson": "1",
            "limit": "1",
            "q": "横瀬町, 埼玉県, 日本",
        }
    )
)

OVERPASS_ENDPOINTS = [
    "https://overpass.kumi.systems/api/interpreter",
    "https://overpass-api.de/api/interpreter",
    "https://overpass.openstreetmap.ru/api/interpreter",
]

YOKOZE_RELATION_ID = 1768252
YOKOZE_AREA_ID = 3600000000 + YOKOZE_RELATION_ID

def solar_query_for_bbox(bbox):
    south, west, north, east = bbox
    overpass_bbox = f"{south},{west},{north},{east}"
    return f"""
[out:json][timeout:60];
(
  way["power"="generator"]["generator:source"="solar"]({overpass_bbox});
  way["power"="plant"]["plant:source"="solar"]({overpass_bbox});
  way["building"="solar_panels"]({overpass_bbox});
  way["landuse"="solar_panel"]({overpass_bbox});
  relation["power"="plant"]["plant:source"="solar"]({overpass_bbox});
  relation["power"="generator"]["generator:source"="solar"]({overpass_bbox});
);
out body geom;
"""


def fetch_json(url, *, data=None):
    headers = {
        "User-Agent": USER_AGENT,
        "Accept": "application/json",
    }
    if data is not None:
        body = data.encode("utf-8")
        headers["Content-Type"] = "application/x-www-form-urlencoded; charset=UTF-8"
    else:
        body = None

    req = Request(url, data=body, headers=headers, method="POST" if body else "GET")
    with urlopen(req, timeout=90) as response:
        return json.loads(response.read().decode("utf-8"))


def fetch_overpass(query):
    last_error = None
    body = urlencode({"data": query})
    for endpoint in OVERPASS_ENDPOINTS:
        try:
            return fetch_json(endpoint, data=body)
        except Exception as exc:
            last_error = exc
            print(f"Overpass failed: {endpoint}: {exc}", file=sys.stderr)
    raise RuntimeError(f"All Overpass endpoints failed: {last_error}")


def close_ring(coords):
    if coords and coords[0] != coords[-1]:
        coords = coords + [coords[0]]
    return coords


def polygon_rings(geometry):
    if geometry["type"] == "Polygon":
        return geometry["coordinates"]
    if geometry["type"] == "MultiPolygon":
        return [ring for polygon in geometry["coordinates"] for ring in polygon]
    raise ValueError(f"Unsupported boundary geometry: {geometry['type']}")


def point_in_ring(point, ring):
    x, y = point
    inside = False
    n = len(ring)
    for i in range(n):
        x1, y1 = ring[i]
        x2, y2 = ring[(i + 1) % n]
        crosses = (y1 > y) != (y2 > y)
        if crosses:
            x_intersection = (x2 - x1) * (y - y1) / ((y2 - y1) or 1e-12) + x1
            if x < x_intersection:
                inside = not inside
    return inside


def point_in_polygon(point, geometry):
    if geometry["type"] == "Polygon":
        rings = geometry["coordinates"]
        return point_in_ring(point, rings[0]) and not any(
            point_in_ring(point, hole) for hole in rings[1:]
        )
    if geometry["type"] == "MultiPolygon":
        return any(point_in_polygon(point, {"type": "Polygon", "coordinates": poly}) for poly in geometry["coordinates"])
    return False


def centroid(coords):
    ring = coords[:-1] if coords and coords[0] == coords[-1] else coords
    if not ring:
        return [0, 0]
    return [
        sum(pt[0] for pt in ring) / len(ring),
        sum(pt[1] for pt in ring) / len(ring),
    ]


def area_m2(coords):
    ring = close_ring(coords)
    if len(ring) < 4:
        return 0.0

    lat0 = math.radians(sum(lat for _, lat in ring) / len(ring))
    meters_per_degree_lat = 111_320.0
    meters_per_degree_lon = 111_320.0 * math.cos(lat0)
    projected = [(lon * meters_per_degree_lon, lat * meters_per_degree_lat) for lon, lat in ring]

    area = 0.0
    for i in range(len(projected) - 1):
        x1, y1 = projected[i]
        x2, y2 = projected[i + 1]
        area += x1 * y2 - x2 * y1
    return abs(area) / 2


def matching_solar_tags(tags):
    matches = []
    if tags.get("power") == "generator" and tags.get("generator:source") == "solar":
        matches.append("power=generator + generator:source=solar")
    if tags.get("power") == "plant" and tags.get("plant:source") == "solar":
        matches.append("power=plant + plant:source=solar")
    if tags.get("building") == "solar_panels":
        matches.append("building=solar_panels")
    if tags.get("landuse") == "solar_panel":
        matches.append("landuse=solar_panel")
    return matches


def format_tags(tags):
    return "; ".join(f"{key}={value}" for key, value in sorted(tags.items()))


def way_feature(element, boundary_geometry, generated_at):
    coords = close_ring([[pt["lon"], pt["lat"]] for pt in element.get("geometry", [])])
    if len(coords) < 4:
        return None

    center = centroid(coords)
    if not point_in_polygon(center, boundary_geometry):
        return None

    tags = element.get("tags") or {}
    area = round(area_m2(coords), 2)
    capacity_kw = round(area * 0.18, 2)
    annual_kwh = round(capacity_kw * 1050, 2)
    peak_kw = round(capacity_kw * 0.75, 2)
    osm_id = f"way/{element['id']}"
    matches = matching_solar_tags(tags)

    return {
        "type": "Feature",
        "id": osm_id,
        "geometry": {"type": "Polygon", "coordinates": [coords]},
        "properties": {
            "id": osm_id,
            "osm_type": "way",
            "osm_id": element["id"],
            "municipality": "横瀬町",
            "source_dataset": "OpenStreetMap via Overpass API",
            "boundary_filter": f"OSM administrative relation {YOKOZE_RELATION_ID} / area {YOKOZE_AREA_ID}",
            "generated_at": generated_at,
            "matched_query_tags": " / ".join(matches) or "検索条件タグ不明",
            "osm_tags": format_tags(tags) or "タグなし",
            "calc_area_m2": area,
            "calc_capacity_kw": capacity_kw,
            "calc_annual_kwh": annual_kwh,
            "calc_peak_kw": peak_kw,
            "capacity_formula": "area_m2 * 0.18",
            "annual_generation_formula": "capacity_kw * 1050",
            "peak_output_formula": "capacity_kw * 0.75",
        },
    }


def write_json(path, payload):
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_csv(path, features):
    columns = [
        "id",
        "osm_type",
        "osm_id",
        "municipality",
        "calc_area_m2",
        "calc_capacity_kw",
        "calc_annual_kwh",
        "calc_peak_kw",
        "matched_query_tags",
        "osm_tags",
        "generated_at",
    ]
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=columns)
        writer.writeheader()
        for feature in features:
            props = feature["properties"]
            writer.writerow({column: props.get(column, "") for column in columns})


def write_tag_summary(path, features, generated_at):
    counts = {}
    for feature in features:
        for match in feature["properties"]["matched_query_tags"].split(" / "):
            counts[match] = counts.get(match, 0) + 1

    columns = ["matched_query_tags", "feature_count", "generated_at"]
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=columns)
        writer.writeheader()
        for tag, count in sorted(counts.items()):
            writer.writerow(
                {
                    "matched_query_tags": tag,
                    "feature_count": count,
                    "generated_at": generated_at,
                }
            )


def main():
    DATA_DIR.mkdir(exist_ok=True)
    generated_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat()

    boundary_response = fetch_json(YOKOZE_NOMINATIM_URL)
    if not boundary_response.get("features"):
        raise RuntimeError("Yokoze boundary was not found from Nominatim.")

    boundary_source = boundary_response["features"][0]
    boundary_geometry = boundary_source["geometry"]
    bbox_raw = boundary_source.get("bbox") or boundary_source["properties"].get("boundingbox")
    if not bbox_raw or len(bbox_raw) != 4:
        raise RuntimeError("Yokoze boundary bbox was not found from Nominatim.")
    if boundary_source.get("bbox"):
        west, south, east, north = [float(value) for value in bbox_raw]
    else:
        south, north, west, east = [float(value) for value in bbox_raw]
    query_bbox = [south, west, north, east]
    boundary_feature = {
        "type": "Feature",
        "geometry": boundary_geometry,
        "properties": {
            "name": "横瀬町",
            "name_en": "Yokoze, Saitama, Japan",
            "osm_type": boundary_source["properties"].get("osm_type"),
            "osm_id": boundary_source["properties"].get("osm_id"),
            "osm_relation_id": YOKOZE_RELATION_ID,
            "source_dataset": "OpenStreetMap via Nominatim",
            "generated_at": generated_at,
        },
    }

    overpass_data = fetch_overpass(solar_query_for_bbox(query_bbox))
    features = []
    seen = set()
    for element in overpass_data.get("elements", []):
        if element.get("type") != "way":
            continue
        feature = way_feature(element, boundary_geometry, generated_at)
        if not feature:
            continue
        if feature["id"] in seen:
            continue
        seen.add(feature["id"])
        features.append(feature)

    features.sort(key=lambda f: f["properties"]["id"])

    total_area = round(sum(f["properties"]["calc_area_m2"] for f in features), 2)
    total_capacity = round(sum(f["properties"]["calc_capacity_kw"] for f in features), 2)
    total_annual = round(sum(f["properties"]["calc_annual_kwh"] for f in features), 2)

    main_geojson = {
        "type": "FeatureCollection",
        "name": "yokoze_solar_panels",
        "metadata": {
            "title": "横瀬町 太陽光設備ポリゴン台帳",
            "municipality": "横瀬町",
            "main_data": True,
            "generated_at": generated_at,
            "source": "OpenStreetMap via Overpass API",
            "boundary_source": "OpenStreetMap administrative boundary via Nominatim",
            "boundary_relation_id": YOKOZE_RELATION_ID,
            "query_tags": [
                "power=generator + generator:source=solar",
                "power=plant + plant:source=solar",
                "building=solar_panels",
                "landuse=solar_panel",
            ],
            "feature_count": len(features),
            "total_area_m2": total_area,
            "total_capacity_kw": total_capacity,
            "total_annual_kwh": total_annual,
            "notes": [
                "OSMに登録された閉じたwayポリゴンのみを対象にしています。",
                "横瀬町行政界ポリゴン内に重心があるポリゴンを採用しています。",
                "計算値は簡易推計であり設備仕様や稼働状況を反映しません。",
            ],
        },
        "features": features,
    }

    boundary_geojson = {
        "type": "FeatureCollection",
        "name": "yokoze_boundary",
        "metadata": {
            "title": "横瀬町行政界",
            "generated_at": generated_at,
            "source": "OpenStreetMap via Nominatim",
            "osm_relation_id": YOKOZE_RELATION_ID,
        },
        "features": [boundary_feature],
    }

    write_json(DATA_DIR / "yokoze_solar_panels.geojson", main_geojson)
    write_json(DATA_DIR / "yokoze_boundary.geojson", boundary_geojson)
    write_csv(DATA_DIR / "yokoze_solar_panels.csv", features)
    write_tag_summary(DATA_DIR / "yokoze_solar_tag_summary.csv", features, generated_at)

    print(
        json.dumps(
            {
                "generated_at": generated_at,
                "feature_count": len(features),
                "total_area_m2": total_area,
                "total_capacity_kw": total_capacity,
                "total_annual_kwh": total_annual,
                "files": [
                    "data/yokoze_solar_panels.geojson",
                    "data/yokoze_boundary.geojson",
                    "data/yokoze_solar_panels.csv",
                    "data/yokoze_solar_tag_summary.csv",
                ],
            },
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
