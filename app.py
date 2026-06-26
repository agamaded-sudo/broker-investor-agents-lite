import streamlit as st
import yfinance as yf
import subprocess
import sys
from pathlib import Path

st.set_page_config(page_title="Broker Investor Agents", layout="wide", page_icon="📊")

st.title("📊 Broker Investor Agents")
st.caption("Investment screening and independent investor analysis system")

tab1, tab2 = st.tabs(["📡 Tab 1 — Initial Scan", "📋 Tab 2 — Five Investor Reports"])


# ── Helpers ───────────────────────────────────────────────────────────────────

def get_info(ticker: str) -> dict:
    return yf.Ticker(ticker.upper()).info


def gate0(info: dict) -> tuple[bool, list[str]]:
    issues = []
    if not info.get("regularMarketPrice") and not info.get("currentPrice"):
        issues.append("No market price — stock may not be listed or tradable")
    if not info.get("totalRevenue"):
        issues.append("No operating revenue found")
    if not info.get("financialCurrency"):
        issues.append("No reliable financial data found")
    return len(issues) == 0, issues


def opportunity_score(info: dict) -> tuple[int, list[str], list[str]]:
    passed, failed = [], []
    checks = {
        "Revenue Growth > 10%":   (info.get("revenueGrowth") or 0) > 0.10,
        "Operating Income > 0":   (info.get("operatingIncome") or 0) > 0,
        "Net Income > 0":         (info.get("netIncomeToCommon") or 0) > 0,
        "Free Cash Flow > 0":     (info.get("freeCashflow") or 0) > 0,
        "Operating Margin > 15%": (info.get("operatingMargins") or 0) > 0.15,
        "ROE > 15%":              (info.get("returnOnEquity") or 0) > 0.15,
        "EPS Growth > 10%":       (info.get("earningsGrowth") or 0) > 0.10,
        "Debt/Equity < 150%":     0 < (info.get("debtToEquity") or 999) < 150,
        "P/E < 30":               0 < (info.get("trailingPE") or 999) < 30,
        "Share Dilution < 5%":    (info.get("sharesPercentSharesOut") or 0) < 0.05,
    }
    for label, result in checks.items():
        (passed if result else failed).append(label)
    return len(passed), passed, failed


def golden_triggers(info: dict) -> list[str]:
    triggers = []
    fcf    = (info.get("freeCashflow") or 0) > 0
    rev_g  = info.get("revenueGrowth") or 0
    eps_g  = info.get("earningsGrowth") or 0
    roe    = info.get("returnOnEquity") or 0
    margin = info.get("operatingMargins") or 0
    pe     = info.get("trailingPE") or 999
    peg    = info.get("pegRatio") or 999
    price  = info.get("currentPrice") or 0
    high52 = info.get("fiftyTwoWeekHigh") or 1

    if rev_g > 0.15 and fcf:
        triggers.append("Revenue Growth > 15% + Positive FCF")
    if roe > 0.20:
        triggers.append("ROE > 20%")
    if margin > 0.25:
        triggers.append("Operating Margin > 25%")
    if eps_g > 0.15 and pe < 25:
        triggers.append("EPS Growth > 15% + P/E < 25")
    if 0 < peg < 1.2:
        triggers.append("PEG < 1.2")
    if high52 > 0 and price < high52 * 0.75 and fcf and rev_g > 0:
        triggers.append("Price down >25% from 52W High + Positive FCF + Growing Revenue")
    return triggers


# ── Tab 1: Initial Scan ───────────────────────────────────────────────────────

