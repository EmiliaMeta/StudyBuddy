"""
build_program_db.py — v4
Använder HT2022 (20222) som basterm — fullt utfärdade program.
Kräver: pip install requests
"""

import json, time, os, requests

API_BASE = "https://api.kth.se/api/kopps/v2"
OUT_DIR  = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "programs")
HEADERS  = {"User-Agent": "study-planner-bot/1.0"}

# Prova dessa HT-terminer i ordning (äldst = mest komplett för 5-åriga program)
HT_TERMS = ["20222", "20212", "20232", "20242", "20252"]

PERIOD_MAP = {0: 0, 1: 1, 2: 2, 3: 3}


def get(url):
    for _ in range(3):
        try:
            r = requests.get(url, headers=HEADERS, timeout=15)
            if r.status_code == 404:
                return None
            r.raise_for_status()
            data = r.json()
            if isinstance(data, dict) and "error" in data:
                return None
            return data
        except Exception:
            time.sleep(1)
    return None


def fetch_all_programmes():
    data = get(f"{API_BASE}/programmes/all")
    if not data:
        return []
    return data if isinstance(data, list) else data.get("programmes", [])


def fetch_year(prog_code, study_year):
    """Hämta kurser för ett studieår. Provar HT-terminer tills en fungerar."""
    mandatory_map = {}
    period_map    = {}

    for term in HT_TERMS:
        url  = f"{API_BASE}/programme/{prog_code}.COMMON.{term}.{study_year}"
        data = get(url)
        if not data or not data.get("courses"):
            continue
        for c in data["courses"]:
            code = c.get("code", "").upper()
            if not code:
                continue
            name      = c.get("name", {}).get("sv", "") or c.get("name", {}).get("en", "")
            condition = c.get("condition", {})
            if isinstance(condition, dict):
                condition_str = condition.get("en", "").lower()
            else:
                condition_str = str(condition).lower()
            mandatory = "mandatory" in condition_str
            try:
                hp = float(str(c.get("credits", "7.5")).replace(",", "."))
            except ValueError:
                hp = 7.5
            mandatory_map[code] = {
                "code": code, "name": name,
                "hp": hp, "mandatory": mandatory
            }

        # Hämta period-placering med samma term
        url2 = f"{API_BASE}/academicyearplan/{prog_code}/{term}/{study_year}"
        data2 = get(url2)
        if data2 and isinstance(data2, list):
            for entry in data2:
                code = entry.get("courseCode", "").upper()
                for rnd in entry.get("courseRoundTerms", []):
                    cpp = rnd.get("creditsPerPeriod", [])
                    for idx, val in enumerate(cpp):
                        if val and idx in PERIOD_MAP:
                            period_map[code] = PERIOD_MAP[idx]
                            break
        break  # lyckades, gå vidare

    result = []
    for code, info in mandatory_map.items():
        result.append({
            "code":      code,
            "name":      info["name"],
            "hp":        info["hp"],
            "mandatory": info["mandatory"],
            "year":      min(study_year - 1, 2),
            "period":    period_map.get(code, 0),
        })
    return result


def build_database():
    os.makedirs(OUT_DIR, exist_ok=True)
    programmes = fetch_all_programmes()
    if not programmes:
        print("Kunde inte hämta programlistan.")
        return

    print(f"Hittade {len(programmes)} program.")
    index = []
    saved = 0

    for i, prog in enumerate(programmes, 1):
        code  = prog.get("programmeCode", "").upper()
        name  = prog.get("title", "") or prog.get("titleOtherLanguage", "")
        level = prog.get("owningSchoolCode", "")
        if not code:
            continue

        print(f"[{i}/{len(programmes)}] {code}...", end=" ", flush=True)

        seen = {}
        for yr in range(1, 6):
            for c in fetch_year(code, yr):
                if c["code"] not in seen:
                    seen[c["code"]] = c
            time.sleep(0.1)

        courses = list(seen.values())
        mandatory_count = len([c for c in courses if c["mandatory"]])

        if courses:
            with open(os.path.join(OUT_DIR, f"{code}.json"), "w", encoding="utf-8") as f:
                json.dump({
                    "code": code, "name": name,
                    "level": level, "courses": courses
                }, f, ensure_ascii=False, indent=2)
            print(f"{len(courses)} kurser ({mandatory_count} oblig.)")
            saved += 1
        else:
            print("inga kurser")

        index.append({"code": code, "name": name, "level": level})
        time.sleep(0.15)

    with open(os.path.join(OUT_DIR, "_index.json"), "w", encoding="utf-8") as f:
        json.dump(index, f, ensure_ascii=False, indent=2)

    print(f"\nKlar! {saved}/{len(programmes)} program sparade.")


if __name__ == "__main__":
    build_database()