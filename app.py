import streamlit as st
import yfinance as yf
import sys
from datetime import date
from pathlib import Path

import yaml

# Ensure the repo's src/ tree is first on sys.path so all broker_agents
# imports resolve to the local source, not the potentially stale site-packages.
_SRC = Path(__file__).resolve().parent / "src"
if str(_SRC) in sys.path:
    sys.path.remove(str(_SRC))
sys.path.insert(0, str(_SRC))

st.set_page_config(page_title="Broker Investor Agents", layout="wide", page_icon="📊")

st.title("📊 Broker Investor Agents")
st.caption("Investment screening and independent investor analysis system")

tab1, tab2, tab3 = st.tabs(["🔭 Tab 1 — Market Scanner", "📡 Tab 2 — Initial Scan", "📋 Tab 3 — Five Investor Reports"])


# ── YAML generator ────────────────────────────────────────────────────────────

def generate_input_yaml(ticker: str, info: dict, examples_root: Path) -> Path:
    """Generate a minimal valid input YAML for ticker and save to examples/."""
    t = ticker.upper()
    tl = ticker.lower()
    today = date.today().isoformat()

    name        = info.get("longName") or info.get("shortName") or t
    exchange    = info.get("exchange") or "NYSE"
    currency    = info.get("financialCurrency") or "USD"
    sector      = info.get("sector") or "Unknown"
    industry    = info.get("industry") or "Unknown"
    fy_end      = info.get("lastFiscalYearEnd") or ""

    revenue      = info.get("totalRevenue") or 0
    gross_profit = info.get("grossProfits") or 0
    op_income    = info.get("operatingIncome") or 0  # not always in info
    net_income   = info.get("netIncomeToCommon") or 0
    op_cf        = info.get("operatingCashflow") or 0
    capex_raw    = info.get("capitalExpenditures") or 0
    capex        = abs(capex_raw)
    fcf          = info.get("freeCashflow") or 0
    cash         = info.get("totalCash") or 0
    total_assets = info.get("totalAssets") or 0
    lt_debt      = info.get("totalDebt") or 0
    equity       = info.get("bookValue", 0) * info.get("sharesOutstanding", 0) if info.get("bookValue") else 0
    dividends    = info.get("dividendRate", 0) * info.get("sharesOutstanding", 0) if info.get("dividendRate") else 0

    op_margin    = round((op_income / revenue), 3) if revenue else 0
    net_margin   = round((net_income / revenue), 3) if revenue else 0
    gross_margin = round((gross_profit / revenue), 3) if revenue else 0
    fcf_margin   = round((fcf / revenue), 3) if revenue else 0
    roe_proxy    = round((net_income / equity), 3) if equity else 0
    de_ratio     = round((lt_debt / equity), 3) if equity else 0

    market_cap   = info.get("marketCap") or 0
    peers        = info.get("recommendationKey") and [] or []  # yfinance doesn't give peers directly

    data = {
        "metadata": {
            "schema_name": "backoffice_data_pack_v2",
            "schema_version": 2,
            "company_name": name,
            "ticker": t,
            "analysis_date": today,
            "latest_annual_period": "TTM",
            "latest_quarterly_period": "Latest available",
            "reporting_standard": "US GAAP",
            "data_entry_mode": "auto_generated_yfinance",
            "units": "millions_usd_except_per_share_and_percentages",
            "notes": [
                "Auto-generated from yfinance data. Values are trailing twelve months where available.",
                "Not produced by manual research. Review before drawing investment conclusions.",
            ],
        },
        "company_identity": {
            "company_name": name,
            "ticker": t,
            "exchange": exchange,
            "market": "USA",
            "currency": currency,
            "sector": sector,
            "industry": industry,
            "fiscal_year_end": fy_end,
            "reporting_standard": "US GAAP",
        },
        "business_model": {
            "summary": f"{name} operates in the {sector} sector ({industry}).",
            "revenue_model": ["Details not available from automated data."],
            "neutral_observations": ["Auto-generated placeholder — review with primary sources."],
        },
        "products_customers_revenue_segments": {
            "segments": [{"name": "Total (single segment reported)", "revenue": round(revenue / 1e6, 1), "operating_income": round(op_income / 1e6, 1), "examples": []}],
            "customer_groups": ["Details not available from automated data."],
        },
        "financial_statements_summary": {
            "annual": {
                "period": "TTM",
                "revenue": round(revenue / 1e6, 1),
                "gross_profit": round(gross_profit / 1e6, 1),
                "operating_income": round(op_income / 1e6, 1),
                "net_income": round(net_income / 1e6, 1),
                "operating_cash_flow": round(op_cf / 1e6, 1),
                "capex": round(capex / 1e6, 1),
                "free_cash_flow": round(fcf / 1e6, 1),
                "cash_and_short_term_investments": round(cash / 1e6, 1),
                "total_assets": round(total_assets / 1e6, 1),
                "long_term_debt": round(lt_debt / 1e6, 1),
                "total_liabilities": None,
                "shareholders_equity": round(equity / 1e6, 1),
                "dividends_paid": round(dividends / 1e6, 1),
                "share_repurchases": None,
            },
        },
        "calculated_financial_metrics": {
            "period": "TTM",
            "gross_margin": gross_margin,
            "operating_margin": op_margin,
            "net_margin": net_margin,
            "free_cash_flow_margin": fcf_margin,
            "operating_cash_flow_margin": round(op_cf / revenue, 3) if revenue else 0,
            "return_on_equity_proxy": roe_proxy,
            "debt_to_equity": de_ratio,
            "cash_to_long_term_debt": round(cash / lt_debt, 3) if lt_debt else None,
            "notes": ["Auto-calculated from yfinance TTM figures."],
        },
        "quality_of_earnings": {
            "observations": ["Auto-generated — manual review required."],
            "gaps": ["Maintenance vs growth capex not disclosed.", "Customer retention/churn missing."],
        },
        "competitive_position_moat_indicators": {
            "moat_sources": ["Details not available from automated data."],
            "neutral_observations": ["Auto-generated placeholder — review with primary sources."],
        },
        "growth_drivers": {
            "drivers": ["Details not available from automated data."],
            "watch_items": ["Auto-generated placeholder — review with primary sources."],
        },
        "sector_specific_operating_kpis": {
            "gaps": ["Sector KPIs not available from automated data."],
        },
        "management_ownership_incentives": {
            "management_notes": ["Management details not available from automated data."],
            "gaps": ["Management compensation details missing."],
        },
        "capital_allocation": {
            "period": "TTM",
            "dividends_paid": round(dividends / 1e6, 1),
            "share_repurchases": None,
            "capex": round(capex / 1e6, 1),
            "observations": ["Auto-generated placeholder — review with primary sources."],
        },
        "capex_owner_earnings_proxy": {
            "operating_cash_flow": round(op_cf / 1e6, 1),
            "capex": round(capex / 1e6, 1),
            "free_cash_flow": round(fcf / 1e6, 1),
            "owner_earnings_proxy": round(fcf / 1e6, 1),
            "caveat": "Maintenance versus growth capex not disclosed.",
            "gaps": ["Maintenance vs growth capex not disclosed."],
        },
        "historical_valuation": {
            "current_snapshot_only": True,
            "pe_5y_median": None,
            "pe_10y_median": None,
            "p_fcf_5y_median": None,
            "p_fcf_10y_median": None,
            "ev_ebitda_5y_median": None,
            "ev_ebitda_10y_median": None,
            "valuation_history_confidence": "low_auto_generated",
            "observations": ["Historical valuation not available from automated data."],
            "gaps": ["5Y/10Y valuation data validation required."],
        },
        "peer_comparison": {
            "status": "incomplete",
            "candidate_peers": [],
            "observations": ["Peer comparison not available from automated data."],
            "gaps": ["Peer comparison incomplete."],
        },
        "valuation_snapshot": {
            "status": "market_data_yfinance",
            "market_cap": round(market_cap / 1e6, 1),
            "observations": ["Market cap sourced from yfinance."],
        },
        "risk_register": {
            "risks": [
                {"name": "Auto-generated placeholder", "description": "Risks require manual research.", "severity": "unknown"},
            ],
        },
        "scuttlebutt": {
            "status": "weak_unavailable",
            "observations": ["Not available from automated data."],
            "gaps": ["Scuttlebutt weak/unavailable."],
        },
        "market_awareness": {
            "observations": ["Auto-generated — review current market data."],
            "missing_items": ["Current share price.", "Enterprise value.", "Analyst expectations."],
        },
        "index_benchmark_alternative": {
            "benchmark_candidates": ["SPY", "VTI"],
            "observations": ["Index comparison not available from automated data."],
            "gaps": ["Index weights missing."],
        },
        "portfolio_context_form": {
            "status": "missing",
            "observations": ["No portfolio context provided."],
            "gaps": ["Portfolio context missing."],
        },
        "investor_data_map": {
            "buffett": {"relevant_sections": ["business_model", "calculated_financial_metrics", "quality_of_earnings", "competitive_position_moat_indicators", "capex_owner_earnings_proxy", "valuation_snapshot"]},
            "munger": {"relevant_sections": ["business_model", "competitive_position_moat_indicators", "management_ownership_incentives", "risk_register"]},
            "fisher": {"relevant_sections": ["growth_drivers", "sector_specific_operating_kpis", "scuttlebutt", "management_ownership_incentives"]},
            "lynch": {"relevant_sections": ["products_customers_revenue_segments", "financial_statements_summary", "calculated_financial_metrics", "peer_comparison"]},
            "bogle": {"relevant_sections": ["index_benchmark_alternative", "market_awareness", "portfolio_context_form"]},
        },
        "sources_confidence_data_gaps": {
            "source_log": [
                {
                    "source_id": f"{tl}_yfinance_auto",
                    "source_name": f"{t} yfinance auto-fetch",
                    "source_type": "vendor",
                    "retrieved_at": today,
                    "confidence": "medium",
                    "confidence_score": 0.60,
                    "freshness": "current",
                    "notes": "Auto-generated from yfinance TTM data. Not validated against primary sources.",
                }
            ],
            "known_gaps": [
                "Valuation history not available.",
                "Peer comparison incomplete.",
                "Scuttlebutt weak/unavailable.",
                "Management compensation details missing.",
                "Customer retention/churn missing.",
                "Portfolio context missing.",
            ],
        },
    }

    out_path = examples_root / f"{tl}_input.yaml"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(yaml.dump(data, sort_keys=False, allow_unicode=True), encoding="utf-8")
    return out_path


