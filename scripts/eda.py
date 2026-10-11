"""
Sunrise Coffee Chain - DataDNA Challenge (Oct 2026)
Reproducible EDA: validates the data, computes the headline metrics used in the
report/dashboard, writes derived CSVs and saves the charts in /images.

Usage:
    python scripts/eda.py [path/to/raw/csv/folder]     (default: data/raw)
"""
import json
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RAW = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "data" / "raw"
OUT_IMG = ROOT / "images"
OUT_DER = ROOT / "data" / "derived"
OUT_IMG.mkdir(exist_ok=True)
OUT_DER.mkdir(parents=True, exist_ok=True)

# ---------- palette ----------
ESPRESSO, CARAMEL, SUNRISE = "#3B2314", "#C98B4A", "#F28C28"
TEAL, RED, GREEN, GREY, CREAM = "#2A7F7F", "#B3382C", "#3C8D5A", "#8C8C8C", "#FAF6F0"
plt.rcParams.update({
    "figure.facecolor": "white", "axes.facecolor": "white",
    "axes.spines.top": False, "axes.spines.right": False,
    "axes.edgecolor": "#BBBBBB", "axes.titleweight": "bold",
    "axes.titlesize": 12, "axes.labelsize": 10, "font.size": 10,
    "figure.dpi": 130, "savefig.bbox": "tight",
})

# ---------- load ----------
store = pd.read_csv(RAW / "dim_store.csv")
prod = pd.read_csv(RAW / "dim_product.csv")
date = pd.read_csv(RAW / "dim_date.csv")
mon = pd.read_csv(RAW / "fact_store_monthly_profitability.csv")
day = pd.read_csv(RAW / "fact_daily_sales.csv")

mon["year"] = mon.month_id.str[:4].astype(int)
mon["mon"] = mon.month_id.str[5:].astype(int)
mon["quarter"] = (mon.mon - 1) // 3 + 1
mon = mon.merge(
    store[["store_id", "store_name", "store_format", "location_type", "region",
           "store_status", "opening_year", "loyalty_adoption_rate",
           "monthly_rent_gbp", "monthly_staffing_cost_gbp"]],
    on="store_id", suffixes=("", "_dim"))

M = {}  # metrics collected for the write-up


def status_from_margin(x):
    if x > 0.20:
        return "Highly-Profitable"
    if x >= 0.08:
        return "Profitable"
    if x >= -0.02:
        return "Break-Even"
    if x >= -0.15:
        return "Loss-Making"
    return "Structural-Loss"


mon["status_recomputed"] = mon.net_profit_margin_pct.map(status_from_margin)
STATUS_ORDER = ["Highly-Profitable", "Profitable", "Break-Even", "Loss-Making", "Structural-Loss"]

# =====================================================================
# 1. DATA QUALITY
# =====================================================================
dq = {}
dq["net_profit_formula_max_abs_diff"] = float((
    mon.total_monthly_revenue_gbp - mon.total_monthly_cogs_gbp - mon.monthly_rent_gbp
    - mon.monthly_staffing_cost_gbp - mon.loyalty_redemption_cost_gbp - mon.net_profit_gbp).abs().max())
dq["member_plus_nonmember_max_abs_diff"] = float((
    mon.loyalty_member_spend_gbp + mon.non_member_spend_gbp - mon.total_monthly_revenue_gbp).abs().max())
dq["categories_sum_max_abs_diff"] = float((
    day.espresso_revenue_gbp + day.filter_revenue_gbp + day.food_revenue_gbp
    + day.retail_beans_revenue_gbp - day.total_revenue_gbp).abs().max())
dq["store_formats"] = store.store_format.value_counts().to_dict()
dq["location_types"] = store.location_type.value_counts().to_dict()
dq["rent_bands_present"] = mon.rent_band.value_counts().to_dict()
dq["status_mismatch_rows"] = int((mon.profitability_status != mon.status_recomputed).sum())
dq["status_supplied"] = mon.profitability_status.value_counts().reindex(STATUS_ORDER).to_dict()
dq["status_recomputed"] = mon.status_recomputed.value_counts().reindex(STATUS_ORDER).to_dict()
dq["status_crosstab"] = pd.crosstab(mon.profitability_status, mon.status_recomputed).to_dict()
dq["rent_ratio_vs_dim_range"] = [float((mon.monthly_rent_gbp / mon.monthly_rent_gbp_dim).min()),
                                 float((mon.monthly_rent_gbp / mon.monthly_rent_gbp_dim).max())]
dq["staff_ratio_vs_dim_range"] = [float((mon.monthly_staffing_cost_gbp / mon.monthly_staffing_cost_gbp_dim).min()),
                                  float((mon.monthly_staffing_cost_gbp / mon.monthly_staffing_cost_gbp_dim).max())]
dq["daily_rows"] = int(len(day))
dq["daily_distinct_store_days"] = int(day.drop_duplicates(["store_id", "date_id"]).shape[0])
dq["daily_duplicate_store_days"] = int(day.duplicated(["store_id", "date_id"]).sum())
dq["daily_coverage_of_store_days"] = dq["daily_distinct_store_days"] / (60 * 730)
dq["nulls_monthly"] = int(mon.isna().sum().sum())
dq["seating_nulls"] = int(store.seating_capacity.isna().sum())
dq["margin_min_max"] = [float(mon.net_profit_margin_pct.min()), float(mon.net_profit_margin_pct.max())]
dq["gm_pl"] = float(1 - mon.total_monthly_cogs_gbp.sum() / mon.total_monthly_revenue_gbp.sum())
dq["gm_daily"] = float(day.daily_gross_profit_gbp.sum() / day.total_revenue_gbp.sum())
M["data_quality"] = dq

