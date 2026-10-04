from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
OUT = ROOT / "visualizations"
OUT.mkdir(exist_ok=True)

orders = pd.read_csv(DATA / "orders.csv")
customers = pd.read_csv(DATA / "customers.csv")
products = pd.read_csv(DATA / "products.csv")

orders["payment_method"] = orders["payment_method"].astype("string").str.strip().str.upper()
natural_key = ["customer_id","product_id","order_date","quantity","discount_pct","payment_method","rating","returned"]
orders = orders.loc[~orders.duplicated(subset=natural_key, keep="first")].copy()
orders["discount_pct"] = orders["discount_pct"].fillna(0)
orders["rating"] = orders["rating"].fillna(orders["rating"].median())

merged = orders.merge(products, on="product_id").merge(customers, on="customer_id")
merged["order_value"] = merged["quantity"] * merged["price"] * (1 - merged["discount_pct"] / 100)
q1, q3 = merged["quantity"].quantile([.25,.75])
iqr = q3-q1
lower, upper = q1-1.5*iqr, q3+1.5*iqr
merged["is_outlier"] = ~merged["quantity"].between(lower, upper)

rates = (merged.groupby("payment_method")["returned"].mean()*100).sort_values(ascending=False)
fig, ax = plt.subplots(figsize=(8,5))
bars = ax.bar(rates.index, rates.values)
ax.set_ylabel("Return rate (%)")
ax.set_xlabel("Payment method")
ax.set_title("COD Returns at 44.4% — 3x Card")
for bar, value in zip(bars, rates.values):
    ax.text(bar.get_x()+bar.get_width()/2, bar.get_height()+0.8, f"{value:.1f}%", ha="center")
fig.tight_layout()
fig.savefig(OUT/"return_rate_by_payment.png", dpi=160)
plt.close(fig)

merged["order_date"] = pd.to_datetime(merged["order_date"])
merged["year_month"] = merged["order_date"].dt.to_period("M").astype(str)
monthly = merged.loc[~merged["is_outlier"]].groupby("year_month")["order_value"].sum()
fig, ax = plt.subplots(figsize=(9,5))
ax.plot(monthly.index, monthly.values, marker="o")
ax.set_xlabel("Month")
ax.set_ylabel("Revenue (INR)")
ax.set_title("Monthly Revenue Trend — March 2026 is the True Peak")
ax.tick_params(axis="x", rotation=45)
fig.tight_layout()
fig.savefig(OUT/"monthly_revenue_trend.png", dpi=160)
plt.close(fig)
print("Generated:", OUT/"return_rate_by_payment.png")
print("Generated:", OUT/"monthly_revenue_trend.png")
