---
name: menu-engineer
description: Use when a restaurant wants to know which menu items to keep, reprice, reposition or cut based on sales and margin, or says "run menu engineering", "which dishes are stars and dogs", "analyze my product mix / PMIX", "what should I take off the menu", or "look at my Toast/Square/Clover item sales". Takes a POS item sales export (Toast ItemSelectionDetails, Square Items Detail, Clover or any item/qty/sales CSV) plus recipe costs; returns a stars/plowhorses/puzzles/dogs matrix as CSV with actions.
---

# Menu engineering (Kasavana-Smith)

All numbers come from `scripts/menu_engineer.py` (this skill's directory).
Never classify an item or compute a margin in prose.

## 1. Inputs

- Demo: `--sample` (Square-style export; add `--pos toast` for the
  Toast-style one). Both cover the same 30 days.
- The user's sales export: any CSV with item name, quantity and net (or
  gross) sales. The script finds columns by header name. If it stops with
  "could not find item/qty/sales columns", show the headers and ask which
  is which. Excel exports (Clover) must be saved as CSV first; ask the user
  to do that or paste the table.
- Costs: either `recipe_costs.csv` from the plate-cost skill (`--costs`), or
  the ingredient + recipe CSVs (`--ingredients --recipes`). If the user has
  neither, cost the plates first with plate-cost. Never invent a plate cost.
- Use a period of at least 2-4 weeks with no menu or price change in the
  middle; ask if unsure.

## 2. Run

```
python3 <this skill dir>/scripts/menu_engineer.py --sales export.csv \
  --costs restaurant-ops-output/recipe_costs.csv [--map pos_item_map.csv] --out restaurant-ops-output
```

If items are listed under "Excluded (no recipe cost on file)", check
whether the POS name differs from the recipe name. If so, write a
`pos_item_map.csv` (columns `pos_item,recipe`), confirm it with the user,
and re-run. Beverages and add-ons without recipes may stay excluded; say so.

Analyze one menu category at a time when categories differ a lot (entrees
vs drinks vs kids); the thresholds assume items compete with each other.

## 3. Report

```
**Menu engineering - <period>, <n> items, <total qty> sold**
Popularity threshold <x>% (70% of 1/<n>) | Weighted average CM $<y>

| Item | Qty | Mix % | Price | Cost | CM | Class |
|---|---|---|---|---|---|---|

What to do Monday:
- Stars: ...
- Plowhorses: ...
- Puzzles: ...
- Dogs: ...
```

Base each bullet on the script's suggested action for that item and the
item's actual numbers (for a plowhorse, name its costliest component from
plate-cost if available). Keep it to 5 bullets.

Files: `menu_matrix.csv`.

## Rules

- Excluded rows (voids, refunds, unmapped items, items netting to zero
  after refunds) are reported with the reason, not hidden. Item names are
  grouped case- and space-insensitively.
- Prices come from net sales / qty in the export (what guests actually
  paid), so discounts lower CM. Mention it if discounts are large.
- Modifiers and add-ons are not costed in this version; mention it if the
  export shows many paid modifiers.
- Do not echo customer names, card data or employee names from the export.