# =====================================================================
# 2. ESTATE HEADLINES
# =====================================================================
cols = ["total_monthly_revenue_gbp", "total_monthly_cogs_gbp", "monthly_rent_gbp",
        "monthly_staffing_cost_gbp", "loyalty_redemption_cost_gbp", "net_profit_gbp"]
tot = mon[cols].sum()
yr = mon.groupby("year")[cols].sum()
yr["margin"] = yr.net_profit_gbp / yr.total_monthly_revenue_gbp
M["totals"] = {
    "revenue": float(tot.total_monthly_revenue_gbp),
    "net_profit": float(tot.net_profit_gbp),
    "margin": float(tot.net_profit_gbp / tot.total_monthly_revenue_gbp),
    "cogs_pct": float(tot.total_monthly_cogs_gbp / tot.total_monthly_revenue_gbp),
    "rent_pct": float(tot.monthly_rent_gbp / tot.total_monthly_revenue_gbp),
    "staffing_pct": float(tot.monthly_staffing_cost_gbp / tot.total_monthly_revenue_gbp),
    "loyalty_pct": float(tot.loyalty_redemption_cost_gbp / tot.total_monthly_revenue_gbp),
    "loyalty_cost": float(tot.loyalty_redemption_cost_gbp),
    "by_year": yr.round(4).to_dict(orient="index"),
}

# =====================================================================
# 3. STORE / FORMAT / REGION
# =====================================================================
def weighted(g):
    d = g.groupby(g.columns[0]) if False else None
    return d


def seg(by):
    g = mon.groupby(by).agg(
        stores=("store_id", "nunique"),
        revenue=("total_monthly_revenue_gbp", "sum"),
        net_profit=("net_profit_gbp", "sum"),
        rent=("monthly_rent_gbp", "sum"),
        staffing=("monthly_staffing_cost_gbp", "sum"),
        sqft=("revenue_per_sqft_gbp", "mean"),
        footfall=("avg_daily_footfall", "mean"),
        adoption=("loyalty_adoption_rate", "mean"),
        n=("store_id", "size"))
    g["margin"] = g.net_profit / g.revenue
    g["rent_pct"] = g.rent / g.revenue
    g["staffing_pct"] = g.staffing / g.revenue
    sup = mon.assign(l=mon.profitability_status.isin(["Loss-Making", "Structural-Loss"])).groupby(by).l.mean()
    rec = mon.assign(l=mon.status_recomputed.isin(["Loss-Making", "Structural-Loss"])).groupby(by).l.mean()
    g["loss_share_supplied"] = sup
    g["loss_share_recomputed"] = rec
    g["avg_rent_per_store"] = mon.groupby(by).monthly_rent_gbp.mean()
    g["avg_rev_per_store_month"] = mon.groupby(by).total_monthly_revenue_gbp.mean()
    return g


by_fmt, by_loc, by_reg = seg("store_format"), seg("location_type"), seg("region")
M["by_format"] = by_fmt.round(4).to_dict(orient="index")
M["by_location"] = by_loc.round(4).to_dict(orient="index")
M["by_region"] = by_reg.sort_values("margin").round(4).to_dict(orient="index")

# recomputed status counts by region (Loss + Structural)
rc = pd.crosstab(mon.region, mon.status_recomputed).reindex(columns=STATUS_ORDER, fill_value=0)
rs = pd.crosstab(mon.region, mon.profitability_status).reindex(columns=STATUS_ORDER, fill_value=0)
M["region_status_recomputed"] = rc.to_dict(orient="index")
M["region_status_supplied"] = rs.to_dict(orient="index")

# ---- store scorecard ----
sc = mon.groupby("store_id").agg(
    store_name=("store_name", "first"), region=("region", "first"),
    location_type=("location_type", "first"), store_format=("store_format", "first"),
    store_status=("store_status", "first"), opening_year=("opening_year", "first"),
    loyalty_adoption_rate=("loyalty_adoption_rate", "first"),
    revenue=("total_monthly_revenue_gbp", "sum"), net_profit=("net_profit_gbp", "sum"),
    cogs=("total_monthly_cogs_gbp", "sum"), rent=("monthly_rent_gbp", "sum"),
    staffing=("monthly_staffing_cost_gbp", "sum"), loyalty_cost=("loyalty_redemption_cost_gbp", "sum"),
    loyalty_member_spend=("loyalty_member_spend_gbp", "sum"),
    avg_footfall=("avg_daily_footfall", "mean"), avg_dwell=("avg_dwell_time_minutes", "mean"),
    avg_rev_per_sqft=("revenue_per_sqft_gbp", "mean"))
sc["avg_monthly_revenue"] = sc.revenue / 24
sc["margin"] = sc.net_profit / sc.revenue
sc["rent_pct"] = sc.rent / sc.revenue
sc["staffing_pct"] = sc.staffing / sc.revenue
sc["loyalty_cost_pct_rev"] = sc.loyalty_cost / sc.revenue
sc["gross_margin"] = 1 - sc.cogs / sc.revenue
sc["loss_months"] = mon.assign(l=mon.status_recomputed.isin(["Loss-Making", "Structural-Loss"])).groupby("store_id").l.sum()
sc["structural_months"] = mon.assign(l=mon.status_recomputed == "Structural-Loss").groupby("store_id").l.sum()
np_y = mon.pivot_table(index="store_id", columns="year", values="net_profit_gbp", aggfunc="sum")
rv_y = mon.pivot_table(index="store_id", columns="year", values="total_monthly_revenue_gbp", aggfunc="sum")
sc["np_2023"], sc["np_2024"] = np_y[2023], np_y[2024]
sc["np_change"] = sc.np_2024 - sc.np_2023
sc["margin_2023"], sc["margin_2024"] = np_y[2023] / rv_y[2023], np_y[2024] / rv_y[2024]
sc["member_spend_share"] = sc.loyalty_member_spend / sc.revenue
# odds ratio of member revenue share vs adoption: 1.0 => members spend the same per head as non-members
sc["member_spend_multiple"] = (sc.member_spend_share / (1 - sc.member_spend_share)) / (
    sc.loyalty_adoption_rate / (1 - sc.loyalty_adoption_rate))
