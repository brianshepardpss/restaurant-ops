#!/usr/bin/env python3
"""Draft an allergen matrix (9 US major food allergens) from recipes and
supplier spec sheets. DRAFT FOR HUMAN VERIFICATION ONLY.

Usage:
  python3 allergen_matrix.py --sample [--out DIR]
  python3 allergen_matrix.py --recipes recipes.csv --specs allergen_specs.csv [--out DIR]

Specs CSV: ingredient, milk, egg, fish, crustacean_shellfish, tree_nuts,
peanuts, wheat, soy, sesame (Y/N each), may_contain (allergens named in a
precautionary statement, separated by ; or ,), spec_source, spec_date.

Rules, per dish and allergen, after expanding sub-recipes to ingredients:
  CONTAINS                      any ingredient spec says Y
  MAY CONTAIN (supplier)        no Y, but a spec lists it under may_contain
  UNKNOWN - verify              no Y, and at least one ingredient has no spec
                                sheet on file or a blank cell for that allergen
  not declared in specs on file all ingredients have specs and none declare it
"Not declared" is NOT a free-from claim: this script cannot see cross-contact,
shared fryers, supplier reformulation or substitutions. It never writes
"safe", "free of" or "allergen-free".
"""
import argparse
import importlib.util
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
# Load the shared math module by file path (works wherever the plugin folder is).
_KM = Path(__file__).resolve().parents[2] / "plate-cost" / "scripts" / "kitchen_math.py"
_spec = importlib.util.spec_from_file_location("kitchen_math", _KM)
km = importlib.util.module_from_spec(_spec)
sys.dont_write_bytecode = True
_spec.loader.exec_module(km)
SAMPLES = km.SAMPLES
key = km.key
load_recipes = km.load_recipes
read_csv = km.read_csv
write_csv = km.write_csv

ALLERGENS = ["milk", "egg", "fish", "crustacean_shellfish", "tree_nuts", "peanuts", "wheat", "soy", "sesame"]
LABELS = ["Milk", "Egg", "Fish", "Crustacean shellfish", "Tree nuts", "Peanuts", "Wheat", "Soy", "Sesame"]
DISCLAIMER = [
    "DRAFT - NOT VERIFIED. Built only from the recipes and supplier spec sheets on file.",
    "It cannot see cross-contact, shared fryers or equipment, supplier reformulation, or substitutions.",
    "'not declared' is not a free-from claim. A manager or chef must verify against current spec sheets",
    "and labels before this is shown to guests. Guests with allergies should speak with the manager.",
]


# Words suppliers use in precautionary statements -> our allergen keys.
MAY_SYN = {
    "milk": "milk", "dairy": "milk", "lactose": "milk", "whey": "milk", "casein": "milk",
    "egg": "egg", "eggs": "egg",
    "fish": "fish",
    "crustacean": "crustacean_shellfish", "crustaceans": "crustacean_shellfish",
    "crustacean shellfish": "crustacean_shellfish", "crustacean_shellfish": "crustacean_shellfish",
    "shellfish": "crustacean_shellfish", "shrimp": "crustacean_shellfish", "crab": "crustacean_shellfish",
    "lobster": "crustacean_shellfish",
    "tree nut": "tree_nuts", "tree nuts": "tree_nuts", "tree_nuts": "tree_nuts", "nut": "tree_nuts",
    "nuts": "tree_nuts", "almond": "tree_nuts", "almonds": "tree_nuts", "cashew": "tree_nuts",
    "walnut": "tree_nuts", "pecan": "tree_nuts", "pistachio": "tree_nuts", "hazelnut": "tree_nuts",
    "peanut": "peanuts", "peanuts": "peanuts",
    "wheat": "wheat", "gluten": "wheat",
    "soy": "soy", "soya": "soy", "soybean": "soy", "soybeans": "soy",
    "sesame": "sesame", "sesame seed": "sesame", "sesame seeds": "sesame",
}
SPEC_COLS = {"crustacean": "crustacean_shellfish", "shellfish": "crustacean_shellfish",
             "tree_nut": "tree_nuts", "treenuts": "tree_nuts", "peanut": "peanuts", "eggs": "egg",
             "dairy": "milk", "item": "ingredient", "ingredient_name": "ingredient"}


def parse_may(text):
    """Return (allergen keys, unrecognised words). "nuts" maps to tree nuts; any
    word we cannot map makes the dish UNKNOWN rather than silently dropped."""
    found, unread = set(), []
    for w in text.replace(";", ",").replace("/", ",").replace(" and ", ",").split(","):
        w = " ".join(w.strip().lower().split())
        if not w:
            continue
        if w in MAY_SYN:
            found.add(MAY_SYN[w])
        else:
            unread.append(w)
    return found, unread