# ── Helpers ───────────────────────────────────────────────────────────────────

MARKET_SUFFIXES = {
    ".SR": {"label": "Saudi (Tadawul)", "currency": "SAR", "symbol": "ر.س", "flag": "🇸🇦"},
    ".QA": {"label": "Qatar (QSE)",     "currency": "QAR", "symbol": "ر.ق", "flag": "🇶🇦"},
}

def detect_market(ticker: str) -> dict:
    """Return market metadata dict for a ticker based on its suffix."""
    upper = ticker.upper()
    for suffix, meta in MARKET_SUFFIXES.items():
        if upper.endswith(suffix):
            return meta
    return {"label": "US Market", "currency": "USD", "symbol": "$", "flag": "🇺🇸"}

def fmt_price(price, market: dict) -> str:
    sym = market["symbol"]
    if price is None:
        return "N/A"
    return f"{sym}{price:,.2f}" if market["currency"] == "USD" else f"{price:,.2f} {sym}"

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

with tab2:
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

    col1, col2, col3 = st.columns([3, 2, 1])
    with col1:
        ticker_scan = st.text_input("Ticker Symbol", placeholder="e.g. AAPL or 2222.SR or QNBK.QA", key="scan_ticker")
    with col2:
        if ticker_scan:
            m = detect_market(ticker_scan)
            st.markdown(f"<br><span style='font-size:0.9em'>{m['flag']} {m['label']} · {m['currency']}</span>", unsafe_allow_html=True)
    with col3:
        st.markdown("<br>", unsafe_allow_html=True)
        scan_btn = st.button("🔍 Scan", key="scan_btn", use_container_width=True)

    if scan_btn and ticker_scan:
        with st.spinner(f"Scanning {ticker_scan.upper()}..."):
            try:
                market_meta = detect_market(ticker_scan)
                info = get_info(ticker_scan)
                name = info.get("shortName") or ticker_scan.upper()
                st.subheader(f"{name} ({ticker_scan.upper()})  {market_meta['flag']}")

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
                    st.metric("Price", fmt_price(price, market_meta))
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

