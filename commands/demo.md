---
description: Run the Restaurant Ops hero workflow on the bundled sample restaurant - plate costs, last invoice's price changes, and menu engineering - in under 5 minutes.
argument-hint: "[target food cost %, default 28]"
---

Run the Restaurant Ops demo on the bundled, fictional "Bluebird Bowl Co."
data. Target food cost: $ARGUMENTS (use 28 if empty). Use the plate-cost,
invoice-tracker and menu-engineer skills; every number must come from their
scripts. The plugin root is two levels above each skill's directory;
samples are in `samples/` there. Write all outputs to
`restaurant-ops-output/` in the working folder.

1. **Plate costs.** Run plate-cost's `scripts/plate_cost.py --sample --target <T>`.
   Show the Chicken Bowl working line by line, then a one-row-per-dish table
   (plate cost, menu price, food cost %, price at target).
2. **Last invoice.** Say that `samples/invoice_2026-09-28.pdf` was
   extracted to `samples/invoice_2026-09-28.csv` and (in real use) you would
   show the lines for confirmation first. Run invoice-tracker's
   `scripts/invoice_tracker.py --sample --target <T>`. Show the flagged
   change and the plate-impact table, and name the dishes that did not move.
3. **Menu engineering on current costs.** Run menu-engineer's
   `scripts/menu_engineer.py --sample --ingredients restaurant-ops-output/ingredients_updated.csv --recipes <plugin root>/samples/recipes.csv`
   so the matrix uses post-invoice costs. Show the matrix table with the
   thresholds.
4. **What to do Monday.** Exactly 5 bullets combining the three results
   (reprice / re-portion / reposition / call the vendor / fix the dog),
   each citing a number from the script output.
5. List the CSV files written and say: "To run this on your own menu, send
   me your ingredient prices and recipes (any format) and a POS item sales
   export."