sc["rent_quartile"] = pd.qcut(sc.rent / 24, 4, labels=["Q1 (lowest rent)", "Q2", "Q3", "Q4 (highest rent)"])

est_margin = M["totals"]["margin"]
sc["flag"] = np.where(
    (sc.margin < 0.10) | (sc.loss_months >= 6), "Priority review",
    np.where((sc.margin < 0.14) | (sc.np_change < -75000), "Watch", "Healthy"))
# which cost line is furthest above the estate average? (rent vs staffing, in % of revenue points)
sc["rent_gap_pts"] = sc.rent_pct - M["totals"]["rent_pct"]
sc["staffing_gap_pts"] = sc.staffing_pct - M["totals"]["staffing_pct"]
sc["primary_driver"] = np.where(sc.flag == "Healthy", "",
                                np.where(sc.staffing_gap_pts >= sc.rent_gap_pts, "Staffing", "Rent"))
M["scorecard_flag_counts"] = sc.flag.value_counts().to_dict()

# =====================================================================
# 4. COST DRIVERS
# =====================================================================
corr = {
    "staffing_pct~margin": float(sc.staffing_pct.corr(sc.margin)),
    "rent_pct~margin": float(sc.rent_pct.corr(sc.margin)),
    "avg_rent~margin": float((sc.rent / 24).corr(sc.margin)),
    "avg_rent~avg_revenue": float((sc.rent / 24).corr(sc.avg_monthly_revenue)),
    "avg_revenue~margin": float(sc.avg_monthly_revenue.corr(sc.margin)),
    "gross_margin~margin": float(sc.gross_margin.corr(sc.margin)),
    "adoption~margin": float(sc.loyalty_adoption_rate.corr(sc.margin)),
    "footfall~revenue": float(sc.avg_footfall.corr(sc.avg_monthly_revenue)),
    "dwell~margin": float(sc.avg_dwell.corr(sc.margin)),
    "opening_year~margin": float(sc.opening_year.corr(sc.margin)),
}
X = np.c_[np.ones(len(sc)), sc.staffing_pct, sc.rent_pct]
beta, *_ = np.linalg.lstsq(X, sc.margin.values, rcond=None)
pred = X @ beta
r2 = 1 - ((sc.margin - pred) ** 2).sum() / ((sc.margin - sc.margin.mean()) ** 2).sum()
r2_staff = float(sc.staffing_pct.corr(sc.margin) ** 2)
corr["r2_margin_on_staffing_and_rent"] = float(r2)
corr["r2_margin_on_staffing_only"] = r2_staff
corr["coef_staffing_pct"] = float(beta[1])
corr["coef_rent_pct"] = float(beta[2])
M["correlations"] = corr

rq = sc.groupby("rent_quartile", observed=True).agg(
    stores=("margin", "size"), avg_rent=("rent", lambda x: x.mean() / 24),
    avg_rev=("avg_monthly_revenue", "mean"), margin=("margin", "mean"),
    rent_pct=("rent_pct", "mean"), staffing_pct=("staffing_pct", "mean"))
M["rent_quartiles"] = rq.round(4).to_dict(orient="index")

# profit prizes (annualised)
london = sc[sc.region == "London"]
ex_london_margin = (sc[sc.region != "London"].net_profit.sum() / sc[sc.region != "London"].revenue.sum())
M["prize"] = {
    "london_margin": float(london.net_profit.sum() / london.revenue.sum()),
    "ex_london_margin": float(ex_london_margin),
    "london_gap_per_year_gbp": float((ex_london_margin - london.net_profit.sum() / london.revenue.sum()) * london.revenue.sum() / 2),
    "london_avg_rent": float(london.rent.mean() / 24),
    "estate_avg_rent": float(sc.rent.mean() / 24),
    "london_rent_pct": float(london.rent.sum() / london.revenue.sum()),
    "london_staffing_pct": float(london.staffing.sum() / london.revenue.sum()),
}
review = sc[sc.flag == "Priority review"]
M["prize"]["priority_review_stores"] = int(len(review))
M["prize"]["priority_review_gap_per_year_gbp"] = float(
    ((est_margin - review.margin).clip(lower=0) * review.revenue).sum() / 2)
med_staff = sc.staffing_pct.median()
above = sc[sc.staffing_pct > med_staff]
M["prize"]["median_staffing_pct"] = float(med_staff)
M["prize"]["staffing_to_median_per_year_gbp"] = float(((above.staffing_pct - med_staff) * above.revenue).sum() / 2)
M["prize"]["stores_above_median_staffing"] = int(len(above))
sc["staffing_gap_to_median_gbp_yr"] = ((sc.staffing_pct - med_staff) * sc.revenue / 2).clip(lower=0)
M["prize"]["bottom6_names"] = sc.sort_values("margin").head(6).store_name.tolist()

# =====================================================================
# 5. LOYALTY
# =====================================================================
lo = {}
lo["corr_adoption_member_share_store"] = float(sc.loyalty_adoption_rate.corr(sc.member_spend_share))
lo["corr_adoption_member_share_monthly"] = float(mon.loyalty_adoption_rate.corr(mon.loyalty_member_revenue_pct))
lo["member_spend_multiple_mean"] = float(sc.member_spend_multiple.mean())
lo["member_spend_multiple_min_max"] = [float(sc.member_spend_multiple.min()), float(sc.member_spend_multiple.max())]
lo["stores_multiple_gt_1_10"] = int((sc.member_spend_multiple > 1.10).sum())
lo["corr_adoption_multiple"] = float(sc.loyalty_adoption_rate.corr(sc.member_spend_multiple))
member_rev = float(mon.loyalty_member_spend_gbp.sum())
red = float(mon.loyalty_redemption_cost_gbp.sum())
gm = dq["gm_pl"]
k = red / (member_rev * gm)
lo["member_revenue"] = member_rev
lo["redemption_cost"] = red
lo["redemption_pct_of_member_rev"] = red / member_rev
lo["redemption_pct_of_total_rev"] = red / float(mon.total_monthly_revenue_gbp.sum())
lo["breakeven_uplift"] = k / (1 - k)
lo["naive_net_value"] = member_rev - red
lo["stores_with_positive_naive_value"] = int(((sc.loyalty_member_spend - sc.loyalty_cost) > 0).sum())
lo["redemption_zero_months"] = int((mon.loyalty_redemption_cost_gbp == 0).sum())
sc["adoption_band"] = pd.qcut(sc.loyalty_adoption_rate, 4, labels=["Q1 low", "Q2", "Q3", "Q4 high"])
ab = sc.groupby("adoption_band", observed=True).apply(lambda x: pd.Series({
    "stores": len(x), "adoption": x.loyalty_adoption_rate.mean(),
    "member_share": x.loyalty_member_spend.sum() / x.revenue.sum(),
    "redemption_pct_rev": x.loyalty_cost.sum() / x.revenue.sum(),
    "redemption_pct_member": x.loyalty_cost.sum() / x.loyalty_member_spend.sum(),
    "margin": x.net_profit.sum() / x.revenue.sum()}), include_groups=False)
lo["adoption_bands"] = ab.round(4).to_dict(orient="index")

dd = day.merge(store[["store_id", "loyalty_adoption_rate"]], on="store_id")
dd["loy_share"] = dd.loyalty_transactions / dd.total_transactions
dd["adopt_band"] = pd.qcut(dd.loyalty_adoption_rate, 4, labels=["Q1 low", "Q2", "Q3", "Q4 high"])
atv_b = dd.groupby("adopt_band", observed=True).apply(lambda x: pd.Series({
    "atv": x.total_revenue_gbp.sum() / x.total_transactions.sum(),
    "loy_tx_share": x.loyalty_transactions.sum() / x.total_transactions.sum()}), include_groups=False)
lo["atv_by_adoption_band"] = atv_b.round(4).to_dict(orient="index")
lo["atv_slope_per_unit_loyalty_share"] = float(np.polyfit(dd.loy_share, dd.avg_transaction_value_gbp, 1)[0])
lo["corr_atv_loyalty_share_daily"] = float(dd.avg_transaction_value_gbp.corr(dd.loy_share))
lo["atv_overall"] = float(day.total_revenue_gbp.sum() / day.total_transactions.sum())
lo["redemption_per_loyalty_tx_daily"] = float(day.loyalty_redemption_cost_gbp.sum() / day.loyalty_transactions.sum())
lo["by_region_adoption"] = sc.groupby("region").loyalty_adoption_rate.mean().sort_values().round(3).to_dict()
lo["by_location_adoption"] = sc.groupby("location_type").loyalty_adoption_rate.mean().round(3).to_dict()
M["loyalty"] = lo

# =====================================================================
# 6. REVENUE MIX (daily sample - ratios only)
# =====================================================================
fd = (day.merge(date, on="date_id")
         .merge(store[["store_id", "store_format", "location_type", "region"]], on="store_id")
         .merge(prod[["product_id", "product_category", "product_name"]], on="product_id"))
cats = ["espresso_revenue_gbp", "filter_revenue_gbp", "food_revenue_gbp", "retail_beans_revenue_gbp"]
CATLAB = {"espresso_revenue_gbp": "Espresso", "filter_revenue_gbp": "Filter",
          "food_revenue_gbp": "Food", "retail_beans_revenue_gbp": "Retail beans"}
mix_all = fd[cats].sum() / fd[cats].sum().sum()
mix_year = fd.groupby("year")[cats].sum().pipe(lambda x: x.div(x.sum(axis=1), axis=0))
mix_q = fd.assign(yq=fd.year.astype(str) + "-Q" + fd.quarter.astype(str)).groupby("yq")[cats].sum().pipe(
    lambda x: x.div(x.sum(axis=1), axis=0))
mix_loc = fd.groupby("location_type")[cats].sum().pipe(lambda x: x.div(x.sum(axis=1), axis=0))
t = fd.date_id.values
trend = {CATLAB[c]: float(np.polyfit(t, (fd[c] / fd.total_revenue_gbp).values, 1)[0] * 365) for c in cats}
# monthly food share and a simple significance check on the trend
fd["ym"] = fd.year.astype(str) + "-" + fd.month_number.astype(str).str.zfill(2)
food_m = (fd.groupby("ym").food_revenue_gbp.sum() / fd.groupby("ym").total_revenue_gbp.sum())
slope, intercept = np.polyfit(np.arange(len(food_m)), food_m.values, 1)
resid = food_m.values - (slope * np.arange(len(food_m)) + intercept)
se = np.sqrt((resid ** 2).sum() / (len(food_m) - 2) / ((np.arange(len(food_m)) - np.arange(len(food_m)).mean()) ** 2).sum())
M["mix"] = {
    "overall": {CATLAB[c]: float(v) for c, v in mix_all.items()},
    "by_year": {int(y): {CATLAB[c]: float(v) for c, v in r.items()} for y, r in mix_year.iterrows()},
    "by_location": {l: {CATLAB[c]: float(v) for c, v in r.items()} for l, r in mix_loc.iterrows()},
    "trend_share_change_per_year": trend,
    "food_share_monthly_slope_per_month": float(slope),
    "food_share_monthly_slope_t": float(slope / se),
    "food_share_first_last_month": [float(food_m.iloc[0]), float(food_m.iloc[-1])],
}
cm = prod.groupby("product_category").agg(
    products=("product_id", "size"), avg_margin=("gross_margin_pct", "mean"),
    min_margin=("gross_margin_pct", "min"), max_margin=("gross_margin_pct", "max"),
    avg_price=("unit_price_gbp", "mean"))
