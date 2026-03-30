"""
build_kth_db.py
---------------
Hämtar alla KTH-kurser via KOPPS API och sparar till data/kth_courses.json.
Kör en gång: python build_kth_db.py

Kräver: pip install requests
"""

import json
import time
import os
import requests

API_BASE = "https://api.kth.se/api/kopps/v2/courses"
OUT      = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "kth_courses.json")

HEADERS = {"User-Agent": "study-planner-bot/1.0 (educational use)"}

# Alla möjliga tvåbokstavsprefixer som KTH använder
PREFIXES = [
    "AB","AD","AF","AG","AH","AK","AL","AN","AO","AP",
    "BB","BF","BJ","BK","BL","BM","BT","CB","CF","CG","CH","CK","CM","CN","CS","CZ",
    "DA","DB","DD","DE","DG","DH","DM","DO","DS","DT","DV","EF","EH","EI","EK","EL",
    "EM","EN","EP","EQ","ES","EY","FA","FB","FE","FF","FH","FI","FL","FM","FO","FP",
    "FQ","FS","FT","FY","GE","GF","GG","GH","HL","HM","HN","HO","HP","HS","HT","HU",
    "ID","IE","IF","II","IK","IL","IM","IN","IO","IP","IS","IT","IV","IX",
    "JH","JN","KD","KE","KF","KH","KI","KL","KN","KO","KP","KS","KT","KU","KV","KW",
    "LA","LB","LC","LH","LL","LM","LN","LO","LP","LS","LT","ME","MF","MG","MH","MI",
    "MJ","MK","ML","MM","MN","MO","MP","MQ","MR","MT","MV","MY",
    "NA","NE","NH","NP","NS","NX","OF","OK","OM","PA","PB","PF","PH","PK","PO","PS",
    "QA","QB","RF","RK","RM","RN","SA","SB","SC","SD","SE","SF","SG","SH","SH","SI",
    "SJ","SK","SL","SM","SN","SO","SP","SQ","SR","ST","SU","SV","SW","SX","SY","SZ",
    "TA","TB","TC","TD","TE","TF","TG","TH","TI","TJ","TK","TL","TM","TN","TO","TP",
    "TQ","TR","TS","TT","TU","TV","TW","TX","TY","TZ","UB","VM","VT",
]


def fetch_courses_for_prefix(prefix):
    url = f"{API_BASE}/{prefix}.json"
    try:
        r = requests.get(url, headers=HEADERS, timeout=10)
        if r.status_code == 404:
            return []
        r.raise_for_status()
        data = r.json()
        return data.get("courses", [])
    except Exception as e:
        print(f"  Fel för {prefix}: {e}")
        return []


def build_database():
    os.makedirs("data", exist_ok=True)

    courses = {}
    total_prefixes = len(PREFIXES)

    for i, prefix in enumerate(PREFIXES, 1):
        print(f"[{i}/{total_prefixes}] Hämtar {prefix}...", end=" ", flush=True)
        results = fetch_courses_for_prefix(prefix)

        for c in results:
            code = c.get("code", "").upper()
            title = c.get("title", "") or c.get("titleOther", "")
            credits = c.get("credits")

            if code and title and credits:
                try:
                    hp = float(str(credits).replace(",", "."))
                except ValueError:
                    continue
                courses[code] = {"code": code, "name": title, "hp": hp}

        print(f"{len(results)} kurser")
        time.sleep(0.15)

    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(courses, f, ensure_ascii=False, indent=2)

    print(f"\nKlar! {len(courses)} kurser sparade till {OUT}")


if __name__ == "__main__":
    build_database()