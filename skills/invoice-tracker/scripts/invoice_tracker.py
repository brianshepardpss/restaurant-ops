#!/usr/bin/env python3
"""Compare confirmed invoice lines to the ingredient master and ripple price
changes into every plate cost.

Usage:
  python3 invoice_tracker.py --sample [--threshold 5] [--out DIR]
  python3 invoice_tracker.py --ingredients ingredients.csv --recipes recipes.csv \
      --invoice invoice_lines.csv [--threshold 5] [--target 28] [--out DIR]

Invoice CSV columns (header synonyms accepted): item_code, description,
pack_size, pack_unit, unit_price (price per case/pack as invoiced). Instead of
pack_size you may give Pack (inner count) and Size ("10LB"): 4 x 10 lb = 40 lb.
Rows with no pack size, zero price, or an item listed twice at different
prices are refused. Changes over 25% are marked VERIFY (possible misread).

Formulas:
  old unit price  = old pack_price / old pack_size       (per pack_unit)
  new unit price  = invoice unit_price / invoice pack_size (converted to the master's pack_unit)
  change %        = (new unit price - old unit price) / old unit price x 100
  flagged         = |change %| >= threshold (default 5)
  plate impact    = plate cost with new prices - plate cost with old prices

Matching: item_code first, then exact ingredient name (case-insensitive).
Unmatched lines are listed, never guessed. The original ingredient file is
never modified; ingredients_updated.csv is written beside the other outputs.
"""
import argparse
import importlib.util
import re
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
convert = km.convert
dimension = km.dimension
key = km.key
load_ingredients = km.load_ingredients
load_recipes = km.load_recipes
money = km.money
norm_unit = km.norm_unit
num = km.num
pct = km.pct
q2 = km.q2
q4 = km.q4
exact = km.exact
read_csv = km.read_csv
write_csv = km.write_csv

SYN = {
    "item_code": ["item_code", "item #", "item no", "item number", "sku", "product code", "code", "supc"],
    "description": ["description", "item", "item description", "product", "product description"],
    "pack_size": ["pack_size", "pack size", "case size", "total size", "case qty"],
    "pack": ["pack", "pack count", "inner pack"],
    "size": ["size", "each size", "item size"],
    "pack_unit": ["pack_unit", "unit", "uom", "size unit"],
    "unit_price": ["unit_price", "price", "case price", "unit price", "each price"],
}


VERIFY_PCT = D("25")


def pack_of(row):
    """Total pack size and unit. Accepts pack_size+unit, or Pack (count) x Size ("10LB")."""
    ps = field(row, "pack_size")
    if ps:
        return num(ps), field(row, "pack_unit")
    pk, sz = field(row, "pack"), field(row, "size")
    if pk and sz:
        m = re.match(r"^\s*([\d.]+)\s*([A-Za-z#][A-Za-z#. ]*)?$", sz)
        if not m:
            raise CostError(f"cannot read size {sz!r}; give the total pack size")
        return num(pk) * num(m.group(1)), (m.group(2) or field(row, "pack_unit")).strip()
    if pk or sz:
        raise CostError("only one of Pack / Size given; give the total pack size (e.g. 4 x 10 lb = 40 lb)")
    return None, ""


def field(row, name):
    low = {k.lower().strip(): v for k, v in row.items()}
    for s in SYN[name]:
        if s in low and low[s] != "":
            return low[s]
    return ""


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--sample", action="store_true")
    ap.add_argument("--ingredients")
    ap.add_argument("--recipes")
    ap.add_argument("--invoice")
    ap.add_argument("--threshold", type=D, default=D("5"))
    ap.add_argument("--target", type=D, default=D("28"))
    ap.add_argument("--out", default="restaurant-ops-output")
    a = ap.parse_args()
    ing_p = a.ingredients or (SAMPLES / "ingredients.csv" if a.sample else None)
    rec_p = a.recipes or (SAMPLES / "recipes.csv" if a.sample else None)
    inv_p = a.invoice or (SAMPLES / "invoice_2026-09-28.csv" if a.sample else None)
    if not (ing_p and rec_p and inv_p):
        ap.error("give --ingredients, --recipes and --invoice, or --sample")

    try:
        old = load_ingredients(ing_p)
        recipes = load_recipes(rec_p)
    except CostError as e:
        print("CANNOT RUN - fix these rows first:\n  " + str(e).replace("\n", "\n  "))
        sys.exit(2)
    by_code = {g["item_code"].lower(): k for k, g in old.items() if g["item_code"]}
    new = {k: dict(g) for k, g in old.items()}

    changes, unmatched, problems = [], [], []
    for i, r in enumerate(read_csv(inv_p), start=2):
        code, desc = field(r, "item_code"), field(r, "description")
        k = by_code.get(code.lower()) if code else None
        k = k or (key(desc) if key(desc) in old else None)
        if not k:
            unmatched.append([code, desc, field(r, "unit_price")])
            continue
        g = old[k]
        try:
            price = money(field(r, "unit_price"))
            if price is None or price <= 0:
                raise CostError("missing or zero unit_price")
            size, unit = pack_of(r)
            if size is None or size <= 0:
                raise CostError("missing or zero pack size (will not assume the old size)")
            unit = norm_unit(unit or g["pack_unit"])
            dim = dimension(g["pack_unit"])
            size_in_master_units = (convert(size, unit, dim, g["density"])
                                    / convert(D("1"), g["pack_unit"], dim, g["density"]))
        except CostError as e:
            problems.append(f"invoice row {i} ({desc}): {e}")
            continue
        old_u = g["pack_price"] / g["pack_size"]
        new_u = price / size_in_master_units
        ch = pct(new_u - old_u, old_u)
        prev = next((c for c in changes if c["key"] == k), None)
        if prev:
            if prev["new_u"] != new_u:
                changes.remove(prev)
                new[k] = dict(old[k])
                problems.append(f"invoice row {i} ({desc}): {g['name']} appears twice with different "
                                f"prices; neither applied - confirm which line is right")
            continue
        new[k]["pack_price"], new[k]["pack_size"] = price, size_in_master_units
        changes.append({"key": k, "verify": abs(ch) >= VERIFY_PCT, "name": g["name"], "code": g["item_code"], "old_pack": g["pack_price"],
                        "new_pack": price, "old_u": old_u, "new_u": new_u, "unit": g["pack_unit"],
                        "pct": ch, "flag": abs(ch) >= a.threshold})

    if problems:
        print("INVOICE ROWS NOT APPLIED (fix and re-run):")
        for p in problems:
            print("  " + p)

    before, after = Coster(old, recipes), Coster(new, recipes)
    impact = []
    for rk, r in recipes.items():
        if r["menu_price"] is None:
            continue
        try:
            b, _, bl = before.plate(rk)
            n, _, nl = after.plate(rk)
        except CostError as e:
            print(f"  cannot cost {r['name']}: {e}")
            continue
        drivers = [f"{x['component']} {q4(x['cost'])}->{q4(y['cost'])}"
                   for x, y in zip(bl, nl) if q4(x["cost"]) != q4(y["cost"])]
        impact.append({"recipe": r["name"], "price": r["menu_price"], "b": b, "n": n,
                       "fb": pct(b, r["menu_price"]), "fn": pct(n, r["menu_price"]),
                       "pt": q2(n / (a.target / D("100"))), "drivers": drivers})

    print(f"PRICE CHANGES (threshold {a.threshold}%)")
    for c in changes:
        mark = "FLAG" if c["flag"] else ("same" if c["pct"] == 0 else "minor")
        if c["verify"]:
            mark = "FLAG - VERIFY, >25% change: re-check this line against the invoice"
        print(f"  [{mark}] {c['name']} ({c['code']}): ${c['old_pack']} -> ${c['new_pack']} per pack; "
              f"${q4(c['old_u'])} -> ${q4(c['new_u'])}/{c['unit']} = {q2(c['pct']):+}%")
    for u in unmatched:
        print(f"  [NOT IN MASTER] {u[0]} {u[1]} ${u[2]} - not costed (new item or non-food?)")

    print("\nPLATE IMPACT")
    for m in impact:
        d = m["n"] - m["b"]
        if q4(d) == 0:
            print(f"  {m['recipe']}: unchanged ${q2(m['n'])} ({q2(m['fn'])}%)")
        else:
            print(f"  {m['recipe']}: ${q2(m['b'])} (exact {exact(m['b'])}) -> ${q2(m['n'])} (exact {exact(m['n'])}), "
                  f"{q4(d):+} | food cost {q2(m['fb'])}% -> {q2(m['fn'])}% at ${m['price']} | "
                  f"price at {a.target}%: ${m['pt']} | driver: {'; '.join(m['drivers'])}")

    out = Path(a.out)
    write_csv(out / "price_changes.csv",
              ["ingredient", "item_code", "old_pack_price", "new_pack_price", "unit", "old_unit_price",
               "new_unit_price", "change_pct", "flagged", "verify_line"],
              [[c["name"], c["code"], c["old_pack"], c["new_pack"], c["unit"], q4(c["old_u"]), q4(c["new_u"]),
                q2(c["pct"]), "YES" if c["flag"] else "", "VERIFY >25%" if c["verify"] else ""] for c in changes]
              + [[u[1], u[0], "", u[2], "", "", "", "", "NOT IN MASTER", ""] for u in unmatched])
    write_csv(out / "plate_impact.csv",
              ["recipe", "menu_price", "cost_before", "cost_after", "change", "food_cost_pct_before",
               "food_cost_pct_after", "price_at_target", "drivers"],
              [[m["recipe"], m["price"], q4(m["b"]), q4(m["n"]), q4(m["n"] - m["b"]), q2(m["fb"]), q2(m["fn"]),
                m["pt"], "; ".join(m["drivers"])] for m in impact])
    hdr = list(next(iter(old.values()))["raw"].keys())
    rows = []
    for k, g in new.items():
        raw = dict(g["raw"])
        raw["pack_price"] = f"{q2(g['pack_price'])}"
        raw["pack_size"] = f"{g['pack_size'].normalize():f}"
        rows.append([raw.get(h, "") for h in hdr])
    write_csv(out / "ingredients_updated.csv", hdr, rows)
    print(f"\nWrote price_changes.csv, plate_impact.csv, ingredients_updated.csv to {out}")
    print("Original ingredient file untouched. Use ingredients_updated.csv as the new master once confirmed.")


if __name__ == "__main__":
    main()