M["category_margin"] = cm.round(4).to_dict(orient="index")
weights = {"Espresso-Drinks": mix_all["espresso_revenue_gbp"], "Filter-Coffee": mix_all["filter_revenue_gbp"],
           "Food": mix_all["food_revenue_gbp"], "Retail-Beans": mix_all["retail_beans_revenue_gbp"]}
M["catalogue_margin_on_mix"] = float(sum(cm.loc[k_, "avg_margin"] * w for k_, w in weights.items()) / sum(weights.values()))
M["top_product_share_by_category"] = fd.product_category.value_counts(normalize=True).round(4).to_dict()

# =====================================================================
# 7. TEMPORAL
# =====================================================================
order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
wd = fd.groupby("day_of_week").agg(rev=("total_revenue_gbp", "mean"), tx=("total_transactions", "mean"),
                                   atv=("avg_transaction_value_gbp", "mean"), foot=("footfall", "mean"),
                                   n=("total_revenue_gbp", "size")).reindex(order)
wd["conv"] = (fd.groupby("day_of_week").total_transactions.sum() / fd.groupby("day_of_week").footfall.sum()).reindex(order)
wk = fd.groupby("is_weekend").total_revenue_gbp.mean()
bh = fd.groupby("is_uk_bank_holiday").total_revenue_gbp.mean()
wkday = fd[(~fd.is_weekend)]
bh_vs_weekday = (wkday[wkday.is_uk_bank_holiday].total_revenue_gbp.mean() /
                 wkday[~wkday.is_uk_bank_holiday].total_revenue_gbp.mean() - 1)
cal = fd.groupby("uk_trading_calendar").agg(rev=("total_revenue_gbp", "mean"), n=("total_revenue_gbp", "size"))
bh_fmt = fd.groupby(["location_type", "is_uk_bank_holiday"]).total_revenue_gbp.agg(["mean", "size"]).unstack()
we_fmt = fd.groupby(["location_type", "is_weekend"]).total_revenue_gbp.mean().unstack()
M["weekday"] = wd.round(3).to_dict(orient="index")
M["weekend_vs_weekday_pct"] = float(wk[True] / wk[False] - 1)
M["weekend_avg"], M["weekday_avg"] = float(wk[True]), float(wk[False])
M["bank_holiday_vs_all_other_days_pct"] = float(bh[True] / bh[False] - 1)
M["bank_holiday_vs_other_weekdays_pct"] = float(bh_vs_weekday)
M["bank_holiday_rows"] = int(fd.is_uk_bank_holiday.sum())
M["trading_calendar"] = cal.round(2).to_dict(orient="index")
M["bank_holiday_by_location"] = {
    loc: {"bh": float(bh_fmt.loc[loc, ("mean", True)]), "non_bh": float(bh_fmt.loc[loc, ("mean", False)]),
          "pct": float(bh_fmt.loc[loc, ("mean", True)] / bh_fmt.loc[loc, ("mean", False)] - 1),
          "n_bh": int(bh_fmt.loc[loc, ("size", True)])} for loc in bh_fmt.index}
M["weekend_by_location"] = {loc: float(we_fmt.loc[loc, True] / we_fmt.loc[loc, False] - 1) for loc in we_fmt.index}

ms = mon.groupby(["year", "mon"]).agg(rev=("total_monthly_revenue_gbp", "sum"), np_=("net_profit_gbp", "sum"))
ms["margin"] = ms.np_ / ms.rev
mm = ms.margin.unstack(0)
mr = ms.rev.unstack(0)
mnp = ms.np_.unstack(0)
M["monthly_margin_corr_2023_2024"] = float(mm[2023].corr(mm[2024]))
M["monthly_revenue_corr_2023_2024"] = float(mr[2023].corr(mr[2024]))
M["monthly_netprofit_corr_2023_2024"] = float(mnp[2023].corr(mnp[2024]))
M["best_worst_month_np"] = {
    "best": [(int(y), int(m_), float(v)) for (y, m_), v in ms.np_.nlargest(3).items()],
    "worst": [(int(y), int(m_), float(v)) for (y, m_), v in ms.np_.nsmallest(3).items()]}
q = mon.groupby(["year", "quarter"]).agg(rev=("total_monthly_revenue_gbp", "sum"), np_=("net_profit_gbp", "sum"))
q["margin"] = q.np_ / q.rev
M["quarterly"] = {f"{y}-Q{qq}": {"rev": float(r.rev), "np": float(r.np_), "margin": float(r.margin)}
                  for (y, qq), r in q.iterrows()}
M["monthly_margin_range"] = [float(ms.margin.min()), float(ms.margin.max())]
M["monthly_revenue_range_pct"] = float(ms.rev.max() / ms.rev.min() - 1)
fm = mon.groupby(["store_format", "mon"]).apply(
    lambda x: x.net_profit_gbp.sum() / x.total_monthly_revenue_gbp.sum(), include_groups=False).unstack(0)
M["hub_vs_hs_monthly_margin_range"] = {c: [float(fm[c].min()), float(fm[c].max())] for c in fm.columns}

# =====================================================================
# 8. SAVE DERIVED DATA
# =====================================================================
sc_out = sc.reset_index().drop(columns=["rent_quartile", "adoption_band"]).round(4)
sc_out.to_csv(OUT_DER / "store_scorecard.csv", index=False)
mon_out = mon[["monthly_profit_id", "store_id", "month_id", "total_monthly_revenue_gbp", "net_profit_gbp",
               "net_profit_margin_pct", "profitability_status", "status_recomputed"]]
