import os
import json
from collections import Counter, defaultdict
from flask import Flask, render_template, abort
import requests

app = Flask(__name__)

# Configuration
API_URL = "https://dxg-bigdata.ieat.go.th/0acc7d8299f44593a67accb41a2a54a3/epp/vw_master_entrepreneur?format=json&show_total=true"
API_KEY = os.getenv("IEAT_API_KEY", "sAtWBxjTAqvq4k2ZdxLNbbJMSURhGlh1IFBiI9V1deU")
HEADERS = {
    "accept": "application/json",
    "ieat-dgx-api-key": API_KEY,
    "Content-Type": "application/json"
}
PAYLOAD = {"start": 0, "limit": 100000}

# Load distance data
DISTANCE_DATA = {}
try:
    with open("Estate.json", "r", encoding="utf-8") as f:
        raw_data = json.load(f)
        DISTANCE_DATA = {
            str(item["EstateNameCode"]): {
                "province_th": item.get("province_th"),
                "ieatindustrial_en": item.get("ieatindustrial_en"),
                "ieatindustrial_abbrv_eng": item.get("ieatindustrial_abbrv_eng"),
                "ieatindustrial_abbrv_th": item.get("ieatindustrial_abbrv_th"),
                "distance_airport": item.get("distance_airport"),
                "distance_mtpport": item.get("distance_mtpport"),
                "distance_railwaysta": item.get("distance_railwaysta"),
                "size_total": item.get("size_total"),
                "size_giz": item.get("size_giz"),
                "size_ifz": item.get("size_ifz"),
                "size_cm": item.get("size_cm"),
                "capacity_water_production": item.get("capacity_water_production"),
                "capacity_reservoir": item.get("capacity_reservoir"),
                "capacity_waste_water_retreat": item.get("capacity_waste_water_retreat"),
                "latitute": item.get("latitute"),
                "longitute": item.get("longitute")
                
                
            }
            for item in raw_data if "EstateNameCode" in item
        }
except Exception as e:
    app.logger.warning(f"Could not load distance data - {e}")

# Load EIA and industry data
EIA_REPORTS = []
TARGET_INDUSTRIES = defaultdict(list)
PROHIBIT_INDUSTRIES = defaultdict(list)

try:
    with open("EIA_REPORT.json", "r", encoding="utf-8") as f:
        EIA_REPORTS = json.load(f)

    with open("target.json", "r", encoding="utf-8") as f:
        for t in json.load(f):
            if (t.get("record_status") or "").strip().upper() == "N":
                rpt_id = str(t.get("rpt_id", "")).strip()
                if rpt_id:
                    TARGET_INDUSTRIES[rpt_id].append(t["t_industry_text"])

    with open("prohibit.json", "r", encoding="utf-8") as f:
        for p in json.load(f):
            if (p.get("record_status") or "").strip().upper() == "N":
                rpt_id = str(p.get("rpt_id", "")).strip()
                if rpt_id:
                    PROHIBIT_INDUSTRIES[rpt_id].append(p["p_industry_text"])

except Exception as e:
    app.logger.warning(f"Could not load EIA or industry data - {e}")

# Fetch data from API
def fetch_estate_data(estate_code=None):
    try:
        payload = {
            "start": 0,
            "limit": 100000
        }
        if estate_code:
            payload["EstateNameCode"] = [str(estate_code)]

        response = requests.post(API_URL, headers=HEADERS, json=payload, timeout=5)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        app.logger.error(f"API request failed: {e}")
        abort(500, description="Failed to fetch data from API")

@app.route("/")
def index():
    data = fetch_estate_data()
    records = data.get("data", [])
    estates_map = {}
    
    for item in records:
        code = item.get("EstateNameCode")
        name = item.get("EstateName")
        if not code or not name:
            continue

        if code not in estates_map:
            dist_info = DISTANCE_DATA.get(str(code), {})
            estates_map[code] = {
                "code": code,
                "name": name,
                "province": dist_info.get("province_th", "ไม่ระบุจังหวัด"),
                "name_en": dist_info.get("ieatindustrial_en", "ไม่ระบุ"),
                "abbrv_eng": dist_info.get("ieatindustrial_abbrv_eng", "ไม่ระบุ"),
                "abbrv_th": dist_info.get("ieatindustrial_abbrv_th", "ไม่ระบุ"),
            }

    sorted_estates = sorted(estates_map.values(), key=lambda item: int(item["code"]) if item["code"].isdigit() else item["code"])
    return render_template("index.html", estates=sorted_estates)

