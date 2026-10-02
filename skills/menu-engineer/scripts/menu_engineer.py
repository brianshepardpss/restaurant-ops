#!/usr/bin/env python3
"""Menu engineering (Kasavana-Smith matrix) from a POS item sales export.

Usage:
  python3 menu_engineer.py --sample [--pos square|toast] [--out DIR]
  python3 menu_engineer.py --sales export.csv (--costs recipe_costs.csv | --ingredients X --recipes Y) \
      [--map pos_item_map.csv] [--out DIR]

Reads Toast ItemSelectionDetails, Square Items Detail, or any CSV with item /
qty / net sales columns (matched by header synonyms, never by position).
Excludes Toast rows with Void? = true; subtracts Square Refund rows.

Formulas:
  avg price (per item)    = net sales / qty sold
  contribution margin CM  = avg price - plate cost
  menu mix %              = item qty / total qty x 100
  popularity threshold    = 70% x (1 / number of items) x 100
  CM threshold            = total CM dollars / total qty  (weighted average CM)
  Star      = mix % >= threshold and CM >= weighted avg CM
  Plowhorse = mix % >= threshold and CM <  weighted avg CM
  Puzzle    = mix % <  threshold and CM >= weighted avg CM
  Dog       = mix % <  threshold and CM <  weighted avg CM
Items with no matching recipe cost are listed as excluded, never estimated.
"""
import argparse
import importlib.util
import sys
from decimal import Decimal as D
from pathlib import Path

HERE = Path(__file__).resolve().parent
# Load the shared math module by file path (works wherever the plugin folder is).
_KM = Path(__file__).resolve().parents[2] / "plate-cost" / "scripts" / "kitchen_math.py"
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
money = km.money
q2 = km.q2
read_csv = km.read_csv
write_csv = km.write_csv

SYN = {
    "item": ["menu item", "item", "item name", "name", "product"],
    "qty": ["qty", "quantity", "item qty", "count", "quantity sold", "items sold"],
    "net": ["net price", "net sales", "item net amount", "net amount", "net"],
    "gross": ["gross price", "gross sales", "item gross amount", "gross"],
    "void": ["void?", "void", "voided"],
    "event": ["event type"],
}

ACTIONS = {
    "Star": "Keep: protect portion and quality, give it the best menu spot, test a small price rise.",
    "Plowhorse": "Popular but thin margin: re-portion or swap a costly component, or nudge price; do not bury it.",
    "Puzzle": "Good margin, low sales: reposition (top-right, box it), rename/describe, have staff recommend it.",
    "Dog": "Low sales and margin: rework the recipe/price or drop it, unless it serves a purpose (kids, dietary).",
}


def col(headers, name):
    low = {h.lower().strip(): h for h in headers}
    for s in SYN[name]:
        if s in low:
            return low[s]
    return None


def load_sales(path):
    rows = read_csv(path)
    if not rows:
        raise SystemExit("sales file is empty")
    h = list(rows[0].keys())
    ci, cq, cn, cg, cv, ce = (col(h, n) for n in ("item", "qty", "net", "gross", "void", "event"))
    if not ci or not cq or not (cn or cg):
        raise SystemExit(f"could not find item/qty/sales columns in headers: {h}\n"
                         "Rename columns or tell me which is which.")
    fmt = "Toast ItemSelectionDetails" if cv else "Square Items Detail" if ce else "generic item sales"
    agg, voids, refunds = {}, 0, 0
    for r in rows:
        if cv and r.get(cv, "").lower() in ("true", "yes", "1", "y"):
            voids += 1
            continue
        q = money(r.get(cq)) or D("0")
        amt = money(r.get(cn or cg)) or D("0")
        if ce and r.get(ce, "").lower() == "refund":
            refunds += 1
            q, amt = -abs(q), -abs(amt)
        name = " ".join(r.get(ci, "").split())
        a = agg.setdefault(key(name), [D("0"), D("0"), name])
        a[0] += q
        a[1] += amt
    return fmt, agg, voids, refunds, (cn or cg)