mon_out.to_csv(OUT_DER / "monthly_status_recomputed.csv", index=False)
with open(OUT_DER / "metrics.json", "w") as fh:
    json.dump(M, fh, indent=2, default=str)

# =====================================================================
# 9. CHARTS
# =====================================================================
def save(fig, name):
    fig.savefig(OUT_IMG / name)
    plt.close(fig)


def pct_fmt(x, _=None):
    return f"{x:.0%}"


# 01 estate trend
fig, ax = plt.subplots(1, 2, figsize=(12, 4))
months = np.arange(1, 13)
for y, c in [(2023, GREY), (2024, SUNRISE)]:
    ax[0].plot(months, mr[y] / 1e6, marker="o", color=c, label=str(y), lw=2)
    ax[1].plot(months, mm[y], marker="o", color=c, label=str(y), lw=2)
ax[0].set_title("Estate revenue by month (£m)")
ax[1].set_title("Estate net margin by month")
ax[1].yaxis.set_major_formatter(pct_fmt)
for a in ax:
    a.set_xticks(months)
    a.set_xticklabels(list("JFMAMJJASOND"))
    a.legend(frameon=False)
fig.suptitle("Flat year on year, and the monthly pattern does not repeat", y=1.02, fontweight="bold")
save(fig, "01_estate_trend.png")

# 02 region margin
rg = by_reg.sort_values("margin")
fig, ax = plt.subplots(figsize=(8, 5))
colors = [RED if r == "London" else (TEAL if m_ > est_margin else CARAMEL) for r, m_ in zip(rg.index, rg.margin)]
ax.barh(rg.index, rg.margin, color=colors)
ax.axvline(est_margin, color=ESPRESSO, ls="--", lw=1)
ax.text(est_margin + 0.003, 0.2, f"Estate {est_margin:.1%}", color=ESPRESSO, fontsize=9)
for i, v in enumerate(rg.margin):
    ax.text(v + 0.004, i, f"{v:.1%}", va="center", fontsize=9)
ax.xaxis.set_major_formatter(pct_fmt)
ax.set_title("Net profit margin by region (revenue-weighted, 2023-24)")
save(fig, "02_region_margin.png")

# 03 cost drivers
fig, ax = plt.subplots(1, 2, figsize=(12, 4.6), gridspec_kw={"width_ratios": [1.3, 1]})
colr = sc.region.map(lambda r: RED if r == "London" else CARAMEL)
ax[0].scatter(sc.staffing_pct, sc.margin, c=colr, s=sc.avg_monthly_revenue / 450, alpha=0.8, edgecolor="white")
z = np.polyfit(sc.staffing_pct, sc.margin, 1)
xs = np.linspace(sc.staffing_pct.min(), sc.staffing_pct.max(), 50)
ax[0].plot(xs, np.polyval(z, xs), color=ESPRESSO, lw=1.5)
ax[0].xaxis.set_major_formatter(pct_fmt)
ax[0].yaxis.set_major_formatter(pct_fmt)
ax[0].set_xlabel("Staffing cost as % of revenue")
ax[0].set_ylabel("Net margin")
ax[0].set_title(f"Staffing share explains margin (r = {corr['staffing_pct~margin']:.2f}); London in red")
worst = sc.sort_values("margin").iloc[0]
ax[0].annotate(worst.store_name.replace("Sunrise Coffee ", ""), (worst.staffing_pct, worst.margin),
               xytext=(-10, 18), textcoords="offset points", fontsize=8, ha="right")
ax[1].bar(range(4), rq.margin, color=[TEAL, TEAL, CARAMEL, RED])
ax[1].set_xticks(range(4))
ax[1].set_xticklabels(["Q1\nlowest", "Q2", "Q3", "Q4\nhighest"])
for i, (m_, rv) in enumerate(zip(rq.margin, rq.avg_rev)):
    ax[1].text(i, m_ + 0.004, f"{m_:.1%}\n£{rv/1000:.0f}k rev", ha="center", fontsize=8)
ax[1].yaxis.set_major_formatter(pct_fmt)
ax[1].set_ylim(0, 0.28)
ax[1].set_title("Margin by rent quartile (revenue ~ equal)")
save(fig, "03_cost_drivers.png")

# 04 status mismatch
fig, ax = plt.subplots(figsize=(8, 4))
w = 0.38
x = np.arange(5)
ax.bar(x - w / 2, [dq["status_supplied"][s_] for s_ in STATUS_ORDER], w, color=GREY, label="Supplied label")
ax.bar(x + w / 2, [dq["status_recomputed"][s_] for s_ in STATUS_ORDER], w, color=SUNRISE, label="Recomputed from margin %")
for i, s_ in enumerate(STATUS_ORDER):
    ax.text(i - w / 2, dq["status_supplied"][s_] + 8, dq["status_supplied"][s_], ha="center", fontsize=8)
    ax.text(i + w / 2, dq["status_recomputed"][s_] + 8, dq["status_recomputed"][s_], ha="center", fontsize=8)
ax.set_xticks(x)
ax.set_xticklabels([s_.replace("-", "-\n") for s_ in STATUS_ORDER], fontsize=9)
ax.legend(frameon=False)
ax.set_title("profitability_status: supplied vs documented thresholds (store-months)")
save(fig, "04_status_supplied_vs_recomputed.png")

# 05 loyalty
fig, ax = plt.subplots(1, 3, figsize=(14, 4.2))
ax[0].scatter(sc.loyalty_adoption_rate, sc.member_spend_share, color=SUNRISE, edgecolor="white", s=45)
ax[0].plot([0, 0.65], [0, 0.65], color=ESPRESSO, ls="--", lw=1)
ax[0].text(0.36, 0.30, "members spend\nsame as non-members", fontsize=8, color=ESPRESSO)
ax[0].xaxis.set_major_formatter(pct_fmt)
ax[0].yaxis.set_major_formatter(pct_fmt)
ax[0].set_xlabel("Loyalty adoption rate")
ax[0].set_ylabel("Member share of revenue")
ax[0].set_title(f"Member share = adoption (r = {lo['corr_adoption_member_share_store']:.3f})")
ax[1].bar(atv_b.index.astype(str), atv_b.atv, color=CARAMEL)
for i, v in enumerate(atv_b.atv):
    ax[1].text(i, v + 0.05, f"£{v:.2f}", ha="center", fontsize=9)
