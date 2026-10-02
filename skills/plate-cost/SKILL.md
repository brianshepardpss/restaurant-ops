---
name: plate-cost
description: Use when a restaurant owner, chef or GM wants to cost a recipe or plate, find food cost %, or price a dish to a target food cost, or says "cost out this recipe", "what does this plate cost me", "what's my food cost on the burger", "price this at 28%", "build a recipe costing sheet", or "my food cost is too high". Takes a recipe (pasted, spreadsheet or CSV) plus ingredient pack prices; returns per-line costs with the arithmetic shown, plate cost, food cost % and price at target, as CSV.
---

# Plate cost and price-to-target

All numbers come from `scripts/plate_cost.py` (standard-library Python, in
this skill's directory). Never compute a cost, percentage or price yourself.

## 1. Get the inputs

- Demo / "try it": use `--sample` (bundled fictional restaurant).
- The user's data: you need two CSVs in the format of `../../samples/ingredients.csv`
  and `../../samples/recipes.csv`. Read `formats.md` (this directory) for the
  columns and how to convert a pasted recipe or spreadsheet. Write the CSVs
  into the working folder, then show the user the rows you wrote and ask
  "Is this right?" before costing if you had to interpret anything.
- Missing pack size, pack price or unit: ask. Do not guess or use "typical"
  prices. The script refuses rows without them.
- Ask for yield % only when it matters (raw proteins, produce with trim).
  If the user does not know, cost at 100% and say the plate is understated.
- Recipe quantities are edible portion (EP): the cooked/trimmed amount on
  the plate. Yield is applied as AP price / yield, never AP x yield.

## 2. Run

```
python3 <this skill dir>/scripts/plate_cost.py --ingredients ingredients.csv \
  --recipes recipes.csv --target 28 --out restaurant-ops-output
```

Options: `--recipe "Chicken Bowl"` for one dish, `--target N` for another
target %, `--q-factor N` to add N% for oil, condiments and waste (only if
the user asks or already uses a Q-factor).

If it prints `CANNOT COST`, show the listed rows and ask for the missing
data. Never "fill in" a value to make it run.

## 3. Report

Use this template, copying numbers exactly from the script output:

```
**<Dish>** - plate cost $X.XX at menu $Y.YY = Z.ZZ% food cost

| Component | Qty | Line cost | Working |
|---|---|---|---|
| ... from the script's bracketed working ... |

Price at <target>%: $P.PP (currently <over/under> by $G.GG)
Biggest cost line: <component> ($ / % of plate)
```

Then at most 3 practical levers, tied to the biggest lines (portion, yield,
supplier, price). Pricing is a suggestion: mention that menu prices also
depend on competition and guest perception.

Files written: `recipe_costs.csv` (one row per dish) and `recipe_lines.csv`
(every line with its working). Tell the user both paths. These open in
Excel or Google Sheets.

## Rules

- Never estimate a price or a number in prose. If the script cannot produce
  it, say what is missing.
- "oz" is weight. Liquids measured by volume must be "fl oz". If a user
  writes "2 oz of sauce", ask weight or fluid ounces only if the ingredient
  is bought by weight and has no density; otherwise use what fits the pack.
- Weight-to-volume needs `density_g_per_ml` on the ingredient row; ask for
  it or for the pack in the same dimension.
- After an invoice arrives, hand off to the invoice-tracker skill; for
  sales-mix questions, the menu-engineer skill.
