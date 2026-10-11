# 02 · Analysis & Visualisation Guide

How to turn the analysis into a Power BI dashboard that a Chief Commercial Officer can act on in five minutes. Measure names refer to `03_DAX_Measures.md`; findings refer to `01_EDA.md`.

---

## 1. Design principles

1. **Decision first.** Every page answers one question the CCO has to decide. If a visual does not support a decision, cut it.
2. **Action titles.** A page or chart title states the finding ("London earns 8.5% margin on 1.8× the rent"), not the content ("Margin by region").
3. **One message per page**, a maximum of six visuals, and one highlighted colour per chart so the eye lands on the answer.
4. **Show the £.** Wherever a finding has a size, show it in pounds per year.
5. **Be honest.** Label confidence and data limits on the page, not in a footnote nobody reads.

---

## 2. Canvas and style system

| Item | Setting |
|---|---|
| Page size | 16:9, 1280 × 720 px |
| Background | Cream `#FAF6F0`; visuals on white cards with 1 px `#E5DDD0` border, 6 px radius |
| Margins / gutter | 24 px outer, 16 px between visuals (snap to an 8 px grid) |
| Header band | Top 64 px: page title (Segoe UI Semibold 22 pt, Espresso), one-line subtitle (11 pt, grey) |
| Font | Segoe UI throughout. Visual titles 12 pt semibold, labels 10 pt minimum |
| Theme | Import `powerbi/sunrise_theme.json` (View → Themes → Browse for themes) |

**Colour roles (use consistently on every page)**

| Role | Hex | Use |
|---|---|---|
| Espresso | `#3B2314` | Titles, benchmark lines |
| Caramel | `#C98B4A` | Default series ("everything else") |
| Sunrise orange | `#F28C28` | The one thing to look at, selected state |
| Teal | `#2A7F7F` | Good / above benchmark |
| Brick red | `#B3382C` | Bad / below benchmark / London in the cost charts |
| Grey | `#8C8C8C` | Prior year, secondary text |
| Cream | `#FAF6F0` | Canvas |

**Colour rules:** good is teal and bad is red, always paired with an icon or label so the report is readable by colour-blind viewers. Never use more than three colours in one chart.

**Number formats:** £ in millions `£0.0,,"m"`; £ in thousands `£#,0,"k"`; percentages one decimal; multiples two decimals.

---

## 3. Report map

| # | Page | Question | Headline (action title) |
|---|---|---|---|
| 1 | Executive Summary | Where do we stand and what should we do? | "A stable £90m estate, leaking profit through costs, not sales" |
| 2 | Where Profit Leaks | What separates good stores from bad ones? | "Rent and staffing drive margin; revenue does not" |
| 3 | Store Watchlist | Which stores need review, and why? | "9 stores need review: 5 have a rent problem, 4 a labour problem" |
| 4 | Loyalty | Is loyalty worth more investment? | "Loyalty costs £1.7m and shows no spend uplift" |
| 5 | Mix & Rhythm | How should we plan staffing and stock? | "Plan for the week, not the season" |
| 6 | Recommendations & Data Notes | What do we do next, and how sure are we? | "Six actions, sized in pounds" |
| 7 | Store Profile (drill-through, hidden) | What is going on in this store? | Store name + flag |

**Navigation:** a slim button bar (page navigator visual) under the header on every page. Add a "Reset filters" button bound to a bookmark.

**Slicers (synced across pages 1-5):** Year (`dim_date[year]`), Region (`dim_store[region]`), Location Type (`dim_store[location_type]`). Keep them in a left or top strip so they do not compete with content. Do not slice on `store_format` (only two hub stores).

---

## 4. Page-by-page specification

### Page 1 · Executive Summary

**Layout (1280 × 720)**

```
┌───────────────────────────────────────────────────────────┐
│ Title / subtitle                              [slicers]   │
├───────┬───────┬───────┬───────┬───────┬───────────────────┤
│ KPI 1 │ KPI 2 │ KPI 3 │ KPI 4 │ KPI 5 │ KPI 6             │
├───────┴───────┴───────┼───────┴───────┴───────────────────┤
│ Monthly margin trend  │ Net margin by region (bar)        │
│ 2023 vs 2024          │ London highlighted                │
├───────────────────────┴───────────────────────────────────┤
│ "What this means" text panel: 3 findings + 1 recommendation│
└───────────────────────────────────────────────────────────┘
```

