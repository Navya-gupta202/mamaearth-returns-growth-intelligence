# Mamaearth Returns & Growth Intelligence Pipeline

## Overview
A three-layer, reproducible analytics pipeline for the Mamaearth returns-and-growth case study:

1. **SQL relational layer** — loads the raw CSVs into SQLite and produces verified reports.
2. **Python/Pandas analysis layer** — cleans the raw CSVs independently, performs EDA, flags outliers, generates visualizations, and exports verified findings.
3. **GenAI insight narrator** — consumes `narrator/findings.json` and produces a Situation–Complication–Resolution (SCR) narrative, with a deterministic offline fallback.

The layers are intentionally connected by verified outputs. Part 1 uses the raw data; Part 2 independently cleans the same raw files; Part 3 receives the verified Part 2 findings.

## Repository structure
```text
.
├── README.md
├── mamaearth.db
├── sql/
│   ├── schema.sql
│   ├── seed_data.sql
│   └── reports.sql
├── data/
│   ├── customers.csv
│   ├── products.csv
│   └── orders.csv
├── analysis/
│   ├── clean_and_eda.py
│   └── visualize.py
├── visualizations/
│   ├── return_rate_by_payment.png
│   └── monthly_revenue_trend.png
└── narrator/
    ├── findings.json
    ├── generate_narrative.py
    └── sample_output.txt
```

## Requirements
- Python 3.10+
- pandas
- numpy
- matplotlib
- SQLite 3
- Optional: `google-genai` for the online Gemini path

Install Python dependencies:
```bash
pip install pandas numpy matplotlib google-genai
```

## Exact execution order

### 1. SQL layer
From the repository root:
```bash
sqlite3 mamaearth.db < sql/schema.sql
sqlite3 mamaearth.db < sql/seed_data.sql
sqlite3 mamaearth.db < sql/reports.sql
```

The seed data contains 45 customers, 16 products, and 180 raw orders.

Expected headline raw SQL result:
- Orders: 180
- Raw revenue: ₹99,860.20
- Average order value: ₹554.78
- Unrated orders: 15
- Zero-order customer: C045 / Vihaan

### 2. Python analysis layer
Run:
```bash
python analysis/clean_and_eda.py
```

This:
- standardizes payment-method casing;
- removes the five deliberate duplicate submissions;
- imputes missing discount and rating values;
- merges customers/products;
- computes order value;
- reconciles cleaned revenue against raw revenue;
- flags quantity outliers;
- tests the COD-return hypothesis;
- segments return risk by payment method and city tier;
- performs correlation analysis;
- creates the outlier-corrected monthly series;
- writes `narrator/findings.json`.

Then run:
```bash
python analysis/visualize.py
```

This regenerates both PNG visualizations from the raw CSVs.

### 3. GenAI narrator
For the optional online Gemini path, set the API key as an environment variable.

Windows PowerShell:
```powershell
$env:GEMINI_API_KEY="YOUR_KEY_HERE"
python narrator/generate_narrative.py
```

Windows CMD:
```cmd
set GEMINI_API_KEY=YOUR_KEY_HERE
python narrator/generate_narrative.py
```

Linux/macOS:
```bash
export GEMINI_API_KEY="YOUR_KEY_HERE"
python narrator/generate_narrative.py
```

If no key is configured, simply run:
```bash
python narrator/generate_narrative.py
```

The script automatically uses the fully offline deterministic SCR fallback. No network access or paid API quota is required for the fallback path.

## Verified findings
The analysis pipeline writes these values to `narrator/findings.json`:
- cleaned revenue: ₹97,358.30
- raw revenue: ₹99,860.20
- duplicate reconciliation delta: ₹2,501.90
- COD return rate: 44.4%
- CARD return rate: 14.7%
- UPI return rate: 18.9%
- highest-risk segment: COD + Tier-2 at 54.5%
- true peak: March 2026 at ₹20,318.90
- apparent January peak: ₹29,582.10, corrected to ₹11,637.10

## Reproducibility
Do not manually edit the CSV source data. All cleaning is performed in Python. Running the commands above regenerates the analytical outputs from the source files.

## Numeric validation
`narrator/generate_narrative.py` runs a numeric accuracy checker against the generated narrative. The checker verifies the cleaned revenue, COD return rate, COD + Tier-2 return rate, duplicate reconciliation delta, and the March 2026 peak revenue. The saved `sample_output.txt` is the artifact used for narrative validation.

## Business takeaway
The main operational signal is concentrated COD return risk, especially in Tier-2 cities. The main data-quality signal is the five duplicate submissions, whose combined value explains the exact raw-to-cleaned revenue difference. The time-series correction also shows why quantity outliers must be flagged before interpreting monthly performance.
