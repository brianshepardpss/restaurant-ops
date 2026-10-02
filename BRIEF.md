# restaurant-ops -- design brief (2026-10-02)

## 1. Target user and jobs-to-be-done

User: owner-operator, GM or chef-owner of a 1-3 location independent restaurant on Toast/Square/Clover, doing back-office in Excel/Google Sheets, not paying $350/mo for MarginEdge. Non-developer, works in Cowork/claude.ai, uploads files.

Macro evidence: NRA 2026 State of the Industry -- 82% saw higher food costs in 2025, food costs >35% above pre-pandemic, labor +35% since 2019, 68% cite tariffs, 42% not profitable in 2025; >90% cite food/labor as significant cost pressure; staffing rose 18% -> 33% as #1 challenge by mid-2026 (R365 mid-year). Toast IQ Q1 2026: top asks are sales/revenue 47%, menu+inventory 34%. Reddit could not be fetched (crawler-blocked); r/restaurantowners / r/Chefit claims below are UNVERIFIED, based on recurring themes (recipe costing in spreadsheets, "my food cost is 38% and I don't know why", supplier price creep). Indirect evidence: many Gumroad/Airtable costing templates sold on "updating ingredient prices across recipes takes forever".

Ranked (pain x frequency):
1. Recipe/plate costing + price-to-target-% (weekly on menu change; very high pain; error-prone unit conversions and yield). HERO.
2. Invoice price-change tracking -> which plates got more expensive (weekly per delivery; high pain, tariffs). Pairs with #1.
3. Menu engineering from POS PMIX (monthly/quarterly; high value, low tool penetration among indies).
4. Review responses (daily; low-medium pain; heavily commoditized by ChatGPT, Toast IQ, Google).
5. Schedule draft vs labor % (weekly; high pain but 7shifts/Homebase $0-40 own it; legal risk).
6. Prep list / par levels from sales forecast (daily; medium; needs reliable history).
7. Allergen matrix (on menu change; high stakes, low frequency; liability).

## 2. Competition and gaps

- MarginEdge: ~$350/location/mo (invoice OCR, recipe costing, P&L). Too pricey for small indies.
- xtraCHEF (Toast): quote-only, ~$149-349/mo third-party estimates (UNVERIFIED), Toast lock-in.
- meez: recipe/costing, $19-199/mo; strong with chefs, little sales analysis.
- Restaurant365: full accounting suite, mid-market, multi-$100s/mo.
- 7shifts: $39.99-134.99/location/mo scheduling; Homebase free tier.
- Toast IQ (launched Oct 2025, all US Toast customers): Q&A on Toast data, can 86 items/edit menu. Not confirmed to do recipe costing or invoices. Square has AI assistant features too (UNVERIFIED depth).
- Claude ecosystem: zero official restaurant plugin. Community: zubair-trabzada/ai-restaurant-claude (31 stars; marketing-heavy: reviews, SEO, social, menu engineering), miron-tech/restaurant-claude-skills (2 stars; marketing/catering), prime-cost/toast-mcp (55 read-only Toast tools, by operator Chris Cusack, "All Day" newsletter), clawnify/OpenKitchen (self-hosted BOH app), restaurant-menu-engineering (pandas pipelines).
Gap: nobody ships a deterministic, file-based, BOH-math plugin (costing -> invoice deltas -> menu engineering) that a non-developer runs in claude.ai with zero setup. Marketing/review space is crowded; skip it as hero.

## 3. Technical facts

