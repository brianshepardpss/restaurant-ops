---
name: invoice-tracker
description: Use when a restaurant gets a new vendor invoice or price sheet and wants to know what got more expensive and which plates it hits, or says "new invoice came in", "chicken went up, what does that do to my food cost", "check this Sysco/US Foods invoice for price changes", "track supplier price creep", or "update my ingredient prices". Takes an invoice PDF, photo or CSV plus the ingredient master; returns flagged price changes and before/after plate costs as CSV.
---

# Invoice price changes -> plate costs

Numbers come from `scripts/invoice_tracker.py` (this skill's directory),
which reuses the plate-cost math. Never compute a change % or plate cost
yourself.

## 1. Get confirmed invoice lines

- Demo: `--sample` uses `../../samples/invoice_2026-09-28.csv` (the
  confirmed version of `../../samples/invoice_2026-09-28.pdf`).
- A CSV/spreadsheet export from the vendor portal: map its columns to
  item_code, description, pack_size, pack_unit, unit_price (the script also
  accepts common synonyms: "Item #", "SUPC", "Price", "UOM", "Pack Size").
  Distributor exports with separate "Pack" (count) and "Size" ("10LB")
  columns are multiplied: 4 x 10 lb = 40 lb. A blank pack size is refused,
  never filled in from the old price list.
- A PDF or photo: read it, extract ONLY item lines (skip subtotals, fuel
  surcharges, deposits, credits, taxes) into a table and SHOW IT to the
  user:

  ```
  | Item # | Description | Pack | Unit | Case price |
  ```

  Ask: "I read these N lines from the invoice. Are the prices and pack
  sizes right?" Wait for a yes (or corrections) before running anything.
  OCR misreads ($112.00 vs $11.20, 4/10LB vs 40LB) are the main risk.
  Write the confirmed lines to `invoice_lines.csv`.
- unit_price is the price for the pack as listed (the case price), not the
  extended line total.

## 2. Run

```
python3 <this skill dir>/scripts/invoice_tracker.py --ingredients ingredients.csv \
  --recipes recipes.csv --invoice invoice_lines.csv --threshold 5 --out restaurant-ops-output
```

`--threshold` is the % change worth flagging (default 5). Matching is by
item code, then exact ingredient name. Lines marked NOT IN MASTER are not
guessed: ask whether each is a new ingredient (then add it with
plate-cost's format) or non-food (ignore).

If any line is marked `VERIFY` (change over 25%), show that line next to
the invoice image/text and ask the user to re-confirm it before you report
plate impact as final; a misread decimal is more likely than a 90% price
drop. Rows listed under "INVOICE ROWS NOT APPLIED" (missing pack size, same
item twice at different prices) need the user's answer, then re-run.

## 3. Report

```
**Invoice <vendor> <date>: <n> price changes flagged (>= <threshold>%)**

| Ingredient | Was | Now | Change |
|---|---|---|---|

**Plates affected**
| Dish | Cost before | Cost after | Food cost % before -> after | Price at target |
|---|---|---|---|---|

Unchanged: <list of dishes with no change>
Not in your ingredient list: <lines>
```

Then 1-3 options for each materially affected plate (absorb, re-portion,
substitute, re-price to the script's price-at-target, or ask the vendor /
get a competing quote). Suggestions only.

Files: `price_changes.csv`, `plate_impact.csv`, and `ingredients_updated.csv`
(the new master). The original ingredient file is never modified. Ask
before replacing the user's master with `ingredients_updated.csv`.

## Rules

- No price is applied until the user has confirmed the extracted lines.
- Pack size changes are price changes: the script compares per-unit cost,
  so a 40 lb case becoming a 36 lb case at the same price shows as a rise.
  Call this out when it happens ("shrinkflation").
- Do not invent a vendor or market explanation for a price change.