with tab1:
    st.header("Initial Scan — Opportunity Scout")

    with st.expander("📖 Logic 1 — Screening Rules", expanded=False):
        st.markdown("""
### Gate 0 — Hard Filters (instant reject if any fails)
| # | Rule |
|---|------|
| 1 | Stock is listed and tradable on a regulated exchange |
| 2 | Reliable and official financial data exists |
| 3 | Company has real operating revenue |

---

### Opportunity Score — 10 Criteria (1 point each)
| Criterion | Threshold |
|-----------|-----------|
| Revenue Growth | > 10% |
| Operating Income | > 0 |
| Net Income | > 0 |
| Free Cash Flow | > 0 |
| Operating Margin | > 15% |
| ROE | > 15% |
| EPS Growth | > 10% |
| Debt/Equity | < 150% |
| P/E Ratio | < 30 |
| Share Dilution | < 5% |

### Decision
| Score | Outcome |
|-------|---------|
| 8–10 | ✅ Pass to Candidate List |
| 6–7  | 👁 Watchlist |
| 0–5  | ❌ Reject |

---

### Golden Triggers (automatic pass regardless of score)
- Revenue Growth > 15% + Positive FCF
- ROE > 20%
- Operating Margin > 25%
- EPS Growth > 15% + P/E < 25
- PEG < 1.2
- Price down >25% from 52W High + Positive FCF + Growing Revenue
        """)

    col1, col2 = st.columns([3, 1])
    with col1:
        ticker_scan = st.text_input("Ticker Symbol", placeholder="e.g. AAPL", key="scan_ticker")
    with col2:
        st.markdown("<br>", unsafe_allow_html=True)
        scan_btn = st.button("🔍 Scan", key="scan_btn", use_container_width=True)

    if scan_btn and ticker_scan:
        with st.spinner(f"Scanning {ticker_scan.upper()}..."):
            try:
                info = get_info(ticker_scan)
                name = info.get("shortName") or ticker_scan.upper()
                st.subheader(f"{name} ({ticker_scan.upper()})")

                # Gate 0
                st.markdown("#### 🚦 Gate 0 — Hard Filters")
                gate_ok, gate_issues = gate0(info)
                if gate_ok:
                    st.success("Passed Gate 0 — Stock is listed, tradable, and has financial data")
                else:
                    st.error("Failed Gate 0 — Stock rejected")
                    for issue in gate_issues:
                        st.write(f"• {issue}")
                    st.stop()

                # Score
                st.markdown("#### 📈 Opportunity Score")
                score, passed, failed = opportunity_score(info)

                price = info.get("currentPrice") or info.get("regularMarketPrice")
                pe    = info.get("trailingPE")
                decision = "✅ Pass" if score >= 8 else "👁 Watchlist" if score >= 6 else "❌ Reject"

                col_a, col_b, col_c, col_d = st.columns(4)
                with col_a:
                    st.metric("Score", f"{score} / 10")
                with col_b:
                    st.metric("Decision", decision)
                with col_c:
                    price_str = f"${price:.2f}" if price else "N/A"
                    st.metric("Price", price_str)
                with col_d:
                    pe_str = f"{pe:.1f}" if pe else "N/A"
                    st.metric("P/E", pe_str)

                col_p, col_f = st.columns(2)
                with col_p:
                    st.markdown("**✅ Passed Criteria**")
                    for p in passed:
                        st.write(f"• {p}")
                with col_f:
                    st.markdown("**❌ Failed Criteria**")
                    for f in failed:
                        st.write(f"• {f}")

                # Golden Triggers
                triggers = golden_triggers(info)
                if triggers:
                    st.markdown("#### 🌟 Golden Triggers Detected")
                    st.info("Strong signals found — stock qualifies even without a full score")
                    for t in triggers:
                        st.write(f"• {t}")

            except Exception as e:
                st.error(f"Error: {e}")


# ── Tab 2: Five Investor Reports ──────────────────────────────────────────────

with tab2:
    st.header("Five Investor Reports")

    with st.expander("📖 Logic 2 — How Reports Are Generated", expanded=False):
        st.markdown("""
### Pipeline
1. **Input** — Ticker symbol entered by user
2. **Backoffice** — Collects and normalizes company data (financials, market data, growth metrics)
3. **Live Data** — Market price and ratios fetched live from Yahoo Finance
4. **Five Independent Agents** — Each investor evaluates the company independently:

| Investor | Focus |
|----------|-------|
| **Buffett** | Durable economics, moat, intrinsic value, margin of safety |
| **Munger** | Business quality, incentives, simplicity, avoidable errors |
| **Fisher** | Qualitative growth, management depth, research culture, long runway |
| **Lynch** | Understandable growth, category fit, earnings durability, valuation discipline |
| **Bogle** | Broad-market discipline, cost awareness, diversification, benchmark context |

5. **Output** — Independent response letter + follow-up memo per investor
6. **Deal Package** — Broker-facing summary of all five responses

### Important
- Each investor evaluates independently — no consensus, no ranking, no average
- Output is research-only — not a recommendation, allocation, or trade signal
- Auto-promotion is disabled
        """)

    col1, col2 = st.columns([3, 1])
    with col1:
        ticker_rep = st.text_input("Ticker Symbol", placeholder="e.g. MSFT", key="rep_ticker")
    with col2:
        st.markdown("<br>", unsafe_allow_html=True)
        rep_btn = st.button("📋 Analyze", key="rep_btn", use_container_width=True)

    if rep_btn and ticker_rep:
        with st.spinner(f"Running full analysis for {ticker_rep.upper()} — this may take a minute..."):
            try:
                project_root = Path(__file__).parent
                result = subprocess.run(
                    [
                        sys.executable, "-m", "broker_agents.cli", "analyze-stock",
                        "--ticker", ticker_rep.upper(),
                        "--examples-root", str(project_root / "examples"),
                        "--outputs-root", str(project_root / "data/outputs"),
                        "--fixtures-root", str(project_root / "tests/fixtures"),
                        "--portfolio-context", str(project_root / "examples/portfolio_context.yaml"),
                    ],
                    capture_output=True, text=True, cwd=str(project_root)
                )

                ticker_up   = ticker_rep.upper()
                report_path = project_root / f"data/outputs/{ticker_up}/deal_package/{ticker_up.lower()}_broker_deal_package.md"

                if report_path.exists():
                    report_text = report_path.read_text(encoding="utf-8")
                    st.success(f"Analysis complete for {ticker_up}")
                    st.markdown("---")
                    st.markdown(report_text)
                    st.markdown("---")
                    st.download_button(
                        label="💾 Download Report",
                        data=report_text,
                        file_name=f"{ticker_up}_broker_report.md",
                        mime="text/markdown"
                    )
                else:
                    st.warning("Analysis completed but report file not found")
                    if result.stderr:
                        st.code(result.stderr)

            except Exception as e:
                st.error(f"Error: {e}")
