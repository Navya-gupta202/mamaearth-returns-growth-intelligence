import json
import os
import re
from pathlib import Path

try:
    from google import genai
except ImportError:
    genai = None

ROOT = Path(__file__).resolve().parents[1]
FINDINGS_PATH = ROOT / "narrator" / "findings.json"
SAMPLE_PATH = ROOT / "narrator" / "sample_output.txt"

def generate_scr_narrative_offline(findings: dict) -> dict:
    rev = findings["cleaned_total_revenue_inr"]
    cod = findings["return_rate_by_payment"]["COD"]
    card = findings["return_rate_by_payment"]["CARD"]
    upi = findings["return_rate_by_payment"]["UPI"]
    risk = findings["highest_risk_segment"]
    delta = findings["duplicate_reconciliation_delta_inr"]
    peak = findings["true_peak_month"]
    inflated = findings["outlier_inflated_month"]

    narrative = f"""Situation

The cleaned order dataset records revenue of ₹{rev:,.2f}. Return behavior differs materially by payment method: COD is at {cod:.1f}%, compared with CARD at {card:.1f}% and UPI at {upi:.1f}%.

Complication

The return risk is concentrated rather than uniform. The highest-risk segment is COD in Tier-{risk["city_tier"]} cities at {risk["return_rate_pct"]:.1f}%. The raw-to-cleaned revenue reconciliation also identifies ₹{delta:,.2f} attributable to five duplicate orders, so operational reporting should use the deduplicated dataset. In the time series, January appears to lead at ₹{inflated["apparent_revenue_inr"]:,.2f}, but that apparent peak is inflated by the flagged bulk orders.

Resolution

Prioritize investigation of COD orders in Tier-{risk["city_tier"]} cities and use the cleaned pipeline as the reporting baseline. After the two quantity outliers are excluded, {peak["month"]} is the true peak month with revenue of ₹{peak["revenue_inr"]:,.2f}. This corrected view gives regional operations and finance a more reliable basis for return-reduction actions and monthly performance decisions."""
    return {"status": "success", "narrative": narrative, "tokens": None}

def generate_scr_narrative(findings: dict) -> dict:
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key or genai is None:
        return generate_scr_narrative_offline(findings)

    try:
        client = genai.Client(api_key=api_key, http_options={"timeout": 30000})
        system_instruction = (
            "You are a senior data analyst writing for Mamaearth's regional ops and finance heads. "
            "Write exactly three labeled sections: Situation, Complication, Resolution. "
            "Every number in the output must come only from the supplied findings and must appear "
            "with the same value; never invent statistics."
        )
        user_prompt = (
            "Write an approximately 250-word business narrative from this verified findings object. "
            "Do not add facts outside it. Findings:\n" + json.dumps(findings, indent=2)
        )
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=user_prompt,
            config={
                "system_instruction": system_instruction,
                # Deterministic factual reporting, not creative writing.
                "temperature": 0.0,
                "max_output_tokens": 500,
            },
        )
        text = getattr(response, "text", None)
        if not text:
            raise RuntimeError("Gemini returned no narrative text")
        usage = getattr(response, "usage_metadata", None)
        tokens = getattr(usage, "total_token_count", None) if usage else None
        return {"status": "success", "narrative": text, "tokens": tokens}
    except Exception as err:
        return {"status": "error", "narrative": None, "message": str(err)}

def normalize(s):
    return s.replace(",", "").replace("₹", "")

def check_numeric_accuracy(narrative: str, findings: dict):
    text = normalize(narrative)
    checks = [
        ("cleaned revenue", "97358.3"),
        ("COD return rate", "44.4"),
        ("COD Tier-2 risk", "54.5"),
        ("duplicate delta", "2501.9"),
        ("March true peak", "2026-03"),
        ("March peak revenue", "20318.9"),
    ]
    passed = True
    for label, needle in checks:
        ok = needle.lower() in text.lower()
        print(f"{label}: {'PASS' if ok else 'FAIL'}")
        passed &= ok
    return passed

if __name__ == "__main__":
    findings = json.loads(FINDINGS_PATH.read_text(encoding="utf-8"))
    result = generate_scr_narrative(findings)
    if result["status"] == "error":
        print("Gemini path failed; using offline fallback.")
        result = generate_scr_narrative_offline(findings)
    narrative = result["narrative"]
    print("\n" + narrative)
    print("\nNumeric accuracy checklist:")
    ok = check_numeric_accuracy(narrative, findings)
    if not SAMPLE_PATH.exists() or os.getenv("GEMINI_API_KEY"):
        SAMPLE_PATH.write_text(narrative, encoding="utf-8")
        print("Saved narrator/sample_output.txt")
    print("Overall:", "PASS" if ok else "FAIL")
