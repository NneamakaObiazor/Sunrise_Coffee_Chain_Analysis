# 03 · Data Model & DAX Measures

Power BI semantic model for the Sunrise Coffee Chain dashboard. Every measure here is paired with an expected value in section 8 so you can check your model against the Python analysis.

---

## 1. Load the data (Power Query)

Load the five CSVs, then set data types:

| Table | Column | Type |
|---|---|---|
| `dim_date` | `full_date` | Date |
| `dim_date` | `is_weekend`, `is_uk_bank_holiday` | True/False |
| `dim_store` | `loyalty_adoption_rate` | Decimal |
| `fact_store_monthly_profitability` | all `_gbp` columns, `*_pct` columns, `avg_*` | Decimal |
| `fact_daily_sales` | all `_gbp` columns | Decimal |
| all tables | `*_id`, counts | Whole number |

Do **not** delete rows or "fix" values in Power Query. The data issues are handled in DAX so the logic is visible to reviewers.

---

## 2. Model

```
                    dim_date
                   (date_id, full_date)
                   /               \
                  1                 1
                  |                 |
                  *                 *
fact_store_monthly_profitability    fact_daily_sales
        *                                *        *
        |                                |        |
        1                                1        1
     dim_store ───────────────────────────┘     dim_product
     (store_id)                                 (product_id)
```

| Relationship | Cardinality | Filter direction |
|---|---|---|
| `dim_date[date_id]` → `fact_store_monthly_profitability[date_id]` | One-to-many | Single (dim to fact) |
| `dim_date[date_id]` → `fact_daily_sales[date_id]` | One-to-many | Single |
| `dim_store[store_id]` → `fact_store_monthly_profitability[store_id]` | One-to-many | Single |
| `dim_store[store_id]` → `fact_daily_sales[store_id]` | One-to-many | Single |
| `dim_product[product_id]` → `fact_daily_sales[product_id]` | One-to-many | Single |

**Rules that prevent wrong numbers**

1. The monthly fact's `date_id` is the **first day of the month**. Never put `day_of_week`, `is_weekend` or `is_uk_bank_holiday` on a visual that uses monthly measures: they would only see 1st-of-month rows.
2. `fact_daily_sales` is a **sample** (about 20% of store-days). Use it only for ratios and averages, never for £ totals. All £ measures come from the monthly fact.
3. Mark `dim_date` as a date table on `full_date`. The table ends on 30 Dec 2024, so prior-year logic below uses `year` rather than `DATEADD`.
4. Create an empty table `_Measures` and keep all measures there, in display folders.

---

## 3. Calculated columns

### dim_date

```dax
Day Type = IF ( dim_date[is_weekend], "Weekend", "Weekday" )

Bank Holiday Label = IF ( dim_date[is_uk_bank_holiday], "Bank holiday", "Normal day" )

Month Label = LEFT ( dim_date[month_name], 3 )
-- Set "Sort by column" to dim_date[month_number]

Year-Month = dim_date[year] & "-" & FORMAT ( dim_date[month_number], "00" )
```

### fact_store_monthly_profitability

The supplied `profitability_status` contradicts its own thresholds on 600 rows, so recompute it:

```dax
Status (Recomputed) =
VAR m = fact_store_monthly_profitability[net_profit_margin_pct]
RETURN
    SWITCH (
        TRUE (),
        m > 0.20,   "Highly-Profitable",
        m >= 0.08,  "Profitable",
        m >= -0.02, "Break-Even",
        m >= -0.15, "Loss-Making",
        "Structural-Loss"
    )

Status Sort =
SWITCH (
    fact_store_monthly_profitability[Status (Recomputed)],
    "Highly-Profitable", 1,
    "Profitable",        2,
    "Break-Even",        3,
    "Loss-Making",       4,
    "Structural-Loss",   5
)
-- Set "Sort by column" on Status (Recomputed) to Status Sort

Is Loss Month =
IF (
    fact_store_monthly_profitability[Status (Recomputed)]
        IN { "Loss-Making", "Structural-Loss" },
    1, 0
)
```

### dim_store (static two-year bands)

These use the full 24 months and do not respond to date slicers; that is intentional, so a store keeps one band.

```dax
Avg Monthly Rent (24m) =
CALCULATE ( AVERAGE ( fact_store_monthly_profitability[monthly_rent_gbp] ) )

Rent Quartile =
VAR r  = dim_store[Avg Monthly Rent (24m)]
VAR q1 = PERCENTILE.INC ( dim_store[Avg Monthly Rent (24m)], 0.25 )
VAR q2 = PERCENTILE.INC ( dim_store[Avg Monthly Rent (24m)], 0.50 )
VAR q3 = PERCENTILE.INC ( dim_store[Avg Monthly Rent (24m)], 0.75 )
RETURN
    SWITCH (
        TRUE (),
        r <= q1, "Q1 (lowest rent)",
        r <= q2, "Q2",
        r <= q3, "Q3",
        "Q4 (highest rent)"
    )

Adoption Band =
VAR a  = dim_store[loyalty_adoption_rate]
VAR q1 = PERCENTILE.INC ( dim_store[loyalty_adoption_rate], 0.25 )
VAR q2 = PERCENTILE.INC ( dim_store[loyalty_adoption_rate], 0.50 )
VAR q3 = PERCENTILE.INC ( dim_store[loyalty_adoption_rate], 0.75 )
RETURN
    SWITCH (
        TRUE (),
        a <= q1, "1 Low",
        a <= q2, "2",
        a <= q3, "3",
        "4 High"
    )
```

---

## 4. Core P&L measures (monthly fact)

Display folder: `1 Profitability`

```dax
Revenue = SUM ( fact_store_monthly_profitability[total_monthly_revenue_gbp] )

COGS = SUM ( fact_store_monthly_profitability[total_monthly_cogs_gbp] )

Rent = SUM ( fact_store_monthly_profitability[monthly_rent_gbp] )

Staffing = SUM ( fact_store_monthly_profitability[monthly_staffing_cost_gbp] )

Loyalty Redemption Cost = SUM ( fact_store_monthly_profitability[loyalty_redemption_cost_gbp] )

Net Profit = SUM ( fact_store_monthly_profitability[net_profit_gbp] )

-- Always revenue-weighted. Never AVERAGE the margin % column: a few
-- tiny-revenue months have margins of -339% and distort simple averages.
Net Margin % = DIVIDE ( [Net Profit], [Revenue] )

Gross Margin % (P&L) = DIVIDE ( [Revenue] - [COGS], [Revenue] )

Staffing % of Revenue = DIVIDE ( [Staffing], [Revenue] )

Rent % of Revenue = DIVIDE ( [Rent], [Revenue] )

Loyalty Cost % of Revenue = DIVIDE ( [Loyalty Redemption Cost], [Revenue] )

Store Count = DISTINCTCOUNT ( fact_store_monthly_profitability[store_id] )

Store-Months = COUNTROWS ( fact_store_monthly_profitability )

Months in Context = DISTINCTCOUNT ( fact_store_monthly_profitability[month_id] )

Years in Context = MAX ( 1, DISTINCTCOUNT ( dim_date[year] ) )

Avg Monthly Revenue per Store = DIVIDE ( [Revenue], [Store-Months] )

Avg Revenue per Sq Ft = AVERAGE ( fact_store_monthly_profitability[revenue_per_sqft_gbp] )

Avg Daily Footfall = AVERAGE ( fact_store_monthly_profitability[avg_daily_footfall] )
```

### Year-on-year (fixed-year pattern, robust to slicers)

Display folder: `2 Year on Year`