@app.route("/estate/<code>")
def estate_detail(code):
    data = fetch_estate_data(code)
    records = data.get("data", [])
    estate_records = records  # No need to filter again

    estate_records = [r for r in records if str(r.get("EstateNameCode")) == str(code)]
    if not estate_records:
        abort(404, description="Estate not found")
        
    hr_fields = [
        "HrExecuiveTechnicianSum",
        "HrMaleWorkersSkillSum",
        "HrFemaleWorkersSkillSum",
        "HrMaleWorkersUnskillSum",
        "HrFemaleWorkersUnskillSum",
        "HrForeignTechnicianSum",
        "HrForeignSkillTechnicianSum",
        "HrForeignExpertSum"
    ]
    
    summary = {field: 0 for field in hr_fields}
    for rec in estate_records:
        for field in hr_fields:
            try:
                summary[field] += int(float(rec.get(field) or 0))
            except (ValueError, TypeError):
                pass
    
    hr_total_count = int(sum(summary.values()))

    group_counts = Counter()
    for rec in estate_records:
        group = (rec.get("IndustrialGroupDesc") or "ไม่ระบุ").strip()
        group_counts[group] += 1

    estate_name = estate_records[0].get("EstateName", "Unknown")
    industrial_group_summary = dict(group_counts)
    group_total_count = sum(group_counts.values())

    distance_info = DISTANCE_DATA.get(code, {
        "province_th": "ไม่ระบุจังหวัด",
        "distance_airport": "ไม่พบข้อมูล",
        "distance_mtpport": "ไม่พบข้อมูล",
        "distance_railwaysta": "ไม่พบข้อมูล",
        "size_total": "ไม่พบข้อมูล",
        "size_giz": "ไม่พบข้อมูล",
        "size_ifz": "ไม่พบข้อมูล",
        "size_cm": "ไม่พบข้อมูล",
        "ieatindustrial_en": "ไม่พบข้อมูล",
        "capacity_water_production": "ไม่พบข้อมูล",
        "capacity_reservoir": "ไม่พบข้อมูล",
        "capacity_waste_water_retreat": "ไม่พบข้อมูล"
    })

    eia_entries = [r for r in EIA_REPORTS if str(r.get("estate_id")) == code]
    eia_entries.sort(key=lambda x: x.get("last_upd_dtm", ""), reverse=True)

    eia_info = []
    for e in eia_entries:
        rpt_id = str(e.get("rpt_id", "")).strip()
        if not rpt_id:
            continue
        eia_info.append({
            "rpt_id": rpt_id,
            "project_name": e.get("rpt_prj_name", "ไม่ระบุโครงการ"),
            "last_upd_dtm": e.get("last_upd_dtm") if e.get("last_upd_dtm") not in ["", "NULL", None] else "ไม่พบข้อมูล",
            "target_industry": TARGET_INDUSTRIES.get(rpt_id, ["ไม่ระบุ"]),
            "prohibited_industry": PROHIBIT_INDUSTRIES.get(rpt_id, ["ไม่ระบุ"])
            
        })

    return render_template(
        "detail_page.html",
        estate_name=estate_name,
        hr_summary=summary,
        hr_total_count=hr_total_count,
        industrial_group_summary=industrial_group_summary,
        distance_airport=distance_info.get("distance_airport"),
        distance_mtpport=distance_info.get("distance_mtpport"),
        distance_railwaysta=distance_info.get("distance_railwaysta"),
        size_total=distance_info.get("size_total"),
        province_th=distance_info.get("province_th"),
        size_giz=distance_info.get("size_giz"),
        size_ifz=distance_info.get("size_ifz"),
        size_cm=distance_info.get("size_cm"),
        ieatindustrial_en=distance_info.get("ieatindustrial_en"),
        capacity_water_production=distance_info.get("capacity_water_production"),
        capacity_reservoir=distance_info.get("capacity_reservoir"),
        capacity_waste_water_retreat=distance_info.get("capacity_waste_water_retreat"),
        group_total_count=group_total_count,
        eia_info=eia_info,
        lat = distance_info.get("latitute"),
        lng = distance_info.get("longitute")
        
    )

if __name__ == "__main__":
    app.run(debug=True)
