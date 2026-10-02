#!/usr/bin/env python3
"""Cost every recipe and price it to a target food cost %.

Usage:
  python3 plate_cost.py --sample [--target 28] [--out DIR]
  python3 plate_cost.py --ingredients ingredients.csv --recipes recipes.csv \
      [--target 28] [--q-factor 0] [--recipe "Chicken Bowl"] [--out DIR]

Formulas (see kitchen_math.py):
  line cost         = qty_EP x (pack_price / pack_size_in_line_units) / (yield_pct/100)
  plate cost        = sum(line costs) x (1 + q_factor/100)
  food cost %       = plate cost / menu price x 100
  price at target % = plate cost / (target/100), rounded to the cent

Writes recipe_lines.csv and recipe_costs.csv to --out (default ./restaurant-ops-output).
Exits 2 and lists every problem (missing pack size, unknown unit, unknown
component) instead of guessing.
"""
import argparse
import importlib.util
import sys
from decimal import Decimal as D
from pathlib import Path

# Load the shared math module by file path (works wherever the plugin folder is).
_KM = Path(__file__).resolve().parent / "kitchen_math.py"
_spec = importlib.util.spec_from_file_location("kitchen_math", _KM)
km = importlib.util.module_from_spec(_spec)
sys.dont_write_bytecode = True
_spec.loader.exec_module(km)
SAMPLES = km.SAMPLES
Coster = km.Coster
CostError = km.CostError
key = km.key
load_ingredients = km.load_ingredients
load_recipes = km.load_recipes
pct = km.pct
q2 = km.q2
q4 = km.q4
exact = km.exact
write_csv = km.write_csv


def run(ingredients, recipes, target, q_factor, only=None):
    ing = load_ingredients(ingredients)
    rec = load_recipes(recipes)
    c = Coster(ing, rec, q_factor)
    results, errs = [], []
    for rk, r in rec.items():
        if only and rk != key(only):
            continue
        try:
            plate, base, lines = c.plate(rk)
        except CostError as e:
            errs.append(str(e))
            continue
        price = r["menu_price"]
        if price is not None and price <= 0:
            errs.append(f"{r['name']}: menu_price must be greater than 0 (got {price}); food cost % is n/a")
            continue
        results.append({"recipe": r["name"], "is_menu": price is not None, "menu_price": price,
                        "batch": f"{r['yield_qty']} {r['yield_unit']}", "base": base,
                        "batch_total": base * r["yield_qty"], "yield_unit": r["yield_unit"],
                        "plate": plate, "lines": lines,
                        "fc_pct": pct(plate, price) if price else None,
                        "price_at_target": q2(plate / (target / D("100"))) if price else None})
    if only and not results and not errs:
        errs.append(f"recipe {only!r} not found")
    return results, errs


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--sample", action="store_true", help="use the bundled sample files")
    ap.add_argument("--ingredients")
    ap.add_argument("--recipes")
    ap.add_argument("--target", type=D, default=D("28"), help="target food cost %% (default 28)")
    ap.add_argument("--q-factor", type=D, default=D("0"), help="%% added for condiments/oil/waste (default 0)")
    ap.add_argument("--recipe", help="cost only this recipe")
    ap.add_argument("--out", default="restaurant-ops-output")
    a = ap.parse_args()
    ing = a.ingredients or (SAMPLES / "ingredients.csv" if a.sample else None)
    rec = a.recipes or (SAMPLES / "recipes.csv" if a.sample else None)
    if not ing or not rec:
        ap.error("give --ingredients and --recipes, or --sample")
    try:
        results, errs = run(ing, rec, a.target, a.q_factor, a.recipe)
    except CostError as e:
        results, errs = [], [str(e)]
    if errs:
        print("CANNOT COST - fix these rows first (nothing was guessed):")
        for e in errs:
            print("  " + e.replace("\n", "\n  "))
        if not results:
            sys.exit(2)

    line_rows, cost_rows = [], []
    for r in results:
        print(f"\n== {r['recipe']}" + (f"  (menu ${r['menu_price']})" if r["is_menu"] else f"  (sub-recipe, batch {r['batch']})"))
        for ln in r["lines"]:
            qu = f"{ln['qty']} {ln['unit']}"
            print(f"  {ln['component']:<34} {qu:<10} ${q4(ln['cost'])}   [{ln['work']}]")
            line_rows.append([r["recipe"], ln["component"], ln["kind"], ln["qty"], ln["unit"], q4(ln["cost"]), ln["work"]])
        if a.q_factor:
            print(f"  Q-factor {a.q_factor}% applied: ${q4(r['base'])} -> ${q4(r['plate'])}")
        if r["is_menu"]:
            print(f"  PLATE COST ${q2(r['plate'])} (exact {exact(r['plate'])}) | food cost {q2(r['fc_pct'])}% at "
                  f"${r['menu_price']} | price at {a.target}% target: ${r['price_at_target']}")
            cost_rows.append([r["recipe"], "menu item", r["menu_price"], exact(r["plate"]), q2(r["plate"]),
                              q2(r["fc_pct"]), a.target, r["price_at_target"],
                              q2(r["price_at_target"] - r["menu_price"]), a.q_factor])
        else:
            print(f"  BATCH COST ${q2(r['batch_total'])} for {r['batch']} = ${q4(r['base'])} per {r['yield_unit']}")
            cost_rows.append([r["recipe"], f"sub-recipe (batch {r['batch']}, cost per {r['yield_unit']})", "",
                              q4(r["base"]), q2(r["base"]), "", "", "", "", ""])

    out = Path(a.out)
    write_csv(out / "recipe_lines.csv",
              ["recipe", "component", "kind", "qty", "unit", "line_cost", "working"], line_rows)
    write_csv(out / "recipe_costs.csv",
              ["recipe", "type", "menu_price", "plate_cost_exact", "plate_cost", "food_cost_pct",
               "target_pct", "price_at_target", "price_gap", "q_factor_pct"], cost_rows)
    print(f"\nWrote {out / 'recipe_lines.csv'} and {out / 'recipe_costs.csv'}")
    print("Note: recipe quantities are edible-portion (EP) amounts; yield divides the AP price.")
    if errs:
        print("WARNING: some recipes were NOT costed (see CANNOT COST above); the CSVs are incomplete.")
        sys.exit(1)


if __name__ == "__main__":
    main()