| Visual | Type | Fields | Notes |
|---|---|---|---|
| KPI 1-6 | Card (new) with reference label | `Revenue`, `Net Profit`, `Net Margin %`, `Priority Review Stores`, `Loyalty Redemption Cost`, `Revenue Growth %` | Add the 2023 to 2024 change as the reference label; red/teal font by sign |
| Margin trend | Line chart | Axis `dim_date[Month Label]`; Legend `dim_date[year]`; Values `Net Margin %` | 2023 grey, 2024 orange; no gridlines; message: the pattern does not repeat |
| Region bars | Clustered bar | Axis `dim_store[region]`, Values `Net Margin %`, sorted ascending | Conditional colour: London red, above-estate teal, else caramel; add average line at `Net Margin %` (all stores) |
| Insight panel | Text box | Static text | Three lines of finding, one of recommendation; update if filters change the story, or mark "full period" |

### Page 2 · Where Profit Leaks

| Visual | Type | Fields | Notes |
|---|---|---|---|
| Staffing vs margin | Scatter | X `Staffing % of Revenue`; Y `Net Margin %`; Details `dim_store[store_name]`; Size `Avg Monthly Revenue per Store`; Legend `dim_store[region]` grouped as London / Other | Add a trend line (Analytics pane); label South London Corner. The hero chart of the report |
| Rent quartile | Clustered column | Axis `dim_store[Rent Quartile]`; Values `Net Margin %`; tooltip `Avg Monthly Revenue per Store` | Teal to red gradient; title: "Same revenue, 7.6 points less margin in the highest-rent quartile" |
| Location type | Clustered column | Axis `dim_store[location_type]`; Values `Net Margin %`; second visual or tooltip with `Store Count` | Flag Train-Station "n = 2" with a data label note |
| Cost waterfall | Waterfall | Category: Revenue, COGS, Staffing, Rent, Loyalty, Net Profit; values from the matching measures (use a small disconnected table for category order) | Shows where each £1 of revenue goes |
| Region matrix | Matrix | Rows `dim_store[region]`; Values `Store Count`, `Net Margin %`, `Rent % of Revenue`, `Staffing % of Revenue`, `Loss Share %` | Data bars on rent and staffing; conditional fill on margin |

Key callout: "London: £11.7k average rent vs £6.5k estate, worth about £0.6m a year if London matched peer margin" (`Margin Gap to Peers (£/yr)` with Region = London).

### Page 3 · Store Watchlist

| Visual | Type | Fields | Notes |
|---|---|---|---|
| Flag summary | 3 cards | `Priority Review Stores`; stores with flag Watch; Healthy | Sets scope in one glance |
| Watchlist table | Table | `store_name`, `region`, `Store Flag`, `Net Margin %`, `Loss Store-Months`, `Staffing % of Revenue`, `Rent % of Revenue`, `Primary Driver`, `Net Profit Change 24 vs 23` | Filter visual: `Store Flag` is not Healthy; sort by `Store Flag Sort` then margin. Conditional icons on the flag; red font on negative change |
| Quadrant scatter | Scatter | X `Avg Monthly Revenue per Store`; Y `Net Margin %`; Details `store_name`; Legend `Store Flag` | Shows "revenue is similar, margin is not" |
| Year-on-year movers | Bar | Top 8 / Bottom 8 on `Net Profit Change 24 vs 23` (Top N filter, two visuals or a diverging bar) | Teal for gains, red for losses |
| Driver split | Donut or stacked bar | `Primary Driver` counts for flagged stores | Supports the "5 rent / 4 labour" headline |

**Drill-through:** configure `Store Profile` with `dim_store[store_name]` as the drill-through field. It shows that store's monthly margin line vs estate, cost mix (staffing/rent/COGS %), loyalty adoption, and its two-year profit change. Add a "Right-click, Drill through" hint on the table.

### Page 4 · Loyalty

| Visual | Type | Fields | Notes |
|---|---|---|---|
| KPI strip | Cards | `Loyalty Redemption Cost`, `Redemption % of Member Revenue`, `Member Spend Multiple`, `Break-even Uplift %` | The multiple reads 1.00: "members behave like everyone else" |
| Adoption vs member share | Scatter | X `Avg Adoption Rate`; Y `Member Revenue %`; Details `store_name` | Add a trend line (Analytics pane): it sits on the diagonal (y ≈ x), which means members spend like non-members. Label it with a text box |
| Basket size by adoption | Column | Axis `dim_store[Adoption Band]`; Values `ATV (£)` | Flat bars; axis starts at 0 |
| Cost per member £ | Column | Axis `dim_store[Adoption Band]`; Values `Redemption % of Member Revenue` | Low-adoption stores pay 18p per member £ vs 3.6p |
| Scenario | Line + slicer | Axis `Uplift Assumption` values; Values `Programme Net Value (scenario)`; slicer on the parameter | The break-even line crosses zero at +10.3%; observed is about 0% |
| Caveat box | Text | Static | "No member-level or baseline data, so incrementality cannot be proven. This shows no visible uplift in spend per head." |

