"""Shared kitchen math for Restaurant Ops (standard library only).

Formulas (all money math uses Decimal, never float):

  AP unit cost      = pack_price / (pack_size converted to the line's base unit)
  EP unit cost      = AP unit cost / (yield_pct / 100)      # yield DIVIDES, never multiplies
  line cost         = recipe qty (EP, converted to base unit) x EP unit cost
  sub-recipe cost   = sum(batch line costs) / batch_yield, used like an ingredient
  plate cost        = sum(line costs) x (1 + q_factor_pct / 100)
  food cost %       = plate cost / menu price x 100
  price at target % = plate cost / (target_pct / 100)

Units: weight (g, kg, oz, lb), volume (ml, l, tsp, tbsp, fl oz, cup, pt, qt,
gal) and count (ea, dz). Weight <-> volume only when the ingredient row has
density_g_per_ml. "oz" always means weight ounces; write "fl oz" for volume.
"""
import csv
import re
from decimal import Decimal, ROUND_HALF_UP, InvalidOperation
from pathlib import Path

D = Decimal

WEIGHT_G = {"g": D("1"), "kg": D("1000"), "oz": D("28.349523125"), "lb": D("453.59237")}
VOLUME_ML = {
    "ml": D("1"), "l": D("1000"), "tsp": D("4.92892159375"), "tbsp": D("14.78676478125"),
    "floz": D("29.5735295625"), "cup": D("236.5882365"), "pt": D("473.176473"),
    "qt": D("946.352946"), "gal": D("3785.411784"),
}
COUNT_EA = {"ea": D("1"), "dz": D("12")}

UNIT_ALIASES = {
    "gram": "g", "grams": "g", "gm": "g", "kgs": "kg", "kilogram": "kg",
    "ounce": "oz", "ounces": "oz", "oz wt": "oz", "ozwt": "oz",
    "lbs": "lb", "pound": "lb", "pounds": "lb", "#": "lb",
    "milliliter": "ml", "millilitre": "ml", "liter": "l", "litre": "l", "lt": "l",
    "teaspoon": "tsp", "tablespoon": "tbsp", "tbs": "tbsp", "tbl": "tbsp",
    "fl oz": "floz", "fl. oz": "floz", "fl.oz": "floz", "floz": "floz", "fluid ounce": "floz",
    "cups": "cup", "c": "cup", "pint": "pt", "pints": "pt", "quart": "qt", "quarts": "qt",
    "gallon": "gal", "gallons": "gal",
    "each": "ea", "ct": "ea", "count": "ea", "pc": "ea", "pcs": "ea", "piece": "ea",
    "dozen": "dz", "doz": "dz",
}

SAMPLES = Path(__file__).resolve().parents[3] / "samples"


class CostError(Exception):
    pass


def norm_unit(u):
    u = (u or "").strip().lower().rstrip(".")
    u = re.sub(r"\s+", " ", u)
    u = UNIT_ALIASES.get(u, u)
    if u in WEIGHT_G or u in VOLUME_ML or u in COUNT_EA:
        return u
    raise CostError(f"unknown unit {u!r}")


def dimension(u):
    if u in WEIGHT_G:
        return "weight"
    if u in VOLUME_ML:
        return "volume"
    return "count"


def to_base(qty, unit):
    """Return (amount in base unit, dimension). Base: g, ml or ea."""
    u = norm_unit(unit)
    table = WEIGHT_G if u in WEIGHT_G else VOLUME_ML if u in VOLUME_ML else COUNT_EA
    return qty * table[u], dimension(u)


def convert(qty, unit, want_dim, density=None):
    """Convert qty+unit into base amount of want_dim, using density g/ml if needed."""
    amt, dim = to_base(qty, unit)
    if dim == want_dim:
        return amt
    if density and {dim, want_dim} == {"weight", "volume"}:
        return amt * density if dim == "volume" else amt / density
    raise CostError(f"cannot convert {unit} ({dim}) to {want_dim} without density_g_per_ml")


def money(s):
    """Parse "$1,234.56", "-$3.00" or accounting-style "($16.00)" to Decimal."""
    s = (s or "").strip().replace("$", "").replace(",", "")
    if not s:
        return None
    neg = s.startswith("(") and s.endswith(")")
    s = s.strip("()").strip()
    try:
        v = D(s)
    except InvalidOperation:
        raise CostError(f"not a number: {s!r}")
    return -v if neg else v


def num(s):
    return money(s)


def key(name):
    return re.sub(r"\s+", " ", (name or "").strip().lower())


def q2(x):
    return x.quantize(D("0.01"), rounding=ROUND_HALF_UP)


def exact(x):
    """Full-precision value for audit columns, trimmed to 7 decimals."""
    return f"{x.quantize(D('0.0000001'), rounding=ROUND_HALF_UP).normalize():f}"


def q4(x):
    return x.quantize(D("0.0001"), rounding=ROUND_HALF_UP)


def read_csv(path, snake=False):
    """Read a CSV, dropping blank rows. snake=True turns "Pack Size" into "pack_size"."""
    with open(path, newline="", encoding="utf-8-sig") as f:
        rows = [r for r in csv.DictReader(f)]

    def k(h):
        h = (h or "").strip()
        return re.sub(r"[^a-z0-9]+", "_", h.lower()).strip("_") if snake else h
    return [{k(h): (v or "").strip() for h, v in r.items() if h is not None}
            for r in rows if any((v or "").strip() for v in r.values() if isinstance(v, str))]