```dax
Net Profit 2023 = CALCULATE ( [Net Profit], dim_date[year] = 2023 )

Net Profit 2024 = CALCULATE ( [Net Profit], dim_date[year] = 2024 )

Net Profit Change 24 vs 23 = [Net Profit 2024] - [Net Profit 2023]

Revenue 2023 = CALCULATE ( [Revenue], dim_date[year] = 2023 )

Revenue 2024 = CALCULATE ( [Revenue], dim_date[year] = 2024 )

Revenue Growth % = DIVIDE ( [Revenue 2024], [Revenue 2023] ) - 1

Net Margin 2023 = CALCULATE ( [Net Margin %], dim_date[year] = 2023 )

Net Margin 2024 = CALCULATE ( [Net Margin %], dim_date[year] = 2024 )

Margin Change (pts) = [Net Margin 2024] - [Net Margin 2023]

-- For month/quarter visuals with the year on the axis or in a slicer:
Net Profit PY =
VAR y = SELECTEDVALUE ( dim_date[year] )
RETURN
    IF (
        NOT ISBLANK ( y ),
        CALCULATE ( [Net Profit], REMOVEFILTERS ( dim_date[year] ), dim_date[year] = y - 1 )
    )
```

---

## 5. Store health, status and watchlist

Display folder: `3 Store Health`

```dax
Loss Store-Months = SUM ( fact_store_monthly_profitability[Is Loss Month] )

Structural Loss Store-Months =
CALCULATE (
    COUNTROWS ( fact_store_monthly_profitability ),
    fact_store_monthly_profitability[Status (Recomputed)] = "Structural-Loss"
)

Loss Share % = DIVIDE ( [Loss Store-Months], [Store-Months] )

-- For comparison with the (unreliable) supplied labels:
Loss Store-Months (Supplied Label) =
CALCULATE (
    COUNTROWS ( fact_store_monthly_profitability ),
    fact_store_monthly_profitability[profitability_status]
        IN { "Loss-Making", "Structural-Loss" }
)

Stores Below Estate Margin =
VAR estate = CALCULATE ( [Net Margin %], ALL ( dim_store ) )
RETURN
    COUNTROWS ( FILTER ( VALUES ( dim_store[store_id] ), [Net Margin %] < estate ) )

Margin Rank (1 = best) =
RANKX ( ALLSELECTED ( dim_store[store_name] ), [Net Margin %], , DESC, DENSE )

-- Priority review = margin below 10% OR 6+ loss months per 24 (scaled to the period shown)
-- Watch           = margin below 14% OR 2024 profit down more than £75k
Store Flag =
VAR margin = [Net Margin %]
VAR lossM  = [Loss Store-Months]
VAR scaled = 0.25 * [Months in Context]
RETURN
    IF (
        ISBLANK ( margin ), BLANK (),
        SWITCH (
            TRUE (),
            margin < 0.10 || lossM >= scaled,            "Priority review",
            margin < 0.14 || [Net Profit Change 24 vs 23] < -75000, "Watch",
            "Healthy"
        )
    )

Store Flag Sort =
SWITCH ( [Store Flag], "Priority review", 1, "Watch", 2, "Healthy", 3 )

Priority Review Stores =
COUNTROWS (
    FILTER ( VALUES ( dim_store[store_id] ), [Store Flag] = "Priority review" )
)

-- Which cost line is furthest above the estate average?
Primary Driver =
VAR estRent  = CALCULATE ( [Rent % of Revenue],     ALL ( dim_store ) )
VAR estStaff = CALCULATE ( [Staffing % of Revenue], ALL ( dim_store ) )
VAR rentGap  = [Rent % of Revenue]     - estRent
VAR staffGap = [Staffing % of Revenue] - estStaff
RETURN
    IF ( [Store Flag] = "Healthy", BLANK (),
         IF ( staffGap >= rentGap, "Staffing", "Rent" ) )
```

### Sizing the prize (annualised)

Display folder: `4 Opportunity`