### Page 5 · Mix & Rhythm

| Visual | Type | Fields | Notes |
|---|---|---|---|
| Revenue mix over time | 100% stacked column | Axis `dim_date[Year-Month]` or quarter; Values four share measures | Message: stable; food is not growing |
| Category margin | Bar | Axis `dim_product[product_category]`; Values `Catalogue Margin %` | Highlight Retail-Beans (lowest) in red. Note: catalogue margin overstates real margin |
| Weekday pattern | Column | Axis `dim_date[day_of_week]` (sorted Mon-Sun); Values `Avg Revenue per Store-Day` | Weekend bars in espresso, weekdays in caramel |
| Calendar effect | Column | Axis `dim_date[uk_trading_calendar]`; Values `Avg Revenue per Store-Day` | Bank holiday in red: −34% |
| Seasonality heat grid | Matrix | Rows `dim_date[year]`; Columns `Month Label`; Values `Net Margin %`; colour scale | The pattern flips between years |
| Driver note | Text | Static | "Weekend drop is footfall, not basket: ATV is about £7.5 every day and conversion about 75%" |

Add a small footer on this page: "Daily figures are a 20% sample. Used for patterns, not totals."

### Page 6 · Recommendations & Data Notes

Left two thirds: a table of six actions (action, value at stake, owner, confidence). Right third: a "Data notes" panel listing the five issues that matter (status labels recomputed, daily table is a sample, only two store formats, store-level profit only, loyalty incrementality untestable). Link to the GitHub repo and add your name/handle.

---

## 5. Interactions and polish

- **Edit interactions:** disable cross-filtering from KPI cards and text; keep it on charts so a click on London filters the page.
- **Tooltips:** create one tooltip page (320 × 240) for stores showing the margin trend line and cost split, and apply it to the watchlist scatter and table.
- **Bookmarks:** "Reset", "London focus" (Region = London), "Priority stores" (flag filter). Use them on buttons so the story can be told in a click.
- **Conditional formatting rules** for `Net Margin %`: below 10% red; 10% to estate average sand; above estate average teal.
- **Sort orders:** weekday Mon-Sun, months Jan-Dec, status by `Status Sort`; never alphabetical.
- **Alt text** on every visual (one sentence stating the insight).
- **Reading order** (Selection pane): title, KPIs, main chart, supporting charts, notes.
- **Mobile layout:** build a phone view for page 1 (KPIs, margin by region, insight text).

---

## 6. Build order

1. Load data, set types, build the model and relationships (`03_DAX_Measures.md` sections 1-2).
2. Add calculated columns, then the measures. Run the validation checklist (section 8 of the DAX file) before drawing anything.
3. Import the theme; build page 2 first (it holds the strongest chart) and page 3 (the actionable one).
4. Build pages 4 and 5, then the executive summary last, once you know the story.
5. Apply navigation, slicer sync, bookmarks, tooltips, alt text.
6. Run the QA list below.

---

## 7. QA checklist before you publish

- [ ] Every KPI matches the validation table in the DAX guide (full period, no slicers)
- [ ] No £ total is built from `fact_daily_sales`
- [ ] No visual averages a `*_pct` column
- [ ] Weekday/holiday attributes are not combined with monthly measures
- [ ] Each page title states a finding, and each finding has a number
- [ ] Caveats (sample, n = 2 hubs, no loyalty baseline) are visible on the relevant pages
- [ ] Colour roles are consistent; red/teal always have an icon or label
- [ ] Slicers behave: Year, Region and Location Type sync; Reset works
- [ ] Fonts 10 pt or larger; no text overflow; alignment on the grid
- [ ] File opens on page 1 with no filters applied

---

## 8. Submitting the challenge

1. Export the dashboard as PDF and screenshots (pages 1-5 at full width) into `/dashboard` in the repo.
2. Publish to the Power BI Service and use "Publish to web" for a public link if the challenge rules allow it.
3. Lead the post/submission with the headline, not the tool: "Costs, not sales, decide which Sunrise stores make money. Here is the £ size of the opportunity."
4. Show one chart (the staffing-vs-margin scatter) as the preview image.
5. Link the repo and mention the data-quality audit; it signals rigour.