def write_csv(path, header, rows, preamble=None):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        for line in preamble or []:
            w.writerow([line])
        w.writerow(header)
        for r in rows:
            w.writerow(r)


def load_ingredients(path):
    """Return {key: ingredient dict}. Raises CostError listing every bad row."""
    out, errs = {}, []
    for i, r in enumerate(read_csv(path, snake=True), start=2):
        name = r.get("ingredient", "")
        try:
            size, price = num(r.get("pack_size")), money(r.get("pack_price"))
            if size is None or price is None or size <= 0:
                raise CostError("missing pack_size or pack_price (will not guess)")
            unit = norm_unit(r.get("pack_unit"))
            y = num(r.get("yield_pct"))
            y = D("100") if y is None else y
            if not (D("0") < y <= D("100")):
                raise CostError(f"yield_pct {y} must be between 0 and 100")
            dens = num(r.get("density_g_per_ml"))
        except CostError as e:
            errs.append(f"ingredients row {i} ({name}): {e}")
            continue
        if key(name) in out:
            errs.append(f"ingredients row {i}: duplicate ingredient {name!r}")
            continue
        out[key(name)] = {"name": name, "item_code": r.get("item_code", ""),
                          "vendor": r.get("vendor", ""), "pack_size": size,
                          "pack_unit": unit, "pack_price": price, "yield_pct": y,
                          "density": dens, "raw": r}
    if errs:
        raise CostError("\n".join(errs))
    return out


def load_recipes(path):
    """Return {key: recipe dict} preserving file order."""
    recs = {}
    for i, r in enumerate(read_csv(path, snake=True), start=2):
        k = key(r.get("recipe"))
        if not k:
            continue
        yq = num(r.get("batch_yield_qty"))
        rec = recs.setdefault(k, {"name": r["recipe"], "menu_price": money(r.get("menu_price")),
                                  "yield_qty": D("1") if yq is None else yq,
                                  "yield_unit": r.get("batch_yield_unit") or "ea", "lines": []})
        rec["lines"].append({"component": r.get("component", ""), "qty": num(r.get("qty")),
                             "unit": r.get("unit", ""), "row": i})
    return recs


class Coster:
    def __init__(self, ingredients, recipes, q_factor=D("0")):
        self.ing, self.rec, self.q = ingredients, recipes, q_factor
        self._batch = {}

    def batch(self, rk, stack=()):
        """Cost one batch of recipe rk. Returns (total, lines)."""
        if rk in stack:
            raise CostError(f"sub-recipe loop: {' -> '.join(stack + (rk,))}")
        if rk in self._batch:
            return self._batch[rk]
        rec, lines, total, errs = self.rec[rk], [], D("0"), []
        if rec["yield_qty"] <= 0:
            raise CostError(f"{rec['name']}: batch_yield_qty must be greater than 0")
        for ln in rec["lines"]:
            try:
                lines.append(self.line(rec, ln, stack + (rk,)))
                total += lines[-1]["cost"]
            except CostError as e:
                if str(e).startswith("sub-recipe loop") or " / " in str(e):
                    raise
                errs.append(f"{rec['name']} / {ln['component']} (recipes row {ln['row']}): {e}")
        if errs:
            raise CostError("\n".join(errs))
        self._batch[rk] = (total, lines)
        return self._batch[rk]

    def line(self, rec, ln, stack):
        ck, qty = key(ln["component"]), ln["qty"]
        if qty is None or qty <= 0:
            raise CostError(f"qty must be a positive number (got {ln['qty']})")
        if ck in self.ing:
            g = self.ing[ck]
            dim = dimension(g["pack_unit"])
            pack_base = convert(g["pack_size"], g["pack_unit"], dim, g["density"])
            line_base = convert(qty, ln["unit"], dim, g["density"])
            ap = g["pack_price"] / g["pack_size"]
            ratio = line_base / pack_base
            cost = g["pack_price"] * ratio / (g["yield_pct"] / D("100"))
            work = (f"${g['pack_price']} / {g['pack_size']} {g['pack_unit']} = ${q4(ap)}/{g['pack_unit']} AP; "
                    f"/ {g['yield_pct']}% yield = ${q4(ap / (g['yield_pct'] / 100))}/{g['pack_unit']} EP; "
                    f"x {qty} {ln['unit']} ({q4(ratio * g['pack_size'])} {g['pack_unit']}) = ${q4(cost)}")
            return {"component": g["name"], "kind": "ingredient", "qty": qty, "unit": ln["unit"],
                    "cost": cost, "work": work}
        if ck in self.rec:
            sub = self.rec[ck]
            btotal, _ = self.batch(ck, stack)
            dim = dimension(norm_unit(sub["yield_unit"]))
            ybase = convert(sub["yield_qty"], sub["yield_unit"], dim)
            lbase = convert(qty, ln["unit"], dim)
            cost = btotal * lbase / ybase
            work = (f"batch ${q4(btotal)} / {sub['yield_qty']} {sub['yield_unit']} = "
                    f"${q4(btotal / sub['yield_qty'])}/{sub['yield_unit']}; x {qty} {ln['unit']} = ${q4(cost)}")
            return {"component": sub["name"], "kind": "sub-recipe", "qty": qty, "unit": ln["unit"],
                    "cost": cost, "work": work}
        raise CostError(f"component {ln['component']!r} is not in the ingredient list or recipes")

    def plate(self, rk):
        total, lines = self.batch(rk)
        rec = self.rec[rk]
        per = total / rec["yield_qty"]
        return per * (1 + self.q / D("100")), per, lines


def pct(part, whole):
    return part / whole * D("100")