```dax
-- Margin of every store NOT in the current selection (e.g. "all stores excluding London")
Peer Margin % =
VAR selected = VALUES ( dim_store[store_id] )
VAR peers    = EXCEPT ( ALL ( dim_store[store_id] ), selected )
RETURN
    CALCULATE ( [Net Margin %], REMOVEFILTERS ( dim_store ), peers )

-- Annual profit uplift if the selection earned the peer margin
Margin Gap to Peers (£/yr) =
VAR gap = [Peer Margin %] - [Net Margin %]
RETURN
    MAX ( 0, DIVIDE ( gap * [Revenue], [Years in Context] ) )

-- Annual saving if each store's staffing % came down to the median store
Median Staffing % =
CALCULATE (
    MEDIANX ( ALL ( dim_store[store_id] ), CALCULATE ( [Staffing % of Revenue] ) ),
    REMOVEFILTERS ( dim_store )
)

Staffing Gap to Median (£/yr) =
SUMX (
    VALUES ( dim_store[store_id] ),
    VAR s   = [Staffing % of Revenue]
    VAR gap = MAX ( 0, s - [Median Staffing %] )
    RETURN DIVIDE ( gap * [Revenue], [Years in Context] )
)
```

> The prize measures **overlap** (a store can appear in more than one). Present them as sizes of opportunity, not as a total.

---

## 6. Loyalty measures

Display folder: `5 Loyalty`

```dax
Member Revenue = SUM ( fact_store_monthly_profitability[loyalty_member_spend_gbp] )

Non-Member Revenue = SUM ( fact_store_monthly_profitability[non_member_spend_gbp] )

Member Revenue % = DIVIDE ( [Member Revenue], [Revenue] )

-- Store attribute, so it averages across the stores in context
Avg Adoption Rate = AVERAGE ( dim_store[loyalty_adoption_rate] )

-- 1.00 = members spend the same per head as non-members.
-- Read it at store level; it is an odds ratio of member share vs adoption.
Member Spend Multiple =
VAR m = [Member Revenue %]
VAR a = [Avg Adoption Rate]
RETURN DIVIDE ( DIVIDE ( m, 1 - m ), DIVIDE ( a, 1 - a ) )

Redemption % of Member Revenue = DIVIDE ( [Loyalty Redemption Cost], [Member Revenue] )

-- The brief's "net value" - note it treats ALL member revenue as incremental
Naive Loyalty Net Value (brief definition) = [Member Revenue] - [Loyalty Redemption Cost]

-- Extra spend per member (vs the same customer without the programme)
-- needed for gross profit to cover redemption cost
Break-even Uplift % =
VAR k = DIVIDE ( [Loyalty Redemption Cost], [Member Revenue] * [Gross Margin % (P&L)] )
RETURN DIVIDE ( k, 1 - k )
```

### What-if scenario (slicer)

Create a parameter: **Modeling → New parameter → Numeric range**, name `Uplift Assumption`, min 0, max 0.30, step 0.01, "Add slicer" ticked. Power BI creates `'Uplift Assumption'[Uplift Assumption Value]`. Then:

```dax
Assumed Uplift = SELECTEDVALUE ( 'Uplift Assumption'[Uplift Assumption], 0 )

Incremental Revenue (scenario) =
DIVIDE ( [Member Revenue] * [Assumed Uplift], 1 + [Assumed Uplift] )

Incremental Gross Profit (scenario) = [Incremental Revenue (scenario)] * [Gross Margin % (P&L)]

Programme Net Value (scenario) = [Incremental Gross Profit (scenario)] - [Loyalty Redemption Cost]

Programme Net Value per Year (scenario) = DIVIDE ( [Programme Net Value (scenario)], [Years in Context] )
```

At 0% uplift the programme loses its full cost (£1.73m over two years); the line crosses zero at about **+10.3%**.

---

## 7. Daily-sample measures (ratios only)

Display folder: `6 Mix & Rhythm`