def load_costs(args):
    if args.costs:
        out = {}
        for r in read_csv(args.costs):
            if r.get("type", "menu item") == "menu item" and r.get("plate_cost_exact", r.get("plate_cost")):
                out[key(r["recipe"])] = (r["recipe"], money(r.get("plate_cost_exact") or r.get("plate_cost")))
        return out
    ing, rec = load_ingredients(args.ingredients), load_recipes(args.recipes)
    c = Coster(ing, rec)
    out = {}
    for rk, r in rec.items():
        if r["menu_price"] is not None:
            out[rk] = (r["name"], c.plate(rk)[0])
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--sample", action="store_true")
    ap.add_argument("--pos", choices=["square", "toast"], default="square", help="which sample export (with --sample)")
    ap.add_argument("--sales")
    ap.add_argument("--costs", help="recipe_costs.csv from plate_cost.py")
    ap.add_argument("--ingredients")
    ap.add_argument("--recipes")
    ap.add_argument("--map", help="CSV pos_item,recipe for names that differ")
    ap.add_argument("--out", default="restaurant-ops-output")
    a = ap.parse_args()
    if a.sample:
        a.sales = a.sales or str(SAMPLES / ("sales_toast_itemselectiondetails.csv" if a.pos == "toast"
                                            else "sales_square_items_detail.csv"))
        if not a.costs:
            a.ingredients = a.ingredients or SAMPLES / "ingredients.csv"
            a.recipes = a.recipes or SAMPLES / "recipes.csv"
        a.map = a.map or SAMPLES / "pos_item_map.csv"
    if not a.sales or not (a.costs or (a.ingredients and a.recipes)):
        ap.error("give --sales and --costs (or --ingredients and --recipes), or --sample")

    try:
        costs = load_costs(a)
    except CostError as e:
        raise SystemExit("CANNOT COST RECIPES:\n  " + str(e).replace("\n", "\n  "))
    fmt, agg, voids, refunds, money_col = load_sales(a.sales)
    alias = {key(r["pos_item"]): key(r["recipe"]) for r in read_csv(a.map)} if a.map else {}

    items, excluded = [], []
    for nk, (q, amt, name) in sorted(agg.items()):
        rk = alias.get(nk, nk)
        if rk in costs and q <= 0:
            excluded.append((name, q, amt, "net qty is zero or negative after refunds/voids"))
        elif rk in costs:
            items.append({"pos": name, "recipe": costs[rk][0], "qty": q, "sales": amt,
                          "price": amt / q, "cost": costs[rk][1]})
        else:
            excluded.append((name, q, amt, "no recipe cost on file (map or cost it to include)"))
    if not items:
        raise SystemExit("no sales items matched a costed recipe; supply --map")

    n = len(items)
    total_q = sum(i["qty"] for i in items)
    for i in items:
        i["cm"] = i["price"] - i["cost"]
        i["cm_total"] = i["cm"] * i["qty"]
        i["mix"] = i["qty"] / total_q * D("100")
    total_cm = sum(i["cm_total"] for i in items)
    pop_t = D("70") / D(n)
    cm_t = total_cm / total_q
    for i in items:
        hp, hc = i["mix"] >= pop_t, i["cm"] >= cm_t
        i["class"] = "Star" if hp and hc else "Plowhorse" if hp else "Puzzle" if hc else "Dog"

    print(f"Source: {fmt} ({Path(a.sales).name}); money column '{money_col}'; "
          f"{voids} voided rows skipped; {refunds} refund rows subtracted")
    print(f"Items analyzed: {n} | total qty {total_q} | total CM ${q2(total_cm)} | "
          f"popularity threshold {q2(pop_t)}% (70% x 1/{n}) | weighted avg CM ${q2(cm_t)} "
          f"(${q2(total_cm)} / {total_q})\n")
    print(f"{'item':<16}{'qty':>6}{'mix%':>8}{'price':>8}{'cost':>8}{'CM':>8}{'CM total':>11}  class")
    for i in sorted(items, key=lambda x: -x["qty"]):
        print(f"{i['recipe']:<16}{i['qty']:>6}{q2(i['mix']):>8}{q2(i['price']):>8}{q2(i['cost']):>8}"
              f"{q2(i['cm']):>8}{q2(i['cm_total']):>11}  {i['class']}")
    if excluded:
        print("\nExcluded from the matrix:")
        for name, q, amt, why in excluded:
            print(f"  {name}: qty {q}, net ${q2(amt)} - {why}")
    print("\nActions:")
    for i in sorted(items, key=lambda x: ["Star", "Plowhorse", "Puzzle", "Dog"].index(x["class"])):
        print(f"  {i['recipe']} ({i['class']}): {ACTIONS[i['class']]}")

    out = Path(a.out)
    write_csv(out / "menu_matrix.csv",
              ["item", "pos_name", "qty", "menu_mix_pct", "avg_price", "plate_cost", "contribution_margin",
               "cm_total", "popularity", "margin", "class", "suggested_action"],
              [[i["recipe"], i["pos"], i["qty"], q2(i["mix"]), q2(i["price"]), q2(i["cost"]), q2(i["cm"]),
                q2(i["cm_total"]), "high" if i["mix"] >= pop_t else "low", "high" if i["cm"] >= cm_t else "low",
                i["class"], ACTIONS[i["class"]]] for i in items]
              + [[], ["TOTAL", "", total_q, "100.00", "", "", "", q2(total_cm), f"threshold {q2(pop_t)}%",
                      f"threshold ${q2(cm_t)}", "", ""]]
              + [[f"EXCLUDED: {nm}", "", q, "", "", "", "", "", "", "", "", why] for nm, q, _, why in excluded])
    print(f"\nWrote {out / 'menu_matrix.csv'}")


if __name__ == "__main__":
    main()