def leaves(recipes, rk, stack=()):
    """Expand a recipe to the set of purchased ingredient names it uses."""
    if rk in stack:
        raise SystemExit(f"sub-recipe loop: {' -> '.join(stack + (rk,))}")
    out = []
    for ln in recipes[rk]["lines"]:
        ck = key(ln["component"])
        if ck in recipes:
            out += [(n, f"{recipes[ck]['name']} > {n}") for n, _ in leaves(recipes, ck, stack + (rk,))]
        else:
            out.append((ln["component"], ln["component"]))
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--sample", action="store_true")
    ap.add_argument("--recipes")
    ap.add_argument("--specs")
    ap.add_argument("--out", default="restaurant-ops-output")
    a = ap.parse_args()
    rp = a.recipes or (SAMPLES / "recipes.csv" if a.sample else None)
    sp = a.specs or (SAMPLES / "allergen_specs.csv" if a.sample else None)
    if not rp or not sp:
        ap.error("give --recipes and --specs, or --sample")
    recipes = load_recipes(rp)
    specs = {}
    for r in read_csv(sp, snake=True):
        r = {SPEC_COLS.get(k, k): v for k, v in r.items()}
        if r.get("ingredient"):
            specs[key(r["ingredient"])] = r

    rows, missing_all = [], {}
    for rk, r in recipes.items():
        if r["menu_price"] is None:
            continue
        ings = leaves(recipes, rk)
        cells, sources = [], []
        missing = sorted({path for n, path in ings if key(n) not in specs})
        unreadable = sorted({f"{path} (may_contain: {', '.join(parse_may(specs[key(n)].get('may_contain', ''))[1])})"
                             for n, path in ings if key(n) in specs
                             and parse_may(specs[key(n)].get("may_contain", ""))[1]})
        for al in ALLERGENS:
            yes, may, blank = [], [], []
            for n, path in ings:
                s = specs.get(key(n))
                if s is None:
                    continue
                v = s.get(al, "").strip().upper()
                mc, unread = parse_may(s.get("may_contain", ""))
                if v in ("Y", "YES", "TRUE", "1", "CONTAINS"):
                    yes.append(path)
                elif al in mc:
                    may.append(path)
                elif v not in ("N", "NO", "FALSE", "0") or unread:
                    blank.append(path)
            if yes:
                cells.append("CONTAINS")
                sources.append(f"{al}: {', '.join(sorted(set(yes)))}")
            elif may:
                cells.append("MAY CONTAIN (supplier)")
                sources.append(f"{al} (may contain): {', '.join(sorted(set(may)))}")
            elif missing or blank:
                cells.append("UNKNOWN - verify")
            else:
                cells.append("not declared in specs on file")
        for m in missing + [f"{u} - words not recognised" for u in unreadable]:
            missing_all.setdefault(m, []).append(r["name"])
        rows.append([r["name"]] + cells + ["; ".join(sources),
                                           "; ".join(missing + [f"UNREADABLE {u}" for u in unreadable]),
                                           "NEEDS MANAGER SIGN-OFF"])

    print("\n".join(DISCLAIMER))
    print()
    w = 14
    print(f"{'dish':<14}" + "".join(f"{l[:w-1]:<{w}}" for l in LABELS))
    short = {"CONTAINS": "CONTAINS", "MAY CONTAIN (supplier)": "MAY CONTAIN", "UNKNOWN - verify": "UNKNOWN",
             "not declared in specs on file": "not declared"}
    for row in rows:
        print(f"{row[0]:<14}" + "".join(f"{short[c]:<{w}}" for c in row[1:10]))
    if missing_all:
        print("\nNO SPEC SHEET / UNREADABLE SPEC (every allergen not otherwise declared is UNKNOWN for these dishes):")
        for m, dishes in missing_all.items():
            print(f"  {m}  -> used in {', '.join(dishes)}. Get the supplier spec sheet or label.")
    out = Path(a.out)
    write_csv(out / "allergen_matrix.csv",
              ["dish"] + LABELS + ["declared_by", "missing_spec_sheets", "status"], rows, preamble=DISCLAIMER)
    print(f"\nWrote {out / 'allergen_matrix.csv'} (disclaimer is in the first 4 lines of the file)")


if __name__ == "__main__":
    main()
