#!/usr/bin/env python3
"""Draft a weekly schedule from a coverage template and staff availability,
then cost it against a labor % target. DRAFT ONLY - not legal advice.

Usage:
  python3 labor_draft.py --sample --forecast 18000 --target 28 [--location "City, ST"]
  python3 labor_draft.py --staff staff.csv --coverage coverage.csv --forecast 18000 --target 28 \
      --week-start 2026-10-05 [--location "Austin, TX"] [--school-week yes|no|auto] [--out DIR]
  python3 labor_draft.py --staff staff.csv --schedule my_schedule.csv --forecast 18000 --target 28
      (audit an existing schedule: columns employee_id, day, start, end[, role])

Formulas:
  labor budget     = forecast sales x target % / 100
  shift hours      = end - start (paid; unpaid meal breaks are NOT deducted)
  regular pay      = min(weekly hours, 40) x wage
  overtime pay     = max(weekly hours - 40, 0) x wage x 1.5     (FLSA weekly OT)
  labor $          = sum(regular pay + overtime pay) over employees
  labor %          = labor $ / forecast sales x 100
Hourly wages only: no payroll tax, benefits, salaried managers or tips.

Assignment (draft mode): shifts in day/start order; candidates must match role,
be available that day and window, not already work that day, and stay within
their max_hours. Prefer whoever stays <= 40 h with the fewest hours so far;
use OT only when nobody else fits (then FLAG). Federal rules for 14-15 year
olds are applied as hard limits (not during school hours - assumed 7:00-15:00 on
school days -, 7am-7pm, 3 h school day, 18 h school week, 8 h non-school day,
40 h non-school week); state rules are NOT checked. A shift whose end is at
or before its start runs past midnight.
"""
import argparse
import csv
import datetime as dt
import sys
from decimal import Decimal as D, ROUND_HALF_UP
from pathlib import Path

SAMPLES = Path(__file__).resolve().parents[3] / "samples"
SCHOOL_START, SCHOOL_END = 7, 15  # assumed school hours for the 14-15 check
DAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
WEIGHTS = [D("0.11"), D("0.11"), D("0.13"), D("0.14"), D("0.18"), D("0.19"), D("0.14")]
FAIR_WORKWEEK = {
    "brooklyn": "New York City Fair Workweek (fast food and retail; fast food coverage keyed to 30+ locations nationally)",
    "queens": "New York City Fair Workweek (fast food and retail; fast food coverage keyed to 30+ locations nationally)",
    "bronx": "New York City Fair Workweek (fast food and retail; fast food coverage keyed to 30+ locations nationally)",
    "staten island": "New York City Fair Workweek (fast food and retail; fast food coverage keyed to 30+ locations nationally)",
    "manhattan": "New York City Fair Workweek (fast food and retail; fast food coverage keyed to 30+ locations nationally)",
    "new york": "New York City Fair Workweek (fast food and retail; fast food coverage keyed to 30+ locations nationally)",
    "nyc": "New York City Fair Workweek (fast food and retail; fast food coverage keyed to 30+ locations nationally)",
    "san francisco": "San Francisco Formula Retail Employee Rights Ordinances (formula retail / chains)",
    "berkeley": "Berkeley Fair Workweek (large retail and food service employers)",
    "emeryville": "Emeryville Fair Workweek (large retail and fast food employers)",
    "los angeles": "Los Angeles city / unincorporated LA County Fair Workweek (large retail employers)",
    "chicago": "Chicago Fair Workweek (restaurants: 250+ employees and 30+ locations)",
    "evanston": "Evanston Fair Workweek (large employers incl. food service)",
    "seattle": "Seattle Secure Scheduling (food service 500+ employees worldwide; full service also 40+ locations)",
    "philadelphia": "Philadelphia Fair Workweek (retail/food/hospitality 250+ employees and 30+ locations)",
    "oregon": "Oregon predictive scheduling (statewide; 500+ employees worldwide)",
}


