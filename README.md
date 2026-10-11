# ☕ Sunrise Coffee Chain: Where does profit really come from?

**DataDNA Dataset Challenge · October 2026**
An analysis of 60 UK coffee stores over 24 months (Jan 2023 – Dec 2024), built to help a Chief Commercial Officer decide where to expand, whether to invest in loyalty, which stores to review, and how to plan staffing.

![Staffing share vs margin](images/03_cost_drivers.png)

## The answer in one paragraph

Sunrise is a stable **£89.7m** estate earning an **18.8%** store-level margin that has not moved in two years. Revenue per store is almost identical everywhere (£56k to £71k a month), so **profit differences come from costs, not sales**: staffing share explains 69% of the gap between stores, and rent buys no extra revenue. Nine stores need review, and they have two different problems. The loyalty programme costs **£1.73m** and shows **no visible spend uplift**. Seasonality is not reliable; the weekly rhythm is.

## Key findings

| # | Finding | Evidence |
|---|---|---|
| 1 | **Costs, not sales, decide margin** | Staffing % vs margin r = −0.83. At equal revenue (~£62k/month), the highest-rent quartile earns 14.8% vs 22.4% for the lowest |
| 2 | **London is a rent problem** | 8.5% margin; £11.7k average rent vs £6.5k estate. Matching peer margin is worth ~£0.6m a year |
| 3 | **9 stores need review: 5 rent-led, 4 labour-led** | e.g. South London Corner: −3.6% margin, staffing 51.7% of revenue. Fixing the 9 is worth ~£0.76m a year |
| 4 | **Loyalty shows no uplift** | Member share of revenue = adoption (r = 0.998); basket size flat at £7.28; members would need to spend +10.3% more just to cover redemption cost |
| 5 | **Mix is stable; food is not growing** | Espresso 45.7%, Food 26.1%, Filter 19.2%, Beans 9.1% |
| 6 | **Plan for the week, not the season** | Weekends −24% (footfall, not basket); bank holidays −34%; same month in 2023 vs 2024 correlates at r = −0.52 |

![Region margin](images/02_region_margin.png)

## Data quality: what I found and how I handled it

The audit matters as much as the insights. Highlights:

- `profitability_status` contradicts its own thresholds on **600 of 1,440 rows**; it is **recomputed from margin %** (Structural-Loss: 17 supplied vs 76 recomputed).
- `fact_daily_sales` is a **~20% sample**, so it is used for ratios and patterns, never for £ totals.
- There are **2 store formats, not 3** (two hubs, both in Luton); analysis uses `location_type` instead.
- Catalogue gross margin (80.7% on mix) does not reconcile with P&L gross margin (62.1%); P&L is used.
- "Net profit" is store-level and excludes central overheads.

Full table of 13 issues: [`docs/01_EDA.md`](docs/01_EDA.md#32-issues-found).

## Repository structure

```
├── README.md
├── docs/
│   ├── 01_EDA.md                  Data audit, findings, sized recommendations
│   ├── 02_Visualisation_Guide.md  Page-by-page Power BI build spec
│   └── 03_DAX_Measures.md         Data model, calculated columns, measures, validation values
├── powerbi/
│   └── sunrise_theme.json         Import via View → Themes → Browse for themes
├── scripts/
│   └── eda.py                     Reproducible analysis: metrics, derived CSVs, charts
├── data/
│   ├── raw/                       Place the 5 challenge CSVs here (not committed)
│   └── derived/
│       ├── store_scorecard.csv           One row per store: margin, flag, driver, £ gaps
│       ├── monthly_status_recomputed.csv Supplied vs recomputed status per store-month
│       └── metrics.json                  Every number quoted in the docs
├── images/                        Charts used in the docs
└── dashboard/                     Power BI export (PDF)
```

## How to reproduce

```bash
pip install -r requirements.txt
# put dim_store.csv, dim_product.csv, dim_date.csv,
# fact_daily_sales.csv, fact_store_monthly_profitability.csv in data/raw/
python scripts/eda.py            # or: python scripts/eda.py path/to/csv/folder
```

This regenerates `data/derived/*` and all charts in `images/`.

## Building the dashboard

1. Follow [`docs/03_DAX_Measures.md`](docs/03_DAX_Measures.md) to build the model and measures, and check them against its validation table.
2. Import `powerbi/sunrise_theme.json`.
3. Build the six pages as specified in [`docs/02_Visualisation_Guide.md`](docs/02_Visualisation_Guide.md).

## Recommendations (sized, overlapping, not additive)

| Action | Value at stake |
|---|---|
| Rota and hours review at the 4 labour-led stores | ~£0.37m a year |
| Lease reviews at the 5 rent-led stores (4 in London) | Part of ~£0.61m London gap |
| Screen 2025 sites on rent-to-revenue and staffing model | 7.6 pts of margin between rent quartiles |
| Pause loyalty expansion; run a holdout test | £0.87m a year cost |
| Flex weekend and bank-holiday rotas to demand | Upper bound ~£1.17m a year (overlaps with the first action) |

## Limitations

Store-level profit only; regions contain 3-7 stores; daily table is a sample with unreliable product fields; no member-level data, so loyalty incrementality can be neither proven nor ruled out; two years cannot establish seasonality.

## Tools

Python (pandas, numpy, matplotlib) for the audit and analysis · Power BI + DAX for the dashboard.

## Author

**<Nneamaka Obiazor>** · [LinkedIn](https://www.linkedin.com/in/nneamaka-obiazor) · [Portfolio]()

*Dataset: DataDNA Dataset Challenge, October 2026 (Sunrise Coffee Chain). Not included in this repository.*