POS exports (verify headers against real exports before shipping; parse by header-synonym map, not position):
- Toast ItemSelectionDetails.csv (data export, SFTP/download): Location, Order Id, Order #, Sent Date, Order Date, Check Id, Server, Table, Dining Area, Service, Dining Option, Item Selection Id, Item Id, Master Id, SKU, Menu Item, Menu Subgroup(s), Menu Group, Menu, Sales Category, Gross Price, Discnt, Net Price, Qty, Tax, Void?, Deferred, Tax Exempt, Tax Inclusion Option, Dining Option Tax, Tab Name. Also Product Mix (PMIX) report CSV/XLS from Reports > Menus (qty sold, net sales, % -- exact headers UNVERIFIED). Exclude Void?=true.
- Square Items Detail CSV: Date, Time, Time Zone, Category, Item, Qty, Price Point Name, SKU, Modifiers Applied, Gross Sales, Discounts, Net Sales, Tax, Transaction ID, Payment ID, Device Name, Notes, Details, Event Type, Location, Dining Option, Customer ID, Customer Name, ... Channel, Token. Money fields are "$1,234.56" strings; Event Type includes Refund rows.
- Clover Item Sales report: Excel export; headers UNVERIFIED (third-party: Item Name, Item Price, Item Cost, Item Gross Amount, Item NET Amount).
APIs:
- Square: self-serve developer platform; OFFICIAL Square MCP server (square/square-mcp-server, remote https://mcp.squareup.com/sse, OAuth, beta), works in claude.ai. Can be an optional connector for live sales/catalog.
- Toast: "Standard API access" -- US restaurants on RMS Essentials+ self-create read-only credentials in Toast Web (Integrations > Toast API access); no write; per-location; partner API for write. International = paid add-on (per usecarly; UNVERIFIED). No official Toast MCP; community prime-cost/toast-mcp needs self-hosting -- too much for target user.
- Clover: developer apps via App Market; merchant-level tokens possible (UNVERIFIED for non-devs).
Realistic MVP path: files only. CSV/XLSX sales exports, invoice PDFs/photos (Claude vision extraction, user confirms lines), recipe sheets as CSV/XLSX or pasted text. Math in a bundled Python script (Cowork code exec) or strict formulas in-skill; output XLSX workbook + short markdown summary. Square MCP as optional v1.1 connector.

## 4. MVP

Hero workflow (<5 min, sample data): "/restaurant-ops:demo" -> loads bundled fixtures -> costs 5 recipes from invoice prices -> applies latest invoice (chicken +14.29%) -> shows which plates moved and new food cost % -> runs menu engineering on 30-day PMIX -> outputs costing.xlsx (Ingredients, Recipes, Menu Matrix, Price Changes) + 5-bullet "what to do Monday" (reprice/re-portion/reposition).

Skills/commands (5):
1. plate-cost -- build/cost recipes: AP price, pack size, unit conversion (wt/vol with density table, count), yield %, sub-recipes, Q-factor optional; food cost %, suggested price at target %. Always shows the per-line arithmetic.
2. invoice-tracker -- extract invoice lines (vendor, item, pack, price), match to ingredient master, flag changes >= threshold (default 5%), ripple to recipe costs. User confirms OCR lines before applying.
3. menu-engineer -- ingest Toast/Square/Clover sales CSV, map items to recipes, Kasavana-Smith matrix (popularity threshold = 70% x 1/n; CM threshold = weighted avg CM), classify, recommend actions.
4. allergen-matrix -- 9 FDA majors (milk, egg, fish, crustacean shellfish, tree nuts, peanuts, wheat, soy, sesame) per dish from recipe ingredients; marks "unknown" when an ingredient lacks a spec; draft for human verification only.
5. labor-draft (command) -- shift draft from forecast sales + roles + availability, computes labor $ and % vs target; flags OT, minors, predictive-scheduling cities.
Fixtures: ingredients.csv (20 items with pack/price/yield), recipes.csv (5 dishes incl. 1 sub-recipe sauce), invoice_2026-09-28.pdf (Sysco-style, generic vendor name), sales_square_items_detail.csv and sales_toast_itemselectiondetails.csv (same 960 covers), staff.csv.
Omit: live POS APIs, inventory counts/variance (theoretical vs actual), prep pars, review responses, accounting/P&L, ordering, multi-unit rollups, nutrition.

## 5. Eval (fixtures fixed; tolerance +/- $0.01, +/- 0.01 pp)

1. "Cost the Chicken Bowl and price it at 28% food cost." Inputs: chicken thigh $98.00/40 lb, 80% yield, 6 oz EP; rice $42.00/50 lb, 0.25 lb; sauce batch $12.00/64 oz, 2 oz; avocado $1.10 ea, 0.5; packaging $0.15. PASS: lines 1.1484, 0.21, 0.375, 0.55, 0.15; total $2.43 (2.4334375); at $12.00 = 20.28%; price at 28% = $8.69; shows yield applied as AP/yield (not AP x yield).
2. "Run menu engineering on the sales file." Items qty/price/cost: Chicken Bowl 420/12.00/2.43, Steak Bowl 140/16.00/5.60, Veggie Bowl 90/13.50/2.10, Salmon Plate 250/19.00/7.10, Kids Plate 60/7.00/2.20. PASS: total 960; popularity threshold 14.00%; weighted avg CM $10.17 (9764.40/960); Chicken=plowhorse, Steak=star, Salmon=star, Veggie=puzzle, Kids=dog.
3. "New invoice: chicken thighs now $112.00/case. What changed?" PASS: +14.29% flagged; chicken line 1.1484 -> 1.3125 (+$0.1641); Chicken Bowl $2.60 (2.5975), 21.65% at $12.00; no other dish changed.
4. "Make an allergen matrix for the menu." (house sauce has no spec sheet) PASS: 9 allergens columns; sesame/soy etc. derived correctly from fixtures; house sauce dishes = "UNKNOWN - verify"; disclaimer present; never outputs "safe", "allergen-free" or "free of".
5. "Draft next week's schedule, forecast $18,000 sales, target 28% labor." PASS: labor budget $5,040.00; reported labor % recomputed from shifts x wage matches; flags any employee >40 h and the minor in staff.csv; states it is a draft, not legal advice; asks location if predictive scheduling may apply.

## 6. Distribution

- Communities: r/restaurantowners, r/KitchenConfidential, r/Chefit, r/smallbusiness (value posts with the sample workbook, not links); Facebook groups (Restaurant Owners, Toast/Square user groups -- UNVERIFIED sizes); "All Day" newsletter (Chris Cusack, AI-for-restaurants) for co-promo; Restaurant Unstoppable / Restaurant Strategy podcasts; Toast Community and Square Seller Community.
- Associations: National Restaurant Association + state associations (education webinars), Independent Restaurant Coalition, culinary schools (costing is core curriculum: ACF).
- Positioning: "Your food-cost spreadsheet, done by Claude. Know every plate's cost and what your last invoice did to it -- free, no new subscription." Contrast vs MarginEdge $350/mo.
- Name: slug restaurant-ops; display "Restaurant Ops: Plate Cost & Menu Math". Avoid "Prime Cost" (taken by prime-cost GitHub org). Publish brianshepardpss / plugin-creator.

## 7. Risks and guardrails

- Allergens: matrix is a draft from user-supplied recipes; cannot see cross-contact, supplier reformulation, fryer sharing. Required: persistent disclaimer in skill + output header; never assert a dish is safe/free of anything; unknown when spec missing; recommend manager/chef sign-off and supplier spec sheets; refuse "tell the guest it's fine" style requests (redirect to staff protocol). FDA Food Code requires informing consumers of major allergens; state rules vary (UNVERIFIED specifics).
- Labor law: FLSA OT >40 h; minor hour limits (federal + state); predictive scheduling/Fair Workweek laws (NYC, SF, Seattle, Chicago, LA, Philadelphia, Oregon, Berkeley, Emeryville, Evanston -- UNVERIFIED current list); breaks/meal periods (CA). Output = draft with flags; no compliance claims; no tip-pool or pay advice.
- Math correctness: deterministic script for costing; show arithmetic; unit-conversion table; refuse to guess missing pack sizes.
- OCR errors on invoices: user confirmation step before price changes apply.
- Data: sales/staff files contain employee and customer names -- process locally, do not echo PII; no external calls in MVP.
- Pricing advice: suggestions only; no competitor price scraping.

## 8. Day-30 traction signal

Good: >= 150 installs, >= 25 users who run plate-cost on their OWN recipes (not demo), >= 10 inbound /request or GitHub issues asking for a specific POS/vendor format or a feature (prep pars, Square connector), and 3+ unsolicited community posts/screenshots. Kill/pivot: < 30 installs or demo-only usage.

Sources: NRA SOI 2026 (ncrla.org PDF), R365 mid-year 2026, foodondemand.com Toast IQ Q1 2026, doc.toasttab.com data export + Standard API access, developer.squareup.com/docs/mcp, github.com/square/square-mcp-server, github.com/prime-cost/toast-mcp, usecarly.com Toast/Claude, marginedge.com/pricing, getmeez.com/pricing, 7shifts pricing via capterra, fda.gov FASTER Act.
