# Sample data (all fictional)

"Bluebird Bowl Co." is a made-up fast-casual restaurant. Every name, vendor,
item code and number here is invented for the demo.

| File | What it is |
|---|---|
| ingredients.csv | Ingredient master: vendor, item code, pack size/unit, pack price, yield %. Has a blank row, a "$108.00" quoted price and an upper-case unit on purpose. |
| recipes.csv | 5 menu items + 1 sub-recipe (House sauce, 64 fl oz batch). Quantities are edible-portion (EP). |
| invoice_2026-09-28.txt | Text of a vendor invoice as it arrives (the PDF is at https://github.com/brianshepardpss/plugin-creator/tree/main/lab/sample-pdfs) (chicken thighs went from $98.00 to $112.00 per 40 lb case). |
| invoice_2026-09-28.csv | The same invoice after line extraction and user confirmation. |
| sales_square_items_detail.csv | 30 days of Square-style Items Detail export (includes 1 refund row). |
| sales_toast_itemselectiondetails.csv | The same 30 days as a Toast-style ItemSelectionDetails export (includes 1 voided row; kids item named differently). |
| pos_item_map.csv | Maps POS item names that differ from recipe names. |
| allergen_specs.csv | Allergen declarations per ingredient from supplier spec sheets. Gochujang has NO spec sheet on purpose. |
| staff.csv | 12 fictional staff with roles, wages, ages (one 15, one 17), availability and max hours. |
| coverage.csv | Shifts needed per day and role for the week. |

Expected results (from the bundled scripts):

- Chicken Bowl plate cost $2.43 (2.4334375), 20.28% at $12.00, $8.69 at 28%.
- After the invoice: chicken +14.29%, Chicken Bowl $2.60 (2.5975), 21.65%; no other dish changes.
- Menu engineering: 960 items, popularity threshold 14.00%. Weighted average CM is $10.17 on
  pre-invoice costs (total CM $9,762.96) and $10.10 on post-invoice costs (the /restaurant-ops:demo
  path, total CM $9,694.05). Either way: Chicken Bowl plowhorse, Steak Bowl and Salmon Plate stars,
  Veggie Bowl puzzle, Kids Plate dog.
- Labor draft at $18,000 forecast and 28% target: budget $5,040.00, scheduled $4,956.50 = 27.54%,
  1 overtime flag (E01), 2 minors flagged, 1 unfilled shift.