with tab3:
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
                from broker_agents.deals.analyze_stock_intake import (
                    build_ticker_analyze_stock_intake,
                    with_financials_provider,
                )
                from broker_agents.deals.analyze_stock_runner import execute_analyze_stock

                project_root  = Path(__file__).resolve().parent
                examples_root = project_root / "examples"
                outputs_root  = project_root / "data" / "outputs"
                fixtures_root = project_root / "tests" / "fixtures"
                portfolio_ctx = project_root / "examples" / "portfolio_context.yaml"
                ticker_up     = ticker_rep.upper()
                ticker_lw     = ticker_rep.lower()
                yaml_path     = examples_root / f"{ticker_lw}_input.yaml"

                if not yaml_path.exists():
                    st.info(f"No input file found for {ticker_up} — fetching data from yfinance to auto-generate it...")
                    yf_info = yf.Ticker(ticker_up).info
                    generate_input_yaml(ticker_up, yf_info, examples_root)
                    st.success(f"Generated {yaml_path.name}")

                intake = build_ticker_analyze_stock_intake(
                    ticker=ticker_up,
                    examples_root=examples_root,
                    outputs_root=outputs_root,
                    fixtures_root=fixtures_root,
                    portfolio_context=portfolio_ctx if portfolio_ctx.exists() else None,
                    financials_provider="sec_fixture",
                )
                intake = with_financials_provider(intake, intake.financials_provider, intake.financials_root)
                execution = execute_analyze_stock(intake=intake, input_mode="ticker")

            except Exception as e:
                st.error(f"Error: {e}")
                import traceback
                st.code(traceback.format_exc())
                execution = None

        # ── Visual display (outside spinner so it renders properly) ──────────
        if execution is not None:
            pkg   = execution.package_payload
            es    = pkg.get("executive_summary", {})
            resps = pkg.get("investor_responses", [])
            svm   = pkg.get("source_verification_matrix", {})
            wop   = pkg.get("backoffice_work_order_plan", {})

            company  = es.get("company_name") or ticker_up
            readiness = es.get("backoffice_readiness_label", "Unknown")
            src_status = es.get("source_verification_status", "unknown")
            n_responses = es.get("total_investor_responses", len(resps))

            # ── 1. Summary card ──────────────────────────────────────────────
            readiness_lower = readiness.lower()
            if "ready" in readiness_lower and "needs" not in readiness_lower and "not" not in readiness_lower:
                card_color, badge_bg = "#1a4731", "#22c55e"
            elif "needs work" in readiness_lower or "partial" in readiness_lower:
                card_color, badge_bg = "#4a3800", "#f59e0b"
            else:
                card_color, badge_bg = "#4a1010", "#ef4444"

            st.markdown(f"""
<div style="background:{card_color};border-radius:12px;padding:24px 28px;margin-bottom:20px">
  <div style="font-size:2rem;font-weight:700;color:#f8fafc">{ticker_up} &nbsp;<span style="font-size:1rem;font-weight:400;color:#cbd5e1">{company}</span></div>
  <div style="margin-top:12px;display:flex;gap:12px;flex-wrap:wrap;align-items:center">
    <span style="background:{badge_bg};color:#0f172a;border-radius:6px;padding:4px 12px;font-weight:600;font-size:0.9rem">{readiness}</span>
    <span style="color:#94a3b8;font-size:0.9rem">Source verification: <strong style="color:#e2e8f0">{src_status}</strong></span>
    <span style="color:#94a3b8;font-size:0.9rem">Investor responses: <strong style="color:#e2e8f0">{n_responses}</strong></span>
  </div>
</div>
""", unsafe_allow_html=True)

            # ── 2. Investor decision cards ───────────────────────────────────
            INVESTOR_ICONS = {
                "buffett": "🏦", "munger": "🧠", "fisher": "🔬",
                "lynch":   "📊", "bogle":  "📈",
            }
            INTEREST_COLORS = {
                "High Interest":       ("#14532d", "#22c55e"),
                "Conditional Interest":("#14532d", "#4ade80"),
                "Watchlist Interest":  ("#713f12", "#fbbf24"),
                "Needs More Evidence": ("#7c2d12", "#fb923c"),
                "Low Interest":        ("#7f1d1d", "#f87171"),
                "Not Interested":      ("#3b0764", "#c084fc"),
            }

            st.markdown("### Investor Decisions")
            cols = st.columns(len(resps) if resps else 1)
            for col, r in zip(cols, resps):
                investor   = r.get("investor", "?")
                icon       = INVESTOR_ICONS.get(investor.lower(), "👤")
                level      = r.get("interest_level", "Unknown")
                decision   = r.get("final_decision", "—")
                concern    = r.get("main_concern", "—")
                bg, badge  = INTEREST_COLORS.get(level, ("#1e293b", "#94a3b8"))
                with col:
                    st.markdown(f"""
<div style="background:{bg};border-radius:10px;padding:16px;height:100%">
  <div style="font-size:1.5rem">{icon}</div>
  <div style="font-weight:700;color:#f1f5f9;margin:4px 0">{investor.capitalize()}</div>
  <span style="background:{badge};color:#0f172a;border-radius:4px;padding:2px 8px;font-size:0.78rem;font-weight:600">{level}</span>
  <div style="color:#cbd5e1;font-size:0.82rem;margin-top:8px"><strong>Decision:</strong> {decision}</div>
  <div style="color:#94a3b8;font-size:0.78rem;margin-top:4px"><strong>Concern:</strong> {concern}</div>
</div>
""", unsafe_allow_html=True)

            st.markdown("")  # spacer

            # ── 3. Expandable sections ───────────────────────────────────────

            # Source Verification Matrix
            svm_cats = svm.get("categories", [])
            if svm_cats:
                with st.expander("🔍 Source Verification Matrix", expanded=False):
                    import pandas as pd
                    svm_rows = [{
                        "Category":      c.get("category", ""),
                        "Status":        c.get("status", ""),
                        "Blocks Promo":  "🚫 Yes" if c.get("blocks_promotion") else "✅ No",
                        "Broker Action": c.get("broker_action", ""),
                    } for c in svm_cats]
                    st.dataframe(pd.DataFrame(svm_rows), use_container_width=True, hide_index=True)

            # Per-investor full details
            st.markdown("### Investor Full Details")
            for r in resps:
                investor = r.get("investor", "?")
                icon     = INVESTOR_ICONS.get(investor.lower(), "👤")
                level    = r.get("interest_level", "")
                with st.expander(f"{icon} {investor.capitalize()} — {level}", expanded=False):
                    c1, c2 = st.columns(2)
                    with c1:
                        st.markdown(f"**Final Decision:** {r.get('final_decision','—')}")
                        st.markdown(f"**Interest Type:** {r.get('interest_type','—')}")
                        st.markdown(f"**Confidence:** {r.get('confidence','—')}")
                        st.markdown(f"**Main Positive Reason:** {r.get('main_positive_reason','—')}")
                    with c2:
                        st.markdown(f"**Main Concern:** {r.get('main_concern','—')}")
                        st.markdown(f"**Required Evidence:** {r.get('required_evidence_before_serious_interest','—')}")
                        st.markdown(f"**Safety Note:** {r.get('safety_note','—')}")
                    items = r.get("broker_follow_up_items") or []
                    if items:
                        st.markdown("**Broker Follow-Up Items:**")
                        for item in items:
                            st.write(f"• {item}")
                    # Full response letter
                    letter_path = execution.workflow_result.investor_response_letter_paths.get(investor.lower())
                    if letter_path and Path(letter_path).exists():
                        with st.expander(f"📄 Full Response Letter — {investor.capitalize()}", expanded=False):
                            st.markdown(Path(letter_path).read_text(encoding="utf-8"))

            # Backoffice Work Orders
            work_orders = wop.get("work_orders", [])
            if work_orders:
                with st.expander(f"🔧 Backoffice Work Orders ({len(work_orders)} total)", expanded=False):
                    import pandas as pd
                    wo_rows = [{
                        "ID":           wo.get("work_order_id", ""),
                        "Evidence":     wo.get("evidence_item", ""),
                        "Priority":     wo.get("priority", ""),
                        "Blocks Promo": "🚫" if wo.get("blocks_promotion") else "✅",
                        "Investors":    ", ".join(wo.get("related_investors") or []),
                        "Action":       wo.get("suggested_backoffice_action", ""),
                    } for wo in work_orders]
                    st.dataframe(pd.DataFrame(wo_rows), use_container_width=True, hide_index=True)

            # Next Actions
            next_actions = es.get("backoffice_next_actions") or []
            if next_actions:
                with st.expander("📋 Next Actions", expanded=False):
                    for action in next_actions:
                        st.write(f"• {action}")

            # ── 4. Download ──────────────────────────────────────────────────
            report_path = (
                execution.workflow_result.deal_output_dir
                / f"{ticker_lw}_broker_deal_package.md"
            )
            if report_path.exists():
                st.markdown("---")
                st.download_button(
                    label="💾 Download Full Report (.md)",
                    data=report_path.read_text(encoding="utf-8"),
                    file_name=f"{ticker_up}_broker_report.md",
                    mime="text/markdown"
                )


