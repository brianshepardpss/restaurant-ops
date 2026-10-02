# Input formats (read when building CSVs from the user's data)

## ingredients.csv (one row per purchased item)

| column | required | example | notes |
|---|---|---|---|
| ingredient | yes | Chicken thigh boneless skinless | must match the recipe component text (case-insensitive) |
| vendor | no | Lone Prairie Foodservice | |
| item_code | no, but helps | LP-10442 | invoice matching uses this first |
| pack_size | yes | 40 | number only |
| pack_unit | yes | lb | see units below |
| pack_price | yes | $98.00 | "$" and "," are fine |
| yield_pct | no (default 100) | 80 | usable % after trim/cook loss; 0 < yield <= 100 |
| density_g_per_ml | no | 1.42 | only to convert weight <-> volume |
| notes | no | | |

A case of "4/10 lb" is pack_size 40, pack_unit lb. A "6/#10 can" case needs
the can net weight from the user; do not assume it.

## recipes.csv (one row per recipe line)

| column | example | notes |
|---|---|---|
| recipe | Chicken Bowl | repeated on every line of that recipe |
| menu_price | 12.00 | blank for sub-recipes (sauces, doughs, dressings) |
| batch_yield_qty | 1 | portions per batch, or batch size for sub-recipes (64) |
| batch_yield_unit | ea | "ea" for plates; "fl oz", "qt", "lb" etc for sub-recipes |
| component | Chicken thigh boneless skinless | an ingredient name OR another recipe name (sub-recipe) |
| qty | 6 | edible-portion amount |
| unit | oz | |

If a recipe makes several portions (a batch of 12 burritos), set
batch_yield_qty 12, batch_yield_unit ea, and give whole-batch quantities.

## Units understood

- weight: g, kg, oz, lb (also: gram, lbs, pound, #)
- volume: ml, l, tsp, tbsp, fl oz, cup, pt, qt, gal
- count: ea, dz (also: each, ct, pc, dozen)

"oz" always means weight. Volume ounces are "fl oz".

## Converting a pasted recipe

1. One line per ingredient: name, quantity, unit.
2. Match each name to an existing ingredient row; if none, add an ingredient
   row and ask for pack size, unit and price (or the invoice line).
3. Write both CSVs, show the rows, confirm, then run the script.
