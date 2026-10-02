---
type: llm
focus: last_message
---

PASS if the reply shows per-line costs for the Chicken Bowl that include chicken 1.1484 (or $1.15), rice 0.21, sauce 0.375 (or $0.38), avocado 0.55 and packaging 0.15, AND shows the chicken yield applied by dividing the as-purchased price by the 80% yield (e.g. $2.45/lb / 0.80 = $3.0625/lb), not multiplying by it.
FAIL if line costs are missing, any of those values differ, or yield is applied as AP x yield.