# ── Tab 3: Market Scanner ─────────────────────────────────────────────────────

_SP500_RAW = [
    "AAPL","MSFT","NVDA","AMZN","META","GOOGL","GOOG","BRK-B","LLY","AVGO",
    "JPM","TSLA","UNH","V","XOM","MA","COST","HD","PG","JNJ",
    "ABBV","NFLX","BAC","CRM","CVX","WMT","MRK","KO","AMD","PEP",
    "TMO","ACN","LIN","MCD","CSCO","ABT","NOW","ADBE","IBM","TXN",
    "GE","PM","DHR","ISRG","CAT","GS","INTU","SPGI","AMGN","PFE",
    "BKNG","RTX","NEE","HON","MS","BLK","SYK","T","VRTX","DE",
    "LOW","SCHW","BA","UBER","MDT","C","CB","AXP","ELV","PLD",
    "AMAT","ADI","MU","LRCX","REGN","MMC","ETN","CI","ZTS","SO",
    "DUK","AON","BSX","CME","KLAC","ITW","TJX","MDLZ","NOC","FI",
    "SHW","PNC","WM","USB","GD","EMR","MCO","APD","HCA","PANW",
]
_seen_sp: set = set()
SP500_TICKERS: list[str] = []
for _t in _SP500_RAW:
    if _t not in _seen_sp:
        _seen_sp.add(_t)
        SP500_TICKERS.append(_t)

