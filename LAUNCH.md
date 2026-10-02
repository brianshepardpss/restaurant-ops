# Launch plan: Restaurant Ops

Nothing here is posted without explicit owner approval, one post at a time.

## Positioning

"Your food-cost spreadsheet, done by Claude. Know every plate's cost and
what your last invoice did to it - free, no new subscription."

Contrast (only where a channel allows comparison): back-office suites run
roughly $150-350 per location per month; this is a free plugin that works
on files you already have. Do not name competitors in community posts.

## Audience and where they are

- Owner-operators, chef-owners and GMs of 1-3 location independents on
  Toast, Square or Clover, costing in spreadsheets.
- r/restaurantowners, r/Chefit, r/KitchenConfidential, r/smallbusiness
  (read each sidebar before posting; most ban link-first self-promotion).
- "All Day" newsletter (AI for restaurants) - co-promo / feature pitch.
- Toast Community and Square Seller Community (product-help forums; post
  only where third-party tools are allowed).
- Culinary schools and ACF chapters (costing is core curriculum).
- Podcasts: Restaurant Unstoppable, Restaurant Strategy (guest pitch later).

## Directory listing text

**Restaurant Ops** - Plate costing, invoice price tracking and menu
engineering for independent restaurants. Cost recipes with yield and unit
conversions, see which plates your latest invoice made more expensive, and
sort your menu into stars, plowhorses, puzzles and dogs from a Toast,
Square or Clover sales export. Also drafts an allergen matrix (marks
UNKNOWN where spec sheets are missing) and a costed weekly schedule with
overtime and minor-labor flags. All math in bundled scripts with the
working shown; CSV output; runs on sample data with no account. No
telemetry, no network calls.

Keywords: restaurant, food cost, recipe costing, menu engineering,
allergens, labor.

## Post drafts

### 1. r/restaurantowners (value post, no link in the body)

Title: How I check what a price increase does to each plate (worked example)

> Our chicken thighs went from $98 to $112 a case last week (+14.29%). Here
> is the math I use to see what that does per plate, since a lot of people
> here ask about food cost creeping up.
>
> Chicken Bowl, 6 oz cooked chicken, 80% yield:
> - Before: $98 / 40 lb = $2.45/lb as purchased. Divide by yield (not
>   multiply): $2.45 / 0.80 = $3.0625/lb usable. 6 oz = 0.375 lb -> $1.1484.
> - After: $112 / 40 = $2.80 / 0.80 = $3.50/lb -> $1.3125.
> - Plate went from $2.43 to $2.60, food cost 20.28% -> 21.65% at $12.
>
> The mistake I see most is multiplying by yield, which understates the
> plate. Happy to share the sample costing CSVs if useful.
>
> (I built a free Claude plugin that does this from invoices; I'll put
> the link in a comment only if mods allow it.)

### 2. r/Chefit (craft angle, no link unless asked)

Title: Yield % is where most recipe costing goes wrong

> Quick one for anyone costing recipes: AP price divided by yield, then
> times your EP portion. Flank at $8.80/lb with 88% yield is $10.00/lb on
> the plate, so a 6 oz portion is $3.75, not $3.30. Across a menu that
> gap is real money. I put together a free costing tool that shows the
> arithmetic line by line; ask and I'll share it.

### 3. "All Day" newsletter (email pitch to the editor)

Subject: Free, file-based food-cost tool for indies (Claude plugin)

> Hi - I read All Day for the AI-in-restaurants coverage. I built a free,
> open-source Claude plugin for independent operators: it costs recipes
> (yield and unit conversions, line-by-line working), shows which plates a
> new invoice made more expensive, and runs menu engineering from a Toast
> or Square item export. It works on files, no POS integration, and every
> number comes from a script you can audit. The demo runs on a fictional
> restaurant in a few minutes. If it is useful to your readers I would be
> glad to send a walkthrough or the sample CSV outputs. No affiliation with any
> POS vendor.

### 4. Toast Community / Square Seller Community (only where tools are allowed)

Title: Menu engineering from your Items Detail / ItemSelectionDetails export

> If you want stars/plowhorses/puzzles/dogs from your own sales, the
> export already has what you need: item, qty, net sales. Combine with
> plate cost; popularity threshold is 70% of 1/(number of items), margin
> threshold is the weighted average contribution margin. Voids and refunds
> need to come out first. I made a free Claude plugin that does this from
> the CSV (not affiliated with Toast or Square); link on request.

## Day-30 signal and thresholds

Good (keep investing): >= 150 installs, >= 25 users running plate-cost on
their OWN recipes (inferred from /request issues and community replies, not
telemetry), >= 10 inbound /request or GitHub issues asking for a specific
POS/vendor format or feature (prep pars, Square connector), and 3+
unsolicited community posts or screenshots.

Kill / pivot: < 30 installs, or only demo usage.

Measured via GitHub traffic, stars, clones and issues on
brianshepardpss/restaurant-ops (no telemetry).
