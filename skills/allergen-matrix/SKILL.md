---
name: allergen-matrix
description: Use when a restaurant needs an allergen chart, allergen matrix or allergen menu, or says "which dishes have nuts / gluten / dairy", "make an allergen chart for the staff", "what allergens are in the menu", or "update our allergen sheet after the menu change". Takes recipes plus supplier spec sheets; returns a DRAFT matrix of the 9 major US food allergens per dish as CSV, marking UNKNOWN wherever a spec sheet is missing. Draft for manager verification only.
---

# Allergen matrix draft (9 major US food allergens)

Allergens: milk, egg, fish, crustacean shellfish, tree nuts, peanuts, wheat,
soy, sesame. The matrix comes from `scripts/allergen_matrix.py` (this
skill's directory). Never decide an allergen cell yourself.

## 1. Inputs

- Demo: `--sample`.
- The user's recipes (plate-cost format, `../plate-cost/formats.md`) and an
  `allergen_specs.csv` like `../../samples/allergen_specs.csv`: one row per
  purchased ingredient, Y/N per allergen, `may_contain` for precautionary
  statements, plus the spec sheet source and date.
- Build the specs file ONLY from supplier spec sheets, product labels or
  the user's statements about a specific product. Do not fill cells from
  general knowledge ("soy sauce usually has wheat"). If a spec is missing,
  leave the ingredient out of the specs file; the script then marks the
  dish UNKNOWN. You may tell the user which allergens such products often
  contain as a reason to get the spec sheet, never as a cell value.

## 2. Run

```
python3 <this skill dir>/scripts/allergen_matrix.py --recipes recipes.csv \
  --specs allergen_specs.csv --out restaurant-ops-output
```

## 3. Ask about the kitchen

Before reporting, ask (or note as open items if the user is not around):
shared fryer oil, shared grill/plancha, shared prep boards or scoops,
garnishes and sauces added at the pass, and recent supplier substitutions.
The script cannot see any of these. Put each "yes" in the report as a
cross-contact note against the affected dishes; never remove a CONTAINS.

## 4. Report

Start every answer with this line, verbatim:

> DRAFT for manager/chef verification. Built only from the recipes and spec sheets on file; it cannot see cross-contact, shared equipment, substitutions or supplier reformulation.

Then the matrix (CONTAINS / MAY CONTAIN / UNKNOWN - verify / not declared),
then:

- **Missing spec sheets:** each ingredient and the dishes it makes UNKNOWN.
- **Cross-contact notes:** from step 3.
- **Next steps:** get the missing spec sheets, have the chef or manager
  check every row against current labels, sign and date it, re-run after
  any recipe or supplier change.

Files: `allergen_matrix.csv` (the disclaimer is in its first lines; keep it
there if the user copies the table elsewhere).

## Rules (no exceptions)

- Never write that a dish is "safe", "allergen-free", "free of" anything,
  "gluten-free", "nut-free" or "OK for" an allergy. "not declared" means
  only that no spec sheet on file declares it.
- If asked "can I tell the guest it's fine?", "is this safe for a peanut
  allergy?" or to write guest-facing "free-from" labels: decline that part.
  Say the matrix is a staff draft, point to the restaurant's allergy
  protocol (manager to table, check labels, clean equipment, communicate to
  the line) and offer to show what the specs on file declare.
- UNKNOWN is never upgraded to "not declared" without a spec sheet.
- This is not legal or medical advice; local labeling rules vary.