ax[1].set_ylim(0, 9)
ax[1].set_xlabel("Store adoption quartile")
ax[1].set_title("Basket size is flat across adoption")
ax[2].bar(ab.index.astype(str), ab.redemption_pct_member, color=RED)
for i, v in enumerate(ab.redemption_pct_member):
    ax[2].text(i, v + 0.004, f"{v:.1%}", ha="center", fontsize=9)
ax[2].set_yticks([0, .05, .10, .15, .20])
ax[2].yaxis.set_major_formatter(pct_fmt)
ax[2].set_xlabel("Store adoption quartile")
ax[2].set_title("Redemption cost as % of member revenue")
save(fig, "05_loyalty.png")

# 06 loyalty break-even
fig, ax = plt.subplots(figsize=(7.5, 4))
ups = np.linspace(0, 0.30, 61)
member_rev_pl = member_rev
net_inc = member_rev_pl * ups / (1 + ups) * gm - red
ax.plot(ups, net_inc / 1e6, color=ESPRESSO, lw=2)
ax.axhline(0, color=GREY, lw=1)
ax.axvline(lo["breakeven_uplift"], color=SUNRISE, ls="--")
ax.axvline(0.0, color=RED, ls=":")
ax.text(lo["breakeven_uplift"] + 0.005, -1.45, f"break-even\n+{lo['breakeven_uplift']:.1%}", color=SUNRISE, fontsize=9)
ax.text(0.005, 0.9, "observed:\n~0%", color=RED, fontsize=9)
ax.xaxis.set_major_formatter(pct_fmt)
ax.set_xlabel("Assumed extra spend per member vs the same customer without the app")
ax.set_ylabel("Net programme value (£m, 2 yrs)")
ax.set_title("What uplift would loyalty need to pay for itself?")
save(fig, "06_loyalty_breakeven.png")

# 07 mix
fig, ax = plt.subplots(1, 2, figsize=(13, 4.3), gridspec_kw={"width_ratios": [1.5, 1]})
bottom = np.zeros(len(mix_q))
for c, col in zip(cats, [ESPRESSO, CARAMEL, SUNRISE, TEAL]):
    ax[0].bar(mix_q.index, mix_q[c], bottom=bottom, color=col, label=CATLAB[c])
    for i, v in enumerate(mix_q[c]):
        ax[0].text(i, bottom[i] + v / 2, f"{v:.0%}", ha="center", va="center", fontsize=7, color="white")
    bottom += mix_q[c].values
ax[0].legend(ncol=4, frameon=False, loc="upper center", bbox_to_anchor=(0.5, -0.12))
ax[0].yaxis.set_major_formatter(pct_fmt)
ax[0].set_title("Revenue mix by quarter (daily-sales sample)")
ax[0].tick_params(axis="x", labelsize=8)
cmx = cm.sort_values("avg_margin")
ax[1].barh(cmx.index, cmx.avg_margin, color=[RED if i == "Retail-Beans" else CARAMEL for i in cmx.index])
for i, v in enumerate(cmx.avg_margin):
    ax[1].text(v + 0.005, i, f"{v:.0%}", va="center", fontsize=9)
ax[1].set_xlim(0.5, 0.95)
ax[1].xaxis.set_major_formatter(pct_fmt)
ax[1].set_title("Catalogue gross margin by category")
save(fig, "07_revenue_mix.png")

# 08 weekday / calendar
fig, ax = plt.subplots(1, 2, figsize=(12, 4))
ax[0].bar([d[:3] for d in order], wd.rev, color=[CARAMEL] * 5 + [ESPRESSO] * 2)
for i, v in enumerate(wd.rev):
    ax[0].text(i, v + 25, f"£{v:,.0f}", ha="center", fontsize=8)
ax[0].set_ylim(0, 2600)
ax[0].set_title(f"Average daily revenue by weekday (weekend {M['weekend_vs_weekday_pct']:.0%})")
cl = cal.rev.reindex(["Standard-Trading-Day", "School-Holiday", "Christmas-Period", "Bank-Holiday"])
ax[1].bar([c_.replace("-", "\n") for c_ in cl.index], cl.values, color=[CARAMEL, CARAMEL, CARAMEL, RED])
for i, v in enumerate(cl.values):
    ax[1].text(i, v + 25, f"£{v:,.0f}", ha="center", fontsize=8)
ax[1].set_ylim(0, 2600)
ax[1].set_title("Average daily revenue by trading calendar")
save(fig, "08_weekday_and_calendar.png")

# 09 seasonality heatmap
fig, ax = plt.subplots(figsize=(8.5, 3))
hm = mm.T.values
im = ax.imshow(hm, cmap="YlOrBr", aspect="auto", vmin=0.15, vmax=0.22)
ax.set_xticks(range(12))
ax.set_xticklabels(["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"])
ax.set_yticks([0, 1])
ax.set_yticklabels(["2023", "2024"])
for i in range(2):
    for j in range(12):
        ax.text(j, i, f"{hm[i, j]:.1%}", ha="center", va="center", fontsize=8)
ax.set_title("Estate net margin by month: no repeating seasonal shape")
save(fig, "09_seasonality_heatmap.png")