SAUDI_TICKERS = [f"{n}.SR" for n in [
    "2222","1120","2010","1180","2380","4200","7010","1211","2350","2330",
    "1302","4030","2001","3010","1050","2020","4240","1020","3020","2060",
    "4500","1010","2050","4001","2070","1030","2040","3050","4130","2080",
]]

QATAR_TICKERS = [f"{n}.QA" for n in [
    "QNBK","QIBK","MARK","CBQK","DHBK","ORDS","IQCD","QGTS","IGRD","UDCD",
    "NLCS","MCCS","QFLS","AKHI","BLDN","MPHC","GWCS","VFQS","SIIS","DBIS",
]]

MARKET_UNIVERSES = {
    "🇺🇸 S&P 500 (US)":          {"tickers": SP500_TICKERS, "meta": detect_market("AAPL"),  "size_options": [50, 100]},
    "🇸🇦 Saudi Market (Tadawul)": {"tickers": SAUDI_TICKERS, "meta": detect_market("2222.SR"), "size_options": [30]},
    "🇶🇦 Qatar Market (QSE)":     {"tickers": QATAR_TICKERS, "meta": detect_market("QNBK.QA"), "size_options": [20]},
}


def quick_scan(ticker: str, market: dict) -> dict | None:
    """Fetch only key criteria fields — fast and lightweight."""
    try:
        info = yf.Ticker(ticker).info
        if not info.get("totalRevenue"):
            return None
        return {
            "ticker":     ticker,
            "name":       info.get("shortName") or ticker,
            "price":      info.get("currentPrice") or info.get("regularMarketPrice"),
            "currency":   market["symbol"],
            "pe":         info.get("trailingPE"),
            "fcf_pos":    (info.get("freeCashflow") or 0) > 0,
            "rev_g":      (info.get("revenueGrowth") or 0) > 0.10,
            "ni_pos":     (info.get("netIncomeToCommon") or 0) > 0,
            "margin":     (info.get("operatingMargins") or 0) > 0.15,
            "roe":        (info.get("returnOnEquity") or 0) > 0.15,
            "rev_g_pct":  round((info.get("revenueGrowth") or 0) * 100, 1),
            "margin_pct": round((info.get("operatingMargins") or 0) * 100, 1),
            "roe_pct":    round((info.get("returnOnEquity") or 0) * 100, 1),
        }
    except Exception:
        return None


