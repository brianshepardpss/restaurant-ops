# Restaurant Ops

Your food-cost spreadsheet, done by Claude. Know what every plate costs,
what your last invoice did to it, and which dishes to reprice, re-portion,
reposition or cut. Plus an allergen matrix draft and a costed labor
schedule draft. Every number comes from a bundled script that shows its
working, never from a guess.

**For:** owners, chef-owners and GMs of independent restaurants (1-3
locations) who do back-office math in Excel or Google Sheets and do not
want another $150-350/month subscription.

Works in: Claude Cowork, claude.ai and Claude Code. No account, API key or
POS connection needed.

## Install (60 seconds)

Claude Code:

```
/plugin marketplace add brianshepardpss/plugin-creator
/plugin install restaurant-ops@plugin-creator
```

Cowork / claude.ai: add the `brianshepardpss/plugin-creator` marketplace in
the plugin settings and enable Restaurant Ops (or upload the plugin folder).

## Try it on the sample restaurant

```
/restaurant-ops:demo
```

or just ask "show me the restaurant ops demo". In a few minutes you get, for
a fictional fast-casual spot:

1. Plate costs for 5 dishes and a sub-recipe sauce, with the arithmetic on
   every line. Chicken Bowl: $2.43 = 20.28% food cost at $12.00; price at
   28% would be $8.69.
2. The latest invoice: chicken thighs +14.29% ($98.00 -> $112.00 per 40 lb
   case), Chicken Bowl now $2.60 = 21.65%, every other dish unchanged.
3. Menu engineering on 30 days of Square-style item sales: stars,
   plowhorses, puzzles, dogs.
4. Five "what to do Monday" actions, and CSV files you can open in Excel or
   Google Sheets.

## What it does

| Skill | Ask it | You get |
|---|---|---|
| plate-cost | "cost out this recipe and price it at 28%" | per-line costs (yield applied as AP / yield), plate cost, food cost %, price at target; `recipe_costs.csv`, `recipe_lines.csv` |
| invoice-tracker | "new invoice came in, what went up?" | flagged price changes (default >= 5%) and before/after plate costs; you confirm the extracted invoice lines first; `price_changes.csv`, `plate_impact.csv`, `ingredients_updated.csv` |
| menu-engineer | "which dishes are stars and dogs?" | Kasavana-Smith matrix from a Toast, Square, Clover or any item-sales CSV; `menu_matrix.csv` |
| allergen-matrix | "make an allergen chart for the staff" | DRAFT matrix of the 9 major US allergens; UNKNOWN wherever a spec sheet is missing; never says "safe" or "free of"; `allergen_matrix.csv` |
| labor-draft | "draft next week's schedule at 28% labor on $18k" | costed draft schedule with overtime, minor and predictive-scheduling flags; `schedule_draft.csv`, `labor_summary.csv` |
| request | "I wish this could..." | a drafted feature request you can file yourself |

Output is CSV (opens in Excel and Google Sheets). The scripts use only the
Python standard library, which cannot write .xlsx files.

## Using your own data

Send Claude your ingredient prices and recipes in any shape (a spreadsheet,
a photo of the costing binder, pasted text). It converts them to two simple
CSVs (see `skills/plate-cost/formats.md`), shows you the rows, and asks you
to confirm before costing. For menu engineering, export item sales from
your POS:

- Toast: ItemSelectionDetails.csv from the data export (voided rows are skipped).
- Square: Items Detail CSV from Reports (refund rows are subtracted).
- Clover or anything else: any CSV with item name, quantity and net sales.

## Limits and guardrails

- Allergen output is a draft for manager or chef verification. It cannot
  see cross-contact, shared fryers, substitutions or supplier
  reformulation, and it never marks a dish as safe for an allergy.
- Labor output is a draft, not legal advice. It applies federal overtime
  and federal 14-15 year old limits; state rules and predictive scheduling
  coverage must be checked locally.
- Invoice prices are applied only after you confirm the extracted lines.
- Pricing suggestions are suggestions; the plugin does not look up
  competitor prices.

## Privacy

Nothing leaves your machine beyond your normal Claude conversation. The
plugin makes no network calls, has no telemetry, and connects to no POS.
Sales and staff files can contain names; the skills avoid repeating them.

## Feedback

Say "I wish this could..." and the request skill drafts an issue for you to
file. Nothing is sent automatically.

Not affiliated with or endorsed by Toast, Inc., Block, Inc. (Square), or
Clover Network, LLC. Not affiliated with or endorsed by MarginEdge, Sysco or
US Foods. All sample names, vendors and figures are fictional.