def hf(x):
    return f"{x.quantize(D('0.01'))}"


def q2(x):
    return x.quantize(D("0.01"), rounding=ROUND_HALF_UP)


def read(path):
    with open(path, newline="", encoding="utf-8-sig") as f:
        return [{k.strip(): (v or "").strip() for k, v in r.items()} for r in csv.DictReader(f)
                if any((v or "").strip() for v in r.values())]


def hm(s):
    h, m = s.split(":")
    return D(int(h)) + D(int(m)) / D(60)


def span(start, end):
    """Start and end in hours; an end at or before the start means the shift ends after midnight."""
    s, e = hm(start), hm(end)
    return s, (e + 24 if e <= s else e)


def school_in_session(date, mode):
    if mode in ("yes", "no"):
        return mode == "yes"
    # auto: approx US school year = day after Labor Day through May 31
    labor_day = dt.date(date.year, 9, 1)
    while labor_day.weekday() != 0:
        labor_day += dt.timedelta(days=1)
    return date > labor_day or date.month <= 5


def minor_ok(emp, day_idx, start, end, hours, week, school_week):
    """Federal FLSA child labor limits for ages 14-15. Returns (ok, reason)."""
    if emp["age"] >= 16:
        return True, ""
    if emp["age"] < 14:
        return False, "under 14: not scheduled"
    school_day = school_week and day_idx < 5
    latest = D(19) if school_week else D(21)  # 9pm only June 1 - Labor Day
    why = []
    if school_day and start < SCHOOL_END and end > SCHOOL_START:
        why.append(f"no work during school hours on a school day (assumed {SCHOOL_START}:00-{SCHOOL_END}:00; confirm)")
    if start < 7 or end > latest:
        why.append(f"must work between 7:00 and {int(latest)}:00")
    if hours > (3 if school_day else 8):
        why.append(f"max {3 if school_day else 8} h on a {'school' if school_day else 'non-school'} day")
    if week + hours > (18 if school_week else 40):
        why.append(f"max {18 if school_week else 40} h in a {'school' if school_week else 'non-school'} week")
    return (False, "14-15: " + "; ".join(why)) if why else (True, "")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--sample", action="store_true")
    ap.add_argument("--staff")
    ap.add_argument("--coverage")
    ap.add_argument("--schedule", help="audit an existing schedule instead of drafting")
    ap.add_argument("--forecast", type=D, required=True, help="forecast sales for the week, $")
    ap.add_argument("--target", type=D, required=True, help="target labor %% of sales")
    ap.add_argument("--week-start", default="2026-10-05", help="Monday date, YYYY-MM-DD")
    ap.add_argument("--location", default="", help='"City, ST" for predictive-scheduling check')
    ap.add_argument("--school-week", choices=["yes", "no", "auto"], default="auto")
    ap.add_argument("--out", default="restaurant-ops-output")
    a = ap.parse_args()
    staff_p = a.staff or (SAMPLES / "staff.csv" if a.sample else None)
    cov_p = a.coverage or (SAMPLES / "coverage.csv" if a.sample and not a.schedule else None)
    if not staff_p or not (cov_p or a.schedule):
        ap.error("give --staff and --coverage (or --schedule), or --sample")

    monday = dt.date.fromisoformat(a.week_start)
    school = school_in_session(monday, a.school_week)
    staff = {}
    for r in read(staff_p):
        staff[r["employee_id"]] = {
            "id": r["employee_id"], "name": r["name"], "role": r["role"].lower(), "wage": D(r["wage"].replace("$", "").replace(",", "")),
            "age": int(r.get("age") or 99), "days": {d.strip()[:3].title() for d in r.get("days_available", "").split(";") if d.strip()},
            "a0": hm(r.get("avail_start") or "00:00"), "a1": hm(r.get("avail_end") or "23:59"),
            "max": D(r.get("max_hours") or "40"), "hours": D(0), "worked": set()}

    shifts, unfilled, notes = [], [], []
    if a.schedule:
        for r in read(a.schedule):
            di = DAYS.index(r["day"][:3].title())
            s, e = span(r["start"], r["end"])
            emp = staff.get(r["employee_id"])
            if not emp:
                notes.append(f"schedule row for unknown employee {r['employee_id']}")
                continue
            ok, why = minor_ok(emp, di, s, e, e - s, emp["hours"], school)
            if not ok:
                notes.append(f"MINOR RULE: {emp['id']} {DAYS[di]} {r['start']}-{r['end']}: {why}")
            emp["hours"] += e - s
            shifts.append((di, r.get("role", emp["role"]), r["start"], r["end"], e - s, emp))
    else:
        cov = sorted(read(cov_p), key=lambda r: (DAYS.index(r["day"][:3].title()), hm(r["start"])))
        for r in cov:
            di = DAYS.index(r["day"][:3].title())
            s, e = span(r["start"], r["end"])
            h = e - s
            for _ in range(int(r.get("headcount") or 1)):
                cands, blocked = [], []
                for emp in staff.values():
                    if emp["role"] != r["role"].lower() or DAYS[di] not in emp["days"] or di in emp["worked"]:
                        continue
                    if s < emp["a0"] or e > emp["a1"]:
                        continue
                    if emp["hours"] + h > emp["max"]:
                        blocked.append(f"{emp['id']} (would pass their max_hours {emp['max']})")
                        continue
                    ok, why = minor_ok(emp, di, s, e, h, emp["hours"], school)
                    if not ok:
                        blocked.append(f"{emp['id']} ({why})")
                        continue
                    cands.append(emp)
                no_ot = [c for c in cands if c["hours"] + h <= 40]
                pool = no_ot or cands
                if not pool:
                    unfilled.append((di, r["role"], r["start"], r["end"], h, blocked))
                    continue
                emp = min(pool, key=lambda c: (c["hours"], c["wage"], c["id"]))
                emp["hours"] += h
                emp["worked"].add(di)
                shifts.append((di, r["role"], r["start"], r["end"], h, emp))

    budget = a.forecast * a.target / D(100)
    emp_rows, total, flags = [], D(0), []
    for emp in staff.values():
        h = emp["hours"]
        reg, ot = min(h, D(40)), max(h - D(40), D(0))
        pay = reg * emp["wage"] + ot * emp["wage"] * D("1.5")
        total += pay
        f = []
        if ot > 0:
            f.append(f"OVERTIME {hf(ot)} h over 40 (+${q2(ot * emp['wage'] * D('0.5'))} premium)")
        if h > 0 and emp["age"] < 16:
            f.append("MINOR 14-15: federal hour/time limits applied; check state law and work permit; no cooking/baking/hazardous equipment except as allowed")
        elif h > 0 and emp["age"] < 18:
            f.append("MINOR 16-17: no federal hour limits but state limits may apply; no hazardous equipment (e.g. meat slicers, power mixers)")
        if f:
            flags.append(f"{emp['id']} {emp['name'].split()[0]}: " + "; ".join(f))
        if h > 0 or f:
            emp_rows.append([emp["id"], emp["name"], emp["role"], emp["wage"], hf(h), hf(reg), hf(ot), q2(pay), " | ".join(f)])
    pct = total / a.forecast * D(100)

    loc = a.location.lower()
    city, _, state = loc.partition(",")
    city, state = city.strip(), state.strip()
    hits = sorted({v for k, v in FAIR_WORKWEEK.items() if k in city or k == state}) if loc else []
    if state in ("or", "oregon"):
        hits.append(FAIR_WORKWEEK["oregon"])
    if state in ("ny", "new york") and not hits:
        hits.append("New York State: NYC (all five boroughs) has a Fair Workweek law; confirm whether this address is in NYC")
    if not loc:
        fw = "LOCATION NOT GIVEN: ask which city/state; predictive scheduling (Fair Workweek) laws may apply."
    elif hits:
        fw = ("PREDICTIVE SCHEDULING MAY APPLY: " + "; ".join(hits)
              + ". Coverage depends on employer size/locations; if covered, post 14 days ahead and track change premiums.")
    else:
        fw = f"{a.location}: not on this plugin's city list (NYC, SF, Berkeley, Emeryville, LA, Chicago, Evanston, Seattle, Philadelphia, Oregon). Lists change; confirm locally."

    print("DRAFT SCHEDULE - not legal advice. A manager must review before posting.")
    print(f"Week of {monday} | school week assumed: {'yes' if school else 'no'} | forecast ${q2(a.forecast)} | "
          f"target {a.target}% -> labor budget ${q2(budget)}")
    print(f"Scheduled labor ${q2(total)} = {q2(pct)}% of forecast (budget ${q2(budget)}, "
          f"{'over' if total > budget else 'under'} by ${q2(abs(total - budget))})")
    print(f"Total scheduled hours {hf(sum((s[4] for s in shifts), D(0)))}; shifts {len(shifts)}; unfilled {len(unfilled)}")
    print("\nFLAGS")
    for f in flags:
        print("  " + f)
    for u in unfilled:
        print(f"  UNFILLED {DAYS[u[0]]} {u[1]} {u[2]}-{u[3]}" + (f" (blocked: {'; '.join(u[5])})" if u[5] else " (no available staff)"))
    for n in notes:
        print("  " + n)
    long_shifts = sum(1 for s in shifts if s[4] >= 5)
    print(f"  MEAL/REST BREAKS: {long_shifts} shifts are 5 h or longer; break rules vary by state (e.g. CA); hours above are paid, no break deducted.")
    print("  " + fw)

    print("\nBY DAY")
    for di, d in enumerate(DAYS):
        day_sh = [s for s in shifts if s[0] == di]
        hrs = sum((s[4] for s in day_sh), D(0))
        cost = sum((s[4] * s[5]["wage"] for s in day_sh), D(0))
        fc = a.forecast * WEIGHTS[di]
        print(f"  {d} {monday + dt.timedelta(days=di)}: {hf(D(hrs))} h, ${q2(cost)} straight-time, forecast ${q2(fc)} "
              f"({q2(cost / fc * 100)}%)")

    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    with open(out / "schedule_draft.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["DRAFT - not legal advice; manager review required before posting"])
        w.writerow(["day", "date", "role", "start", "end", "hours", "employee_id", "employee"])
        for s in sorted(shifts, key=lambda s: (s[0], s[2], s[1])):
            w.writerow([DAYS[s[0]], monday + dt.timedelta(days=s[0]), s[1], s[2], s[3], hf(s[4]), s[5]["id"], s[5]["name"]])
        for u in unfilled:
            w.writerow([DAYS[u[0]], monday + dt.timedelta(days=u[0]), u[1], u[2], u[3], hf(u[4]), "", "UNFILLED"])
    with open(out / "labor_summary.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["DRAFT - not legal advice"])
        w.writerow(["employee_id", "employee", "role", "wage", "hours", "regular_hours", "ot_hours", "pay", "flags"])
        w.writerows(emp_rows)
        w.writerow([])
        w.writerow(["TOTAL", "", "", "", hf(sum((s[4] for s in shifts), D(0))), "", "", q2(total), ""])
        w.writerow(["forecast_sales", q2(a.forecast)])
        w.writerow(["target_pct", a.target])
        w.writerow(["labor_budget", q2(budget)])
        w.writerow(["labor_pct", q2(pct)])
        w.writerow(["predictive_scheduling", fw])
    print(f"\nWrote {out / 'schedule_draft.csv'} and {out / 'labor_summary.csv'}")


if __name__ == "__main__":
    main()
