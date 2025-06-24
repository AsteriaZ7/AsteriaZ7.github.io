import requests
import json
from collections import Counter

# API endpoint and headers
url = "https://dxg-bigdata.ieat.go.th/0acc7d8299f44593a67accb41a2a54a3/epp/vw_master_entrepreneur?format=json&show_total=true"
headers = {
    "accept": "application/json",
    "ieat-dgx-api-key": "sAtWBxjTAqvq4k2ZdxLNbbJMSURhGlh1IFBiI9V1deU",
    "Content-Type": "application/json"
}

# Payload with EstateNameCode = "7"
payload = {
    "start": 0,
    "limit": 100000,
    "EstateNameCode": ["7"]
}

# HR fields to sum
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

# Make the POST request
response = requests.post(url, headers=headers, json=payload)

if response.status_code == 200:
    data = response.json()
    records = data.get("data", [])

    # Industrial Group summary
    group_counts = Counter((r.get("IndustrialGroupDesc") or "ไม่ระบุ").strip() for r in records)

    # HR and capacity totals
    hr_total_count = 0
    capacity_water_production = 0
    capacity_reservoir = 0
    capacity_waste_water_retreat = 0

    for r in records:
        # Sum HR fields
        for field in hr_fields:
            try:
                hr_total_count += int(float(r.get(field) or 0))
            except (ValueError, TypeError):
                pass

        # Sum water-related capacities
        try:
            capacity_water_production += float(r.get("capacity_water_production") or 0)
        except:
            pass

        try:
            capacity_reservoir += float(r.get("capacity_reservoir") or 0)
        except:
            pass

        try:
            capacity_waste_water_retreat += float(r.get("capacity_waste_water_retreat") or 0)
        except:
            pass

    # Print summaries
    print("🔹 นับจำนวนแต่ละกลุ่มอุตสาหกรรม (IndustrialGroupDesc):")
    for group, count in group_counts.items():
        print(f"- {group}: {count} รายการ")
    print(f"รวมทั้งหมด: {sum(group_counts.values())} รายการ\n")

    print("🔹 รวมจำนวนคนงานทั้งหมด:", hr_total_count, "คน")
    print("🔹 ปริมาณการผลิตน้ำรวม:", round(capacity_water_production, 2), "ลบ.ม./วัน")
    print("🔹 ปริมาณน้ำสำรองรวม:", round(capacity_reservoir, 2), "ลบ.ม.")
    print("🔹 ความสามารถในการบำบัดน้ำเสียรวม:", round(capacity_waste_water_retreat, 2), "ลบ.ม./วัน")

else:
    print(f"❌ Request failed with status code {response.status_code}")
    print(response.text)