def passes_top5(r: dict) -> bool:
    """Top 5 criteria that no investor skips."""
    pe_ok = 0 < (r.get("pe") or 999) < 30
    return all([r["fcf_pos"], r["rev_g"], r["ni_pos"], r["margin"], pe_ok])


with tab1:
    st.header("Market Scanner")

    with st.expander("📖 Logic 3 — Scanner Criteria", expanded=False):
        st.markdown("""
### Top 5 Universal Criteria (must pass all 5)
| # | Criterion | Threshold | Why |
|---|-----------|-----------|-----|
| 1 | Free Cash Flow | > 0 | Every investor requires positive FCF |
| 2 | Revenue Growth | > 10% | Minimum growth signal |
| 3 | Net Income | > 0 | Profitable business |
| 4 | Operating Margin | > 15% | Pricing power and efficiency |
| 5 | P/E Ratio | < 30 | Valuation discipline |

### Output
Stocks passing all 5 criteria appear in a sortable table.
Copy any ticker to Tab 2 for full five-investor analysis.

### Note
First-pass filter only — not a recommendation or ranking.
        """)

    col1, col2, col3 = st.columns([2, 2, 1])
    with col1:
        market_choice = st.selectbox("Market", options=list(MARKET_UNIVERSES.keys()), key="market_choice")
    with col2:
        universe_cfg  = MARKET_UNIVERSES[market_choice]
        size_options  = universe_cfg["size_options"]
        universe_size = st.selectbox(
            "Universe Size",
            options=size_options,
            index=0,
            format_func=lambda x: f"Top {x} stocks",
            key="universe_size",
        )
    with col3:
        st.markdown("<br>", unsafe_allow_html=True)
        scan_market_btn = st.button("🔭 Run Scan", key="market_scan_btn", use_container_width=True)

    if scan_market_btn:
        scan_meta      = universe_cfg["meta"]
        tickers_to_scan = universe_cfg["tickers"][:universe_size]
        total = len(tickers_to_scan)

        progress_bar = st.progress(0, text="Starting scan...")
        passed_list = []
        failed_count = 0
        error_count = 0

        for i, ticker in enumerate(tickers_to_scan):
            progress_bar.progress(
                (i + 1) / total,
                text=f"Scanning {ticker} ({i+1}/{total}) — {len(passed_list)} candidates found so far..."
            )
            r = quick_scan(ticker, scan_meta)
            if r is None:
                error_count += 1
                continue
            if passes_top5(r):
                passed_list.append(r)
            else:
                failed_count += 1

        progress_bar.progress(1.0, text="Scan complete!")

        st.markdown("---")
        col_a, col_b, col_c, col_d = st.columns(4)
        with col_a:
            st.metric("Scanned", total)
        with col_b:
            st.metric("Passed All 5", len(passed_list))
        with col_c:
            st.metric("Rejected", failed_count)
        with col_d:
            pass_rate = round(len(passed_list) / total * 100, 1) if total > 0 else 0
            st.metric("Pass Rate", f"{pass_rate}%")

        if passed_list:
            st.markdown(f"### Candidates Passing All 5 Criteria — {len(passed_list)} stocks")

            import pandas as pd
            price_col = f"Price ({scan_meta['currency']})"
            df = pd.DataFrame([{
                "Ticker":       r["ticker"],
                "Company":      r["name"],
                price_col:      round(r["price"], 2) if r["price"] else "N/A",
                "P/E":          round(r["pe"], 1) if r["pe"] else "N/A",
                "Rev Growth %": r["rev_g_pct"],
                "Op Margin %":  r["margin_pct"],
                "ROE %":        r["roe_pct"],
                "FCF":          "Yes",
            } for r in passed_list])

            st.dataframe(df, use_container_width=True, hide_index=True)

            csv = df.to_csv(index=False)
            st.download_button(
                label="💾 Download Candidate List (CSV)",
                data=csv,
                file_name=f"{market_choice.split()[1].lower()}_scan_results.csv",
                mime="text/csv"
            )

            st.info("Copy any ticker above to Tab 2 for full five-investor analysis.")
        else:
            st.warning("No stocks passed all 5 criteria.")