# 10 store yoy
yy = sc.sort_values("np_change")
pick = pd.concat([yy.head(8), yy.tail(8)])
fig, ax = plt.subplots(figsize=(8, 6))
ax.barh(pick.store_name.str.replace("Sunrise Coffee ", ""), pick.np_change / 1000,
        color=[RED if v < 0 else TEAL for v in pick.np_change])
ax.axvline(0, color=GREY, lw=1)
ax.set_xlabel("Change in annual net profit, 2024 vs 2023 (£k)")
ax.set_title("Biggest movers: 8 decliners and 8 improvers")
save(fig, "10_store_yoy_movers.png")

# 11 watchlist scatter
fig, ax = plt.subplots(figsize=(8, 5))
fc = sc.flag.map({"Priority review": RED, "Watch": SUNRISE, "Healthy": TEAL})
ax.scatter(sc.avg_monthly_revenue / 1000, sc.margin, c=fc, s=55, edgecolor="white")
ax.axhline(est_margin, color=ESPRESSO, ls="--", lw=1)
ax.yaxis.set_major_formatter(pct_fmt)
ax.set_xlabel("Average monthly revenue (£k)")
ax.set_ylabel("Net margin (24 months)")
for _, r in sc[sc.flag == "Priority review"].iterrows():
    ax.annotate(r.store_name.replace("Sunrise Coffee ", ""), (r.avg_monthly_revenue / 1000, r.margin),
                xytext=(5, 4), textcoords="offset points", fontsize=7)
for lab, col in [("Priority review", RED), ("Watch", SUNRISE), ("Healthy", TEAL)]:
    ax.scatter([], [], c=col, label=lab)
ax.legend(frameon=False, loc="lower right")
ax.set_title("Store watchlist: revenue is similar, margin is not")
save(fig, "11_store_watchlist.png")

# 12 correlation heatmap
cc = pd.DataFrame({
    "Avg monthly revenue": sc.avg_monthly_revenue, "Monthly rent": sc.rent / 24,
    "Staffing % rev": sc.staffing_pct, "Rent % rev": sc.rent_pct, "Gross margin": sc.gross_margin,
    "Loyalty adoption": sc.loyalty_adoption_rate, "Avg footfall": sc.avg_footfall,
    "Avg dwell (min)": sc.avg_dwell, "Opening year": sc.opening_year, "Net margin": sc.margin}).corr()
fig, ax = plt.subplots(figsize=(8, 6.5))
im = ax.imshow(cc, cmap="RdBu_r", vmin=-1, vmax=1)
ax.set_xticks(range(len(cc)))
ax.set_xticklabels(cc.columns, rotation=45, ha="right", fontsize=8)
ax.set_yticks(range(len(cc)))
ax.set_yticklabels(cc.columns, fontsize=8)
for i in range(len(cc)):
    for j in range(len(cc)):
        ax.text(j, i, f"{cc.iloc[i, j]:.2f}", ha="center", va="center", fontsize=7,
                color="white" if abs(cc.iloc[i, j]) > 0.6 else "black")
ax.set_title("Store-level correlations (60 stores)")
fig.colorbar(im, shrink=0.7)
save(fig, "12_correlations.png")
M["corr_matrix"] = cc.round(3).to_dict()
with open(OUT_DER / "metrics.json", "w") as fh:
    json.dump(M, fh, indent=2, default=str)

# =====================================================================
# 10. PRINT SUMMARY
# =====================================================================
pd.set_option("display.width", 220)
pd.set_option("display.max_columns", 40)
print(json.dumps({k_: M[k_] for k_ in ["data_quality", "totals", "correlations", "prize", "loyalty"]}, indent=1, default=str))
print("\nREGION\n", by_reg.sort_values("margin")[["stores", "revenue", "margin", "rent_pct", "staffing_pct",
                                              "avg_rent_per_store", "loss_share_supplied", "loss_share_recomputed", "adoption"]].round(3))
print("\nLOCATION\n", by_loc[["stores", "revenue", "margin", "sqft", "footfall", "rent_pct", "staffing_pct", "adoption"]].round(3))
print("\nFORMAT\n", by_fmt[["stores", "revenue", "margin", "sqft", "footfall"]].round(3))
print("\nRENT Q\n", rq.round(3))
print("\nRECOMPUTED STATUS BY REGION\n", rc)
print("\nFLAGS\n", sc.flag.value_counts())
print(sc.sort_values("margin").head(14)[["store_name", "region", "store_status", "avg_monthly_revenue", "margin", "loss_months",
                                         "structural_months", "staffing_pct", "rent_pct", "np_change", "flag"]].round(3))
print("\nWATCH\n", sc[sc.flag == "Watch"][["store_name", "region", "margin", "loss_months", "np_change"]].round(3))
for k_ in ["mix", "category_margin", "catalogue_margin_on_mix", "weekend_vs_weekday_pct", "weekend_avg", "weekday_avg",
           "bank_holiday_vs_all_other_days_pct", "bank_holiday_vs_other_weekdays_pct", "bank_holiday_rows",
           "trading_calendar", "bank_holiday_by_location", "weekend_by_location", "monthly_margin_corr_2023_2024",
           "monthly_revenue_corr_2023_2024", "monthly_netprofit_corr_2023_2024", "best_worst_month_np", "quarterly",
           "monthly_margin_range", "monthly_revenue_range_pct", "hub_vs_hs_monthly_margin_range"]:
    print("\n", k_, json.dumps(M[k_], indent=1, default=str) if isinstance(M[k_], (dict, list)) else M[k_])
print("\nWEEKDAY\n", wd.round(3))
print("\nYoY movers\n", sc.sort_values("np_change")[["store_name", "region", "np_2023", "np_2024", "np_change"]].head(6).round(0),
      "\n", sc.sort_values("np_change")[["store_name", "region", "np_2023", "np_2024", "np_change"]].tail(6).round(0))
print("improved", int((sc.np_change > 0).sum()), "declined", int((sc.np_change < 0).sum()))