```dax
Daily Revenue (Sample) = SUM ( fact_daily_sales[total_revenue_gbp] )

Espresso Revenue = SUM ( fact_daily_sales[espresso_revenue_gbp] )
Filter Revenue   = SUM ( fact_daily_sales[filter_revenue_gbp] )
Food Revenue     = SUM ( fact_daily_sales[food_revenue_gbp] )
Beans Revenue    = SUM ( fact_daily_sales[retail_beans_revenue_gbp] )

Espresso Share % = DIVIDE ( [Espresso Revenue], [Daily Revenue (Sample)] )
Filter Share %   = DIVIDE ( [Filter Revenue],   [Daily Revenue (Sample)] )
Food Share %     = DIVIDE ( [Food Revenue],     [Daily Revenue (Sample)] )
Beans Share %    = DIVIDE ( [Beans Revenue],    [Daily Revenue (Sample)] )

-- Revenue-weighted basket size
ATV (£) = DIVIDE ( SUM ( fact_daily_sales[total_revenue_gbp] ),
                   SUM ( fact_daily_sales[total_transactions] ) )

Footfall Conversion % = DIVIDE ( SUM ( fact_daily_sales[total_transactions] ),
                                 SUM ( fact_daily_sales[footfall] ) )

Avg Footfall per Store-Day = AVERAGE ( fact_daily_sales[footfall] )

Loyalty Transaction Share % = DIVIDE ( SUM ( fact_daily_sales[loyalty_transactions] ),
                                       SUM ( fact_daily_sales[total_transactions] ) )

-- Average revenue per sampled store-day (a pattern measure, not a total)
Avg Revenue per Store-Day = AVERAGE ( fact_daily_sales[total_revenue_gbp] )

Avg Rev Weekday = CALCULATE ( [Avg Revenue per Store-Day], dim_date[is_weekend] = FALSE () )
Avg Rev Weekend = CALCULATE ( [Avg Revenue per Store-Day], dim_date[is_weekend] = TRUE () )

Weekend vs Weekday % = DIVIDE ( [Avg Rev Weekend], [Avg Rev Weekday] ) - 1

Avg Rev Standard Day =
CALCULATE ( [Avg Revenue per Store-Day],
            dim_date[uk_trading_calendar] = "Standard-Trading-Day" )

Avg Rev Bank Holiday =
CALCULATE ( [Avg Revenue per Store-Day],
            dim_date[uk_trading_calendar] = "Bank-Holiday" )

Bank Holiday vs Standard Day % = DIVIDE ( [Avg Rev Bank Holiday], [Avg Rev Standard Day] ) - 1

Sampled Rows = COUNTROWS ( fact_daily_sales )

Catalogue Margin % = AVERAGE ( dim_product[gross_margin_pct] )
```

---

## 8. Validation checklist

After building the model, place these on a scratch page. Values should match to the precision shown.

| Measure | Expected (full period, no filters) |
|---|---:|
| Revenue | £89,685,989 |
| Net Profit | £16,879,504 |
| Net Margin % | 18.82% |
| Gross Margin % (P&L) | 62.11% |
| Staffing % of Revenue | 30.99% |
| Rent % of Revenue | 10.37% |
| Loyalty Cost % of Revenue | 1.93% |
| Loyalty Redemption Cost | £1,730,161 |
| Member Revenue | £29,769,501 |
| Store Count | 60 |
| Store-Months | 1,440 |
| Loss Store-Months (recomputed) | 197 |
| Structural Loss Store-Months | 76 |
| Loss Store-Months (supplied label) | 164 |
| Net Margin 2023 / 2024 | 18.84% / 18.80% |
| Revenue Growth % | −0.6% |
| Break-even Uplift % | 10.3% |
| ATV (£) | £7.28 |
| Weekend vs Weekday % | −24.4% |
| Bank Holiday vs Standard Day % | −34.4% |
| Priority Review Stores | 9 |
| Net Margin % (London only) | 8.45% |
| Margin Gap to Peers (£/yr), London | about £614k |
| Staffing Gap to Median (£/yr), all stores | about £1.17m |
| Food Share % / Espresso Share % | 26.1% / 45.7% |

`data/derived/store_scorecard.csv` has one row per store with margin, flag and driver, for checking the store-level table.

---

## 9. Performance and good-practice notes

- Hide all `*_id` columns and the raw fact columns that you have wrapped in measures.
- Use **display folders** exactly as labelled above so the field list is navigable.
- Format: £ measures `£#,0` (use `£#,0.0,,"m"` for millions), % measures `0.0%`, multiples `0.00`.
- Do not use `AVERAGE` on any `*_pct` column in a visual; use the weighted measures.
- Set measure descriptions (Model view → Properties). Judges and stakeholders read them.
