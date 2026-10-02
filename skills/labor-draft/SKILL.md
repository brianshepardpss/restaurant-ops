---
name: labor-draft
description: Use when a restaurant manager wants a draft weekly schedule or labor plan against a labor % target, or says "draft next week's schedule", "how many hours can I schedule on $18k in sales", "build the schedule at 28% labor", "check my schedule for overtime", or "are we over on labor". Takes staff (roles, wages, availability, ages) and shifts needed, or an existing schedule; returns a costed draft with overtime, minor and predictive-scheduling flags as CSV. Draft only, not legal advice.
---

# Labor draft against a labor % target

All hours, dollars and percentages come from `scripts/labor_draft.py` (this
skill's directory). Never total hours or compute labor % yourself.

## 1. Inputs

- Demo: `--sample` (fictional staff and coverage, week of 2026-10-05).
- Forecast sales for the week and target labor %: ask if not given. Do not
  invent a forecast; offer to use last year's or last month's same week if
  the user has it.
- Staff CSV like `../../samples/staff.csv`: employee_id, name, role, wage,
  age (only needed if under 18; otherwise leave blank), days_available,
  avail_start, avail_end, max_hours.
- Either shifts needed (`coverage.csv`: day, role, start, end, headcount)
  to draft, or an existing schedule (employee_id, day, start, end, role) to
  audit with `--schedule`.
- Location (city, state). Ask every time it is not known: predictive
  scheduling (Fair Workweek) laws apply in some cities and Oregon.
- Week start date (Monday) and whether school is in session if any staff
  are 14-15 (`--school-week yes|no`; default guesses from the date).

## 2. Run

```
python3 <this skill dir>/scripts/labor_draft.py --staff staff.csv --coverage coverage.csv \
  --forecast 18000 --target 28 --week-start 2026-10-05 --location "City, ST" --out restaurant-ops-output
```

## 3. Report

Start with: "Draft schedule - not legal advice; review before posting."

```
Forecast $F | target T% | labor budget $B
Scheduled $L = P% of forecast (<over/under> by $V) | <h> hours | <n> unfilled shifts

Flags
- Overtime: ...
- Minors: ...
- Unfilled: ...
- Predictive scheduling: ...
- Breaks: ...

By day: (table from the script)
```

Then up to 3 suggestions to close a gap (trim a slow-day shift, move a
shift to a lower-wage qualified person, fill unfilled shifts). Re-run the
script for any change the user accepts; never adjust totals by hand.

Use first names only in chat. Files: `schedule_draft.csv`,
`labor_summary.csv`.

## Rules

- Overtime is flagged at > 40 h per workweek (federal). Some states (e.g.
  CA) also have daily overtime; say so if the location is in such a state,
  without computing it.
- 14-15 year olds: the script applies federal limits as hard limits. State
  rules can be stricter and are not checked. 16-17: no federal hour limits,
  but hazardous-equipment rules and state limits apply. Always tell the
  user to confirm with their state labor department.
- Predictive scheduling: if the script says it may apply, explain that
  coverage depends on employer size and location count, and that the
  user should check the ordinance. Never state that the user is or is not
  covered.
- Do not give advice on tip pools, tip credits, pay rates, classification
  (exempt vs non-exempt) or terminations; refer to a payroll provider or
  employment lawyer.
- Do not repeat employee ages, wages or personal notes in chat beyond what
  a flag requires.
