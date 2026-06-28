import streamlit as st
import yfinance as yf
import sys
import os
from datetime import date
from pathlib import Path

import yaml

try:
    import anthropic as _anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False

try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).resolve().parent / ".env.local")
except ImportError:
    pass

# Ensure the repo's src/ tree is first on sys.path so all broker_agents
# imports resolve to the local source, not the potentially stale site-packages.
_SRC = Path(__file__).resolve().parent / "src"
if str(_SRC) in sys.path:
    sys.path.remove(str(_SRC))
sys.path.insert(0, str(_SRC))

st.set_page_config(page_title="Broker Investor Agents", layout="wide", page_icon="📊")

# ── DEBUG: sidebar + main-area button (remove once confirmed working) ─────────
st.sidebar.write(f"SIDEBAR TEST | anthropic={ANTHROPIC_AVAILABLE}")
if st.button("🌐 EN/AR"):
    if st.session_state.get("lang", "en") == "en":
        st.session_state["lang"] = "ar"
    else:
        st.session_state["lang"] = "en"
    st.rerun()

# ── Auth gate ─────────────────────────────────────────────────────────────────

def _required_password() -> str | None:
    """Return APP_PASSWORD from secrets, or None if not configured (local dev)."""
    try:
        return st.secrets.get("APP_PASSWORD") or None
    except Exception:
        return None

if not st.session_state.get("authenticated"):
    required = _required_password()
    if required is None:
        st.session_state["authenticated"] = True
    else:
        _, col, _ = st.columns([1, 1, 1])
        with col:
            st.markdown("<br><br>", unsafe_allow_html=True)
            st.markdown("## 📊 Broker Investor Agents")
            st.caption("Investment screening and independent investor analysis system")
            st.markdown("<br>", unsafe_allow_html=True)
            pwd = st.text_input("Password", type="password", key="_login_pwd")
            if st.button("Login", use_container_width=True):
                if pwd == required:
                    st.session_state["authenticated"] = True
                    st.rerun()
                else:
                    st.error("Incorrect password")
        st.stop()

# ── Language support ──────────────────────────────────────────────────────────

if "lang" not in st.session_state:
    st.session_state["lang"] = "en"


def _anthropic_api_key() -> str | None:
    """Return ANTHROPIC_API_KEY from env (loaded via .env.local) or Streamlit secrets."""
    key = os.getenv("ANTHROPIC_API_KEY")
    if key:
        return key
    try:
        return st.secrets.get("ANTHROPIC_API_KEY") or None
    except Exception:
        return None


def translate_to_arabic(text: str) -> str:
    if not ANTHROPIC_AVAILABLE:
        raise RuntimeError("anthropic package not installed")
    api_key = _anthropic_api_key()
    if not api_key:
        raise RuntimeError("ANTHROPIC_API_KEY not found in .env.local or Streamlit secrets")
    client = _anthropic.Anthropic(api_key=api_key)
    msg = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=500,
        messages=[{"role": "user", "content": f"Translate this investment/financial text to Arabic. Return ONLY the Arabic translation, nothing else: {text}"}],
    )
    return msg.content[0].text.strip()


def t(text: str) -> str:
    """Return text translated to Arabic when lang='ar', otherwise return as-is."""
    if st.session_state.get("lang") != "ar":
        return text
    cache_key = f"tr_{hash(text)}"
    if cache_key not in st.session_state:
        try:
            st.session_state[cache_key] = translate_to_arabic(text)
        except Exception as _e:
            # Store the error marker so we don't retry every render, but surface it once
            st.session_state[cache_key] = text
            st.session_state["_translation_error"] = str(_e)
    return st.session_state[cache_key]


# ── Investor Personas ─────────────────────────────────────────────────────────

PERSONAS = {
    "buffett": {
        "internal": "Warren Buffett",
        "en": "The Value Seeker",
        "ar": "باحث القيمة",
        "icon": "🏛️",
        "philosophy": """You are an investment analyst who applies the investment \
philosophy and methodology of Warren Buffett. Analyze using these principles:
- Durable competitive advantage (economic moat)
- Strong and consistent free cash flow
- Honest, capable, and shareholder-friendly management
- Intrinsic value with margin of safety
- Long-term business quality over short-term price movements
- Return on equity and capital allocation discipline""",
    },
    "munger": {
        "internal": "Charlie Munger",
        "en": "The Rationalist",
        "ar": "العقلاني",
        "icon": "🧠",
        "philosophy": """You are an investment analyst who applies the investment \
philosophy and methodology of Charlie Munger. Analyze using these principles:
- Business quality and simplicity over complexity
- Management incentives and integrity
- Mental models and inversion thinking (what could go wrong?)
- Avoiding psychological biases and errors
- Concentrated positions in truly great businesses
- Patience and discipline — fewer but better decisions""",
    },
    "fisher": {
        "internal": "Philip Fisher",
        "en": "The Growth Hunter",
        "ar": "صائد النمو",
        "icon": "🔬",
        "philosophy": """You are an investment analyst who applies the investment \
philosophy and methodology of Philip Fisher. Analyze using these principles:
- Long-term qualitative growth potential
- Management depth, integrity, and research culture
- Scuttlebutt method: customer, supplier, competitor insights
- Sales organization strength and product pipeline
- Profit margins sustainability and improvement trends
- Conservative accounting and financial transparency""",
    },
    "lynch": {
        "internal": "Peter Lynch",
        "en": "The Story Finder",
        "ar": "كاشف القصص",
        "icon": "📊",
        "philosophy": """You are an investment analyst who applies the investment \
philosophy and methodology of Peter Lynch. Analyze using these principles:
- Invest in what you understand — clear business story
- PEG ratio as primary valuation tool
- Category classification: slow grower, stalwart, fast grower, cyclical, turnaround, asset play
- Earnings growth durability and consistency
- Avoid over-diversification — focus on best ideas
- Institutional neglect as opportunity signal""",
    },
    "bogle": {
        "internal": "John Bogle",
        "en": "The Index Keeper",
        "ar": "حارس المؤشر",
        "icon": "📈",
        "philosophy": """You are an investment analyst who applies the investment \
philosophy and methodology of John Bogle. Analyze using these principles:
- Cost efficiency — fees and expenses matter enormously
- Broad diversification over concentration
- Individual stock vs broad index comparison
- Long-term market returns vs active management
- Simplicity and discipline over complexity
- Benchmark exposure: does owning this add value vs just buying the index?""",
    },
}


def persona_display(key: str) -> str:
    """Return the display name for a persona in the current language."""
    lang = st.session_state.get("lang", "en")
    p = PERSONAS.get(key.lower(), {})
    return p.get(lang, p.get("en", key))


def persona_icon(key: str) -> str:
    return PERSONAS.get(key.lower(), {}).get("icon", "👤")


def run_ai_investor_analysis(persona_key: str, company_data: dict) -> str | None:
    """Run real AI analysis using Claude API with investor philosophy. Returns None on failure."""
    if not ANTHROPIC_AVAILABLE:
        return None
    api_key = _anthropic_api_key()
    if not api_key:
        return None

    persona = PERSONAS.get(persona_key.lower(), {})
    philosophy = persona.get("philosophy", "")

    company_info = f"""
Company: {company_data.get('name', 'Unknown')}
Ticker: {company_data.get('ticker', 'N/A')}
Sector: {company_data.get('sector', 'N/A')}
Current Price: {company_data.get('price', 'N/A')}
P/E Ratio: {company_data.get('pe', 'N/A')}
Revenue Growth: {company_data.get('revenue_growth', 'N/A')}%
Operating Margin: {company_data.get('operating_margin', 'N/A')}%
Free Cash Flow: {company_data.get('fcf', 'N/A')}
ROE: {company_data.get('roe', 'N/A')}%
Debt/Equity: {company_data.get('debt_equity', 'N/A')}
Market Cap: {company_data.get('market_cap', 'N/A')}
Business Description: {company_data.get('description', 'N/A')}
"""

    prompt = f"""{philosophy}

Analyze this company and provide your assessment:

{company_info}

Provide a structured analysis with:
1. DECISION: One of [Strong Interest / Conditional Interest / Watchlist / Needs More Evidence / Low Interest / Pass]
2. MAIN POSITIVE: Key strength from your philosophy perspective (2-3 sentences)
3. MAIN CONCERN: Primary concern or blocker (2-3 sentences)
4. REQUIRED EVIDENCE: What additional information would change your view (1-2 sentences)
5. SUMMARY: Overall 3-4 sentence investment thesis from your philosophical perspective

Be specific to this company's actual data. Do not give generic responses.
Format your response clearly with these 5 labeled sections."""

    _NAME_SUB = {
        "Buffett": "The Value Seeker",
        "Munger":  "The Rationalist",
        "Fisher":  "The Growth Hunter",
        "Lynch":   "The Story Finder",
        "Bogle":   "The Index Keeper",
    }
    try:
        client = _anthropic.Anthropic(api_key=api_key)
        msg = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=600,
            messages=[{"role": "user", "content": prompt}],
        )
        text = msg.content[0].text
        for _raw, _disp in _NAME_SUB.items():
            text = text.replace(_raw, _disp)
        return text
    except Exception:
        return None


# RTL CSS injection for Arabic
if st.session_state["lang"] == "ar":
    st.markdown("""
<style>
    .stMarkdown p, .stMarkdown h1, .stMarkdown h2, .stMarkdown h3,
    .stMarkdown h4, .stMarkdown li, .stMarkdown td, .stMarkdown th,
    [data-testid="stMetricLabel"], [data-testid="stMetricValue"],
    [data-testid="stExpander"] summary, .stCaption, .stAlert p {
        direction: rtl;
        text-align: right;
    }
</style>
""", unsafe_allow_html=True)

# ── Sidebar language toggle ───────────────────────────────────────────────────

st.sidebar.markdown("### 🌐 Language")
if st.session_state.get("lang", "en") == "en":
    if st.sidebar.button("Switch to Arabic / عربي"):
        st.session_state["lang"] = "ar"
        for _k in list(st.session_state.keys()):
            if _k.startswith("tr_"):
                del st.session_state[_k]
        st.rerun()
else:
    if st.sidebar.button("Switch to English"):
        st.session_state["lang"] = "en"
        for _k in list(st.session_state.keys()):
            if _k.startswith("tr_"):
                del st.session_state[_k]
        st.rerun()

if st.session_state.get("_translation_error"):
    st.sidebar.warning(f"Translation error: {st.session_state['_translation_error']}")

# ── Title ────────────────────────────────────────────────────────────────────

st.title("📊 Broker Investor Agents")
st.caption(t("Investment screening and independent investor analysis system"))

tab1, tab2, tab3, tab4, tab5 = st.tabs([
    t("🔭 Tab 1 — Market Scanner"),
    t("📡 Tab 2 — Initial Scan"),
    t("📋 Tab 3 — Five Investor Reports"),
    t("📁 Tab 4 — Portfolio Manager"),
    t("🏢 Tab 5 — Private Company"),
])


# ── YAML generator ────────────────────────────────────────────────────────────

def generate_input_yaml(ticker: str, info: dict, examples_root: Path) -> Path:
    """Generate a minimal valid input YAML for ticker and save to examples/."""
    tk = ticker.upper()
    tl = ticker.lower()
    today = date.today().isoformat()

    name        = info.get("longName") or info.get("shortName") or tk
    exchange    = info.get("exchange") or "NYSE"
    currency    = info.get("financialCurrency") or "USD"
    sector      = info.get("sector") or "Unknown"
    industry    = info.get("industry") or "Unknown"
    fy_end      = info.get("lastFiscalYearEnd") or ""

    revenue      = info.get("totalRevenue") or 0
    gross_profit = info.get("grossProfits") or 0
    op_income    = info.get("operatingIncome") or 0
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

    data = {
        "metadata": {
            "schema_name": "backoffice_data_pack_v2",
            "schema_version": 2,
            "company_name": name,
            "ticker": tk,
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
            "ticker": tk,
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
                    "source_name": f"{tk} yfinance auto-fetch",
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


# ── Portfolio log helpers ─────────────────────────────────────────────────────

import base64
import json
import requests as _requests

_PORTFOLIO_LOG  = Path(__file__).resolve().parent / "data" / "portfolio_log.json"
_GH_REPO        = "agamaded-sudo/broker-investor-agents-lite"
_GH_FILE_PATH   = "data/portfolio_log.json"
_GH_API_URL     = f"https://api.github.com/repos/{_GH_REPO}/contents/{_GH_FILE_PATH}"


def _gh_token() -> str | None:
    """Return GitHub token from Streamlit secrets, or None if absent."""
    try:
        return st.secrets.get("GITHUB_TOKEN")
    except Exception:
        return None


def _gh_headers(token: str) -> dict:
    return {"Authorization": f"token {token}", "Accept": "application/vnd.github+json"}


def _gh_fetch() -> tuple[list[dict], str | None]:
    """Fetch portfolio JSON from GitHub. Returns (entries, sha)."""
    token = _gh_token()
    if not token:
        return [], None
    try:
        resp = _requests.get(_GH_API_URL, headers=_gh_headers(token), timeout=10)
        if resp.status_code == 404:
            return [], None
        resp.raise_for_status()
        data = resp.json()
        content = base64.b64decode(data["content"]).decode("utf-8")
        return json.loads(content), data["sha"]
    except Exception:
        return [], None


def _gh_push(entries: list[dict], sha: str | None, commit_msg: str) -> bool:
    """Push updated portfolio JSON to GitHub. Returns True on success."""
    token = _gh_token()
    if not token:
        return False
    try:
        content_b64 = base64.b64encode(
            json.dumps(entries, indent=2, ensure_ascii=False).encode("utf-8")
        ).decode("ascii")
        body: dict = {"message": commit_msg, "content": content_b64}
        if sha:
            body["sha"] = sha
        resp = _requests.put(_GH_API_URL, headers=_gh_headers(token), json=body, timeout=15)
        resp.raise_for_status()
        return True
    except Exception:
        return False


@st.cache_data(ttl=60)
def _load_portfolio_cached() -> tuple[list[dict], str | None]:
    """Load from GitHub (preferred) then fall back to local file. Cached 60 s."""
    entries, sha = _gh_fetch()
    if entries:
        # Keep local copy in sync so CLI tools still work
        _PORTFOLIO_LOG.parent.mkdir(parents=True, exist_ok=True)
        _PORTFOLIO_LOG.write_text(json.dumps(entries, indent=2, ensure_ascii=False), encoding="utf-8")
        return entries, sha
    # GitHub not available — use local file
    if _PORTFOLIO_LOG.exists():
        try:
            return json.loads(_PORTFOLIO_LOG.read_text(encoding="utf-8")), None
        except Exception:
            pass
    return [], None


def _load_portfolio() -> list[dict]:
    entries, _ = _load_portfolio_cached()
    return list(entries)


def _save_portfolio(entries: list[dict], commit_msg: str = "Portfolio update") -> None:
    """Write local file, push to GitHub, then bust the cache."""
    _PORTFOLIO_LOG.parent.mkdir(parents=True, exist_ok=True)
    _PORTFOLIO_LOG.write_text(json.dumps(entries, indent=2, ensure_ascii=False), encoding="utf-8")
    # Fetch current SHA before pushing (cache may be stale)
    _, sha = _gh_fetch()
    _gh_push(entries, sha, commit_msg)
    # Invalidate cache so next _load_portfolio_cached() re-fetches
    _load_portfolio_cached.clear()


def _portfolio_should_save(score: int, triggers: list[str], investor_decisions: dict[str, str]) -> tuple[bool, list[str]]:
    """Return (should_save, reasons) based on auto-save criteria."""
    reasons: list[str] = []
    if score >= 6:
        reasons.append("score>=6")
    if investor_decisions.get("munger", "").lower().startswith("conditional interest"):
        reasons.append("munger=conditional")
    buffett = investor_decisions.get("buffett", "").lower()
    if any(k in buffett for k in ("conditional interest", "watchlist interest", "high interest")):
        reasons.append("buffett>=watchlist")
    if len(triggers) >= 2:
        reasons.append(f"golden_triggers={len(triggers)}")
    return bool(reasons), reasons


def _upsert_portfolio_entry(entry: dict) -> str:
    """Insert or update an entry; return 'added' or 'updated'."""
    entries = _load_portfolio()
    for i, e in enumerate(entries):
        if e.get("ticker") == entry["ticker"]:
            entry.setdefault("status", e.get("status", "watching"))
            entry.setdefault("notes", e.get("notes", ""))
            entries[i] = entry
            msg = f"Portfolio update: {entry['ticker']} {entry.get('status','watching')} {entry.get('date_added','')}"
            _save_portfolio(entries, msg)
            return "updated"
    entries.append(entry)
    msg = f"Portfolio update: {entry['ticker']} added {entry.get('date_added','')}"
    _save_portfolio(entries, msg)
    return "added"

# ── Tab 1: Initial Scan ───────────────────────────────────────────────────────

with tab2:
    st.header(t("Initial Scan — Opportunity Scout"))

    with st.expander(t("📖 Logic 1 — Screening Rules"), expanded=False):
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
        ticker_scan = st.text_input(t("Ticker Symbol"), placeholder="e.g. AAPL or 2222.SR or QNBK.QA", key="scan_ticker")
    with col2:
        if ticker_scan:
            m = detect_market(ticker_scan)
            st.markdown(f"<br><span style='font-size:0.9em'>{m['flag']} {m['label']} · {m['currency']}</span>", unsafe_allow_html=True)
    with col3:
        st.markdown("<br>", unsafe_allow_html=True)
        scan_btn = st.button(t("🔍 Scan"), key="scan_btn", use_container_width=True)

    if scan_btn and ticker_scan:
        with st.spinner(f"Scanning {ticker_scan.upper()}..."):
            try:
                market_meta = detect_market(ticker_scan)
                info = get_info(ticker_scan)
                name = info.get("shortName") or ticker_scan.upper()
                st.subheader(f"{name} ({ticker_scan.upper()})  {market_meta['flag']}")

                # Gate 0
                st.markdown(f"#### 🚦 {t('Gate 0 — Hard Filters')}")
                gate_ok, gate_issues = gate0(info)
                if gate_ok:
                    st.success(t("Passed Gate 0 — Stock is listed, tradable, and has financial data"))
                else:
                    st.error(t("Failed Gate 0 — Stock rejected"))
                    for issue in gate_issues:
                        st.write(f"• {issue}")
                    st.stop()

                # Score
                st.markdown(f"#### 📈 {t('Opportunity Score')}")
                score, passed, failed = opportunity_score(info)

                price = info.get("currentPrice") or info.get("regularMarketPrice")
                pe    = info.get("trailingPE")
                decision = t("✅ Pass") if score >= 8 else t("👁 Watchlist") if score >= 6 else t("❌ Reject")

                col_a, col_b, col_c, col_d = st.columns(4)
                with col_a:
                    st.metric(t("Score"), f"{score} / 10")
                with col_b:
                    st.metric(t("Decision"), decision)
                with col_c:
                    st.metric(t("Price"), fmt_price(price, market_meta))
                with col_d:
                    pe_str = f"{pe:.1f}" if pe else "N/A"
                    st.metric("P/E", pe_str)

                col_p, col_f = st.columns(2)
                with col_p:
                    st.markdown(f"**{t('✅ Passed Criteria')}**")
                    for p in passed:
                        st.write(f"• {p}")
                with col_f:
                    st.markdown(f"**{t('❌ Failed Criteria')}**")
                    for f in failed:
                        st.write(f"• {f}")

                # Golden Triggers
                triggers = golden_triggers(info)
                if triggers:
                    st.markdown(f"#### 🌟 {t('Golden Triggers Detected')}")
                    st.info(t("Strong signals found — stock qualifies even without a full score"))
                    for trig in triggers:
                        st.write(f"• {trig}")

                # Cache for portfolio auto-save in Tab 3
                st.session_state[f"scan_{ticker_scan.upper()}"] = {
                    "score": score, "triggers": triggers, "price": price,
                    "market": market_meta,
                }

            except Exception as e:
                st.error(f"Error: {e}")


# ── Tab 2: Five Investor Reports ──────────────────────────────────────────────

with tab3:
    st.header(t("Five Investor Reports"))

    with st.expander(t("📖 Logic 2 — How Reports Are Generated"), expanded=False):
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
        ticker_rep = st.text_input(t("Ticker Symbol"), placeholder="e.g. MSFT", key="rep_ticker")
    with col2:
        st.markdown("<br>", unsafe_allow_html=True)
        rep_btn = st.button(t("📋 Analyze"), key="rep_btn", use_container_width=True)

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

            company   = es.get("company_name") or ticker_up
            readiness = es.get("backoffice_readiness_label", "Unknown")
            src_status = es.get("source_verification_status", "unknown")
            n_responses = es.get("total_investor_responses", len(resps))

            # ── Auto-save to portfolio log ───────────────────────────────────
            inv_decisions = {r["investor"].lower(): r.get("interest_level", "") for r in resps}
            scan_cache    = st.session_state.get(f"scan_{ticker_up}", {})
            opp_score     = scan_cache.get("score", 0)
            gt_list       = scan_cache.get("triggers", [])
            price_at_analysis = scan_cache.get("price") or (
                yf.Ticker(ticker_up).info.get("currentPrice")
                or yf.Ticker(ticker_up).info.get("regularMarketPrice")
            )
            mkt = scan_cache.get("market") or detect_market(ticker_up)
            should_save, save_reasons = _portfolio_should_save(opp_score, gt_list, inv_decisions)
            if should_save:
                entry = {
                    "ticker":              ticker_up,
                    "company":             company,
                    "date_added":          date.today().isoformat(),
                    "market":              mkt.get("label", "US"),
                    "currency":            mkt.get("currency", "USD"),
                    "price_at_analysis":   round(float(price_at_analysis), 2) if price_at_analysis else None,
                    "opportunity_score":   opp_score,
                    "golden_triggers":     len(gt_list),
                    "buffett_decision":    inv_decisions.get("buffett", ""),
                    "munger_decision":     inv_decisions.get("munger", ""),
                    "fisher_decision":     inv_decisions.get("fisher", ""),
                    "lynch_decision":      inv_decisions.get("lynch", ""),
                    "bogle_decision":      inv_decisions.get("bogle", ""),
                    "save_reason":         save_reasons,
                    "status":              "watching",
                    "notes":               "",
                }
                action = _upsert_portfolio_entry(entry)
                st.toast(f"{ticker_up} {action} in portfolio log", icon="📁")

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
    <span style="background:{badge_bg};color:#0f172a;border-radius:6px;padding:4px 12px;font-weight:600;font-size:0.9rem">{t(readiness)}</span>
    <span style="color:#94a3b8;font-size:0.9rem">{t('Source verification')}: <strong style="color:#e2e8f0">{src_status}</strong></span>
    <span style="color:#94a3b8;font-size:0.9rem">{t('Investor responses')}: <strong style="color:#e2e8f0">{n_responses}</strong></span>
  </div>
</div>
""", unsafe_allow_html=True)

            # ── 2. Investor decision cards (summary row) ─────────────────────
            INTEREST_COLORS = {
                "High Interest":       ("#14532d", "#22c55e"),
                "Conditional Interest":("#14532d", "#4ade80"),
                "Watchlist Interest":  ("#713f12", "#fbbf24"),
                "Needs More Evidence": ("#7c2d12", "#fb923c"),
                "Low Interest":        ("#7f1d1d", "#f87171"),
                "Not Interested":      ("#3b0764", "#c084fc"),
            }

            st.markdown(f"### {t('Investor Decisions')}")
            cols = st.columns(len(resps) if resps else 1)
            for col, r in zip(cols, resps):
                investor  = r.get("investor", "?")
                icon      = persona_icon(investor)
                disp_name = persona_display(investor)
                level     = r.get("interest_level", "Unknown")
                decision  = r.get("final_decision", "—")
                concern   = r.get("main_concern", "—")
                bg, badge = INTEREST_COLORS.get(level, ("#1e293b", "#94a3b8"))
                with col:
                    st.markdown(f"""
<div style="background:{bg};border-radius:10px;padding:16px;height:100%">
  <div style="font-size:1.5rem">{icon}</div>
  <div style="font-weight:700;color:#f1f5f9;margin:4px 0">{disp_name}</div>
  <span style="background:{badge};color:#0f172a;border-radius:4px;padding:2px 8px;font-size:0.78rem;font-weight:600">{t(level)}</span>
  <div style="color:#cbd5e1;font-size:0.82rem;margin-top:8px"><strong>{t('Decision')}:</strong> {t(decision)}</div>
  <div style="color:#94a3b8;font-size:0.78rem;margin-top:4px"><strong>{t('Concern')}:</strong> {t(concern)}</div>
</div>
""", unsafe_allow_html=True)

            st.markdown("")  # spacer

            # ── 3. Unified per-analyst AI expanders ──────────────────────────
            # Build company_data once from yfinance for all AI calls
            _ticker_info = yf.Ticker(ticker_up).info
            _company_data = {
                "name":             _ticker_info.get("shortName", ticker_up),
                "ticker":           ticker_up,
                "sector":           _ticker_info.get("sector", "N/A"),
                "price":            _ticker_info.get("currentPrice", "N/A"),
                "pe":               _ticker_info.get("trailingPE", "N/A"),
                "revenue_growth":   round((_ticker_info.get("revenueGrowth", 0) or 0) * 100, 1),
                "operating_margin": round((_ticker_info.get("operatingMargins", 0) or 0) * 100, 1),
                "fcf":              _ticker_info.get("freeCashflow", "N/A"),
                "roe":              round((_ticker_info.get("returnOnEquity", 0) or 0) * 100, 1),
                "debt_equity":      _ticker_info.get("debtToEquity", "N/A"),
                "market_cap":       _ticker_info.get("marketCap", "N/A"),
                "description":      (_ticker_info.get("longBusinessSummary", "N/A") or "N/A")[:500],
            }
            _ai_available = bool(ANTHROPIC_AVAILABLE and _anthropic_api_key())

            st.markdown(f"### {t('Investor Full Details')}")
            for r in resps:
                investor  = r.get("investor", "?")
                icon      = persona_icon(investor)
                disp_name = persona_display(investor)
                level     = r.get("interest_level", "")
                with st.expander(f"{icon} {disp_name} — {t(level)}", expanded=False):
                    if _ai_available:
                        with st.spinner(f"{t('Running AI deep analysis')}..."):
                            ai_text = run_ai_investor_analysis(investor, _company_data)
                        if ai_text:
                            st.markdown(ai_text)
                        else:
                            st.caption(t("AI analysis unavailable — showing rule-based details"))
                            _show_rule_based(r, investor, execution)
                    else:
                        _show_rule_based(r, investor, execution)

            # ── 4. Supporting sections ────────────────────────────────────────
            # Source Verification Matrix
            svm_cats = svm.get("categories", [])
            if svm_cats:
                with st.expander(t("🔍 Source Verification Matrix"), expanded=False):
                    import pandas as pd
                    svm_rows = [{
                        t("Category"):      c.get("category", ""),
                        t("Status"):        c.get("status", ""),
                        t("Blocks Promo"):  "🚫 Yes" if c.get("blocks_promotion") else "✅ No",
                        t("Broker Action"): c.get("broker_action", ""),
                    } for c in svm_cats]
                    st.dataframe(pd.DataFrame(svm_rows), use_container_width=True, hide_index=True)

            # Backoffice Work Orders
            work_orders = wop.get("work_orders", [])
            if work_orders:
                with st.expander(f"🔧 {t('Backoffice Work Orders')} ({len(work_orders)} {t('total')})", expanded=False):
                    import pandas as pd
                    wo_rows = [{
                        t("ID"):           wo.get("work_order_id", ""),
                        t("Evidence"):     wo.get("evidence_item", ""),
                        t("Priority"):     wo.get("priority", ""),
                        t("Blocks Promo"): "🚫" if wo.get("blocks_promotion") else "✅",
                        t("Investors"):    ", ".join(wo.get("related_investors") or []),
                        t("Action"):       wo.get("suggested_backoffice_action", ""),
                    } for wo in work_orders]
                    st.dataframe(pd.DataFrame(wo_rows), use_container_width=True, hide_index=True)

            # Next Actions
            next_actions = es.get("backoffice_next_actions") or []
            if next_actions:
                with st.expander(f"📋 {t('Next Actions')}", expanded=False):
                    for action in next_actions:
                        st.write(f"• {t(action)}")

            # ── 5. Download ───────────────────────────────────────────────────
            _PERSONA_NAME_MAP = {
                "Buffett": "The Value Seeker",
                "Munger":  "The Rationalist",
                "Fisher":  "The Growth Hunter",
                "Lynch":   "The Story Finder",
                "Bogle":   "The Index Keeper",
            }
            report_path = (
                execution.workflow_result.deal_output_dir
                / f"{ticker_lw}_broker_deal_package.md"
            )
            if report_path.exists():
                report_text = report_path.read_text(encoding="utf-8")
                for _raw, _display in _PERSONA_NAME_MAP.items():
                    report_text = report_text.replace(_raw, _display)
                st.markdown("---")
                st.download_button(
                    label=t("💾 Download Full Report (.md)"),
                    data=report_text,
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
for _sp in _SP500_RAW:
    if _sp not in _seen_sp:
        _seen_sp.add(_sp)
        SP500_TICKERS.append(_sp)

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
    st.header(t("Market Scanner"))

    with st.expander(t("📖 Logic 3 — Scanner Criteria"), expanded=False):
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
        market_choice = st.selectbox(t("Market"), options=list(MARKET_UNIVERSES.keys()), key="market_choice")
    with col2:
        universe_cfg  = MARKET_UNIVERSES[market_choice]
        size_options  = universe_cfg["size_options"]
        universe_size = st.selectbox(
            t("Universe Size"),
            options=size_options,
            index=0,
            format_func=lambda x: f"{t('Top')} {x} {t('stocks')}",
            key="universe_size",
        )
    with col3:
        st.markdown("<br>", unsafe_allow_html=True)
        scan_market_btn = st.button(t("🔭 Run Scan"), key="market_scan_btn", use_container_width=True)

    if scan_market_btn:
        scan_meta      = universe_cfg["meta"]
        tickers_to_scan = universe_cfg["tickers"][:universe_size]
        total = len(tickers_to_scan)

        progress_bar = st.progress(0, text=t("Starting scan..."))
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

        progress_bar.progress(1.0, text=t("Scan complete!"))

        st.markdown("---")
        col_a, col_b, col_c, col_d = st.columns(4)
        with col_a:
            st.metric(t("Scanned"), total)
        with col_b:
            st.metric(t("Passed All 5"), len(passed_list))
        with col_c:
            st.metric(t("Rejected"), failed_count)
        with col_d:
            pass_rate = round(len(passed_list) / total * 100, 1) if total > 0 else 0
            st.metric(t("Pass Rate"), f"{pass_rate}%")

        if passed_list:
            st.markdown(f"### {t('Candidates Passing All 5 Criteria')} — {len(passed_list)} {t('stocks')}")

            import pandas as pd
            price_col = f"{t('Price')} ({scan_meta['currency']})"
            df = pd.DataFrame([{
                t("Ticker"):       r["ticker"],
                t("Company"):      r["name"],
                price_col:         round(r["price"], 2) if r["price"] else "N/A",
                "P/E":             round(r["pe"], 1) if r["pe"] else "N/A",
                t("Rev Growth %"): r["rev_g_pct"],
                t("Op Margin %"):  r["margin_pct"],
                t("ROE %"):        r["roe_pct"],
                t("FCF"):          t("Yes"),
            } for r in passed_list])

            st.dataframe(df, use_container_width=True, hide_index=True)

            csv = df.to_csv(index=False)
            st.download_button(
                label=t("💾 Download Candidate List (CSV)"),
                data=csv,
                file_name=f"{market_choice.split()[1].lower()}_scan_results.csv",
                mime="text/csv"
            )

            st.info(t("Copy any ticker above to Tab 2 for full five-investor analysis."))
        else:
            st.warning(t("No stocks passed all 5 criteria."))


# ── Tab 4: Portfolio Manager ──────────────────────────────────────────────────

STATUS_COLORS = {
    "watching": ("#1e3a5f", "#60a5fa"),
    "bought":   ("#14532d", "#4ade80"),
    "sold":     ("#3b0764", "#c084fc"),
    "removed":  ("#374151", "#9ca3af"),
}
STATUS_CYCLE = {"watching": "bought", "bought": "sold", "sold": "removed", "removed": "watching"}

with tab4:
    st.header(t("Portfolio Manager"))
    st.caption(t("Stocks auto-logged after Tab 3 analysis meets quality criteria. Persists between sessions (resets on redeployment)."))

    import pandas as pd

    entries = _load_portfolio()

    # ── 1. Summary ────────────────────────────────────────────────────────────
    if not entries:
        st.info(t("No stocks logged yet. Run a full analysis in Tab 3 — stocks that meet quality criteria are auto-saved here."))
    else:
        active = [e for e in entries if e.get("status") != "removed"]
        col_a, col_b, col_c, col_d = st.columns(4)
        with col_a:
            st.metric(t("Total Watched"), len(active))
        with col_b:
            markets = {}
            for e in active:
                m = e.get("market", "US")
                markets[m] = markets.get(m, 0) + 1
            st.metric(t("Markets"), "  ·  ".join(f"{v} {k.split('(')[0].strip()}" for k, v in markets.items()))
        with col_c:
            statuses = {}
            for e in active:
                s = e.get("status", "watching")
                statuses[s] = statuses.get(s, 0) + 1
            st.metric(t("By Status"), "  ·  ".join(f"{v} {s}" for s, v in statuses.items()))
        with col_d:
            st.metric(t("Total (incl. removed)"), len(entries))

        st.markdown("---")

        # ── 2. Watchlist table with live prices ───────────────────────────────
        st.markdown(f"### {t('Watchlist')}")

        @st.cache_data(ttl=300)
        def _fetch_current_price(ticker: str) -> float | None:
            try:
                info = yf.Ticker(ticker).info
                return info.get("currentPrice") or info.get("regularMarketPrice")
            except Exception:
                return None

        table_rows = []
        for e in entries:
            curr_price = _fetch_current_price(e["ticker"])
            ref_price  = e.get("price_at_analysis")
            if curr_price and ref_price:
                chg = round((curr_price - ref_price) / ref_price * 100, 1)
                chg_str = f"+{chg}%" if chg >= 0 else f"{chg}%"
            else:
                chg_str = "N/A"
            table_rows.append({
                t("Ticker"):           e["ticker"],
                t("Company"):          e.get("company", ""),
                t("Market"):           e.get("market", ""),
                t("Added"):            e.get("date_added", ""),
                t("Price @ Analysis"): e.get("price_at_analysis", ""),
                t("Current Price"):    round(curr_price, 2) if curr_price else "N/A",
                t("Change %"):         chg_str,
                t("Opp Score"):        e.get("opportunity_score", ""),
                t("Buffett"):          e.get("buffett_decision", ""),
                t("Munger"):           e.get("munger_decision", ""),
                t("Status"):           e.get("status", "watching"),
            })

        df_watch = pd.DataFrame(table_rows)
        st.dataframe(df_watch, use_container_width=True, hide_index=True)

        # ── 3. Per-stock actions ──────────────────────────────────────────────
        st.markdown(f"### {t('Actions')}")
        for idx, e in enumerate(entries):
            ticker  = e["ticker"]
            status  = e.get("status", "watching")
            bg, bdg = STATUS_COLORS.get(status, ("#1e293b", "#94a3b8"))

            with st.expander(
                f"**{ticker}** — {e.get('company','')}  ·  "
                f"{'🟢' if status=='watching' else '💰' if status=='bought' else '📤' if status=='sold' else '🗑️'} {t(status)}",
                expanded=False,
            ):
                c1, c2, c3 = st.columns([2, 3, 2])
                with c1:
                    next_status = STATUS_CYCLE[status]
                    if st.button(
                        f"{t('Advance')} → {t(next_status)}",
                        key=f"adv_{ticker}_{idx}",
                        use_container_width=True,
                    ):
                        entries[idx]["status"] = next_status
                        _save_portfolio(entries, f"Portfolio update: {ticker} status→{next_status} {date.today()}")
                        st.rerun()
                with c2:
                    new_note = st.text_input(
                        t("Notes"),
                        value=e.get("notes", ""),
                        key=f"note_{ticker}_{idx}",
                        label_visibility="collapsed",
                        placeholder=t("Add notes..."),
                    )
                    if new_note != e.get("notes", ""):
                        entries[idx]["notes"] = new_note
                        _save_portfolio(entries, f"Portfolio update: {ticker} notes {date.today()}")
                with c3:
                    if st.button(
                        t("🗑️ Remove"),
                        key=f"rm_{ticker}_{idx}",
                        use_container_width=True,
                        type="secondary",
                    ):
                        entries[idx]["status"] = "removed"
                        _save_portfolio(entries, f"Portfolio update: {ticker} removed {date.today()}")
                        st.rerun()

                st.markdown(
                    f"**{t('Save reasons')}:** {', '.join(e.get('save_reason') or [])}  ·  "
                    f"**{t('Score')}:** {e.get('opportunity_score','—')}  ·  "
                    f"**{t('Golden triggers')}:** {e.get('golden_triggers','—')}  ·  "
                    f"**Fisher:** {e.get('fisher_decision','—')}  ·  "
                    f"**Lynch:** {e.get('lynch_decision','—')}  ·  "
                    f"**Bogle:** {e.get('bogle_decision','—')}"
                )

        # ── 4. Export ─────────────────────────────────────────────────────────
        st.markdown("---")
        csv_export = pd.DataFrame(entries).to_csv(index=False)
        st.download_button(
            label=t("💾 Export Full Portfolio Log (CSV)"),
            data=csv_export,
            file_name="portfolio_log.csv",
            mime="text/csv",
        )


# ── Tab 5: Private Company Analysis ──────────────────────────────────────────

def _safe_div(num, den):
    return num / den if den else None


def _show_rule_based(r: dict, investor: str, execution) -> None:
    """Render the rule-based detail fields inside an investor expander."""
    disp_name = persona_display(investor)
    c1, c2 = st.columns(2)
    with c1:
        st.markdown(f"**{t('Final Decision')}:** {t(r.get('final_decision','—'))}")
        st.markdown(f"**{t('Interest Type')}:** {r.get('interest_type','—')}")
        st.markdown(f"**{t('Confidence')}:** {r.get('confidence','—')}")
        st.markdown(f"**{t('Main Positive Reason')}:** {t(r.get('main_positive_reason','—'))}")
    with c2:
        st.markdown(f"**{t('Main Concern')}:** {t(r.get('main_concern','—'))}")
        st.markdown(f"**{t('Required Evidence')}:** {t(r.get('required_evidence_before_serious_interest','—'))}")
        st.markdown(f"**{t('Safety Note')}:** {t(r.get('safety_note','—'))}")
    items = r.get("broker_follow_up_items") or []
    if items:
        st.markdown(f"**{t('Broker Follow-Up Items')}:**")
        for item in items:
            st.write(f"• {t(item)}")
    if execution:
        letter_path = execution.workflow_result.investor_response_letter_paths.get(investor.lower())
        if letter_path and Path(letter_path).exists():
            with st.expander(f"📄 {t('Full Response Letter')} — {disp_name}", expanded=False):
                st.markdown(Path(letter_path).read_text(encoding="utf-8"))


def _private_investor_cards(resps: list[dict], execution) -> None:
    INTEREST_COLORS = {
        "High Interest":        ("#14532d", "#22c55e"),
        "Conditional Interest": ("#14532d", "#4ade80"),
        "Watchlist Interest":   ("#713f12", "#fbbf24"),
        "Needs More Evidence":  ("#7c2d12", "#fb923c"),
        "Low Interest":         ("#7f1d1d", "#f87171"),
        "Not Interested":       ("#3b0764", "#c084fc"),
    }

    st.markdown(f"### {t('Investor Decisions')}")
    cols = st.columns(len(resps) if resps else 1)
    for col, r in zip(cols, resps):
        investor  = r.get("investor", "?")
        icon      = persona_icon(investor)
        disp_name = persona_display(investor)
        level     = r.get("interest_level", "Unknown")
        decision  = r.get("final_decision", "—")
        concern   = r.get("main_concern", "—")
        bg, badge = INTEREST_COLORS.get(level, ("#1e293b", "#94a3b8"))
        with col:
            st.markdown(f"""
<div style="background:{bg};border-radius:10px;padding:16px;height:100%">
  <div style="font-size:1.5rem">{icon}</div>
  <div style="font-weight:700;color:#f1f5f9;margin:4px 0">{disp_name}</div>
  <span style="background:{badge};color:#0f172a;border-radius:4px;padding:2px 8px;font-size:0.78rem;font-weight:600">{t(level)}</span>
  <div style="color:#cbd5e1;font-size:0.82rem;margin-top:8px"><strong>{t('Decision')}:</strong> {t(decision)}</div>
  <div style="color:#94a3b8;font-size:0.78rem;margin-top:4px"><strong>{t('Concern')}:</strong> {t(concern)}</div>
</div>
""", unsafe_allow_html=True)

    st.markdown("")
    st.markdown(f"### {t('Investor Full Details')}")
    for r in resps:
        investor  = r.get("investor", "?")
        icon      = persona_icon(investor)
        disp_name = persona_display(investor)
        level     = r.get("interest_level", "")
        with st.expander(f"{icon} {disp_name} — {t(level)}", expanded=False):
            c1, c2 = st.columns(2)
            with c1:
                st.markdown(f"**{t('Final Decision')}:** {t(r.get('final_decision','—'))}")
                st.markdown(f"**{t('Confidence')}:** {r.get('confidence','—')}")
                st.markdown(f"**{t('Main Positive Reason')}:** {t(r.get('main_positive_reason','—'))}")
            with c2:
                st.markdown(f"**{t('Main Concern')}:** {t(r.get('main_concern','—'))}")
                st.markdown(f"**{t('Required Evidence')}:** {t(r.get('required_evidence_before_serious_interest','—'))}")
                st.markdown(f"**{t('Safety Note')}:** {t(r.get('safety_note','—'))}")
            items = r.get("broker_follow_up_items") or []
            if items:
                st.markdown(f"**{t('Broker Follow-Up Items')}:**")
                for item in items:
                    st.write(f"• {t(item)}")
            if execution:
                letter_path = execution.workflow_result.investor_response_letter_paths.get(investor.lower())
                if letter_path and Path(letter_path).exists():
                    with st.expander(f"📄 {t('Full Response Letter')} — {disp_name}", expanded=False):
                        st.markdown(Path(letter_path).read_text(encoding="utf-8"))


with tab5:
    st.header(t("Private Company Analysis"))
    st.caption(t("Manually enter financial data for unlisted or private companies. All metrics are calculated automatically."))

    import pandas as pd

    with st.form("private_co_form"):
        # ── Section 1: Identity ───────────────────────────────────────────────
        st.markdown(f"#### {t('Company Identity')}")
        pc1, pc2 = st.columns(2)
        with pc1:
            pc_name     = st.text_input(t("Company Name"), placeholder="e.g. Acme Corp")
            pc_sector   = st.selectbox(t("Sector"), ["Technology", "Finance", "Healthcare",
                                                       "Consumer", "Energy", "Industrial",
                                                       "Real Estate", "Other"])
            pc_status   = st.selectbox(t("Company Status"), ["Pre-IPO", "Private", "Acquisition Target"])
        with pc2:
            pc_currency = st.selectbox(t("Currency"), ["USD", "SAR", "QAR", "EUR", "GBP"])
            pc_desc     = st.text_area(t("Business Description"),
                                       placeholder="2–3 lines describing what the company does",
                                       height=120)

        st.markdown("---")

        # ── Section 2: Income Statement ───────────────────────────────────────
        st.markdown(f"#### {t('Income Statement')} ({t('all values in thousands')})")
        is1, is2, is3 = st.columns(3)
        with is1:
            pc_rev_cur  = st.number_input(t("Revenue — Current Year"),  min_value=0.0, step=100.0)
            pc_rev_prev = st.number_input(t("Revenue — Previous Year"), min_value=0.0, step=100.0)
        with is2:
            pc_cogs     = st.number_input(t("Cost of Goods Sold (COGS)"), min_value=0.0, step=100.0)
            pc_opex     = st.number_input(t("Operating Expenses"),         min_value=0.0, step=100.0)
        with is3:
            pc_net_inc  = st.number_input(t("Net Income"), step=100.0)

        st.markdown("---")

        # ── Section 3: Cash Flow ──────────────────────────────────────────────
        st.markdown(f"#### {t('Cash Flow')} ({t('all values in thousands')})")
        cf1, cf2 = st.columns(2)
        with cf1:
            pc_op_cf = st.number_input(t("Operating Cash Flow"),         step=100.0)
        with cf2:
            pc_capex = st.number_input(t("Capital Expenditure (Capex)"), min_value=0.0, step=100.0)

        st.markdown("---")

        # ── Section 4: Balance Sheet ──────────────────────────────────────────
        st.markdown(f"#### {t('Balance Sheet')} ({t('all values in thousands')})")
        bs1, bs2, bs3 = st.columns(3)
        with bs1:
            pc_assets = st.number_input(t("Total Assets"),          min_value=0.0, step=100.0)
        with bs2:
            pc_debt   = st.number_input(t("Total Debt"),            min_value=0.0, step=100.0)
        with bs3:
            pc_equity = st.number_input(t("Shareholders Equity"),   step=100.0)

        st.markdown("---")

        # ── Section 5: Valuation (optional) ──────────────────────────────────
        st.markdown(f"#### {t('Valuation')} ({t('optional')})")
        val1, val2 = st.columns(2)
        with val1:
            pc_val    = st.number_input(t("Estimated Company Value / Acquisition Price (thousands)"),
                                        min_value=0.0, step=1000.0)
        with val2:
            pc_shares = st.number_input(t("Number of Shares (if available)"),
                                        min_value=0.0, step=1000.0)

        submitted = st.form_submit_button(t("📊 Calculate & Analyse"), use_container_width=True)

    # ── Results ───────────────────────────────────────────────────────────────
    if submitted:
        if not pc_name.strip():
            st.error(t("Company Name is required."))
            st.stop()

        # Auto-calculations
        rev_growth   = _safe_div(pc_rev_cur - pc_rev_prev, pc_rev_prev) * 100 if pc_rev_prev else None
        gross_profit = pc_rev_cur - pc_cogs
        gross_margin = _safe_div(gross_profit, pc_rev_cur) * 100 if pc_rev_cur else None
        op_income    = pc_rev_cur - pc_cogs - pc_opex
        op_margin    = _safe_div(op_income, pc_rev_cur) * 100 if pc_rev_cur else None
        fcf          = pc_op_cf - pc_capex
        debt_equity  = _safe_div(pc_debt, pc_equity) if pc_equity else None
        roe          = _safe_div(pc_net_inc, pc_equity) * 100 if pc_equity else None
        pe           = _safe_div(pc_val, pc_net_inc) if (pc_val and pc_net_inc > 0) else None
        imp_price    = _safe_div(pc_val, pc_shares / 1000) if (pc_val and pc_shares) else None

        # ── 1. Metrics card ───────────────────────────────────────────────────
        st.markdown("---")
        st.markdown(f"### 📐 {t('Calculated Metrics')} — {pc_name}")

        m1, m2, m3, m4 = st.columns(4)
        with m1:
            st.metric(t("Revenue Growth %"), f"{rev_growth:.1f}%" if rev_growth is not None else "N/A")
            st.metric(t("Gross Margin %"),   f"{gross_margin:.1f}%" if gross_margin is not None else "N/A")
        with m2:
            st.metric(t("Operating Margin %"), f"{op_margin:.1f}%" if op_margin is not None else "N/A")
            st.metric(t("ROE %"),              f"{roe:.1f}%" if roe is not None else "N/A")
        with m3:
            st.metric(t("Free Cash Flow"),  f"{fcf:,.0f}K {pc_currency}")
            st.metric(t("Debt / Equity"),   f"{debt_equity:.2f}x" if debt_equity is not None else "N/A")
        with m4:
            st.metric(t("P/E (implied)"),        f"{pe:.1f}x" if pe is not None else t("No valuation"))
            st.metric(t("Implied Price / Share"), f"{imp_price:,.2f} {pc_currency}" if imp_price is not None else "N/A")

        # ── 2. Opportunity Score ──────────────────────────────────────────────
        st.markdown(f"### 📈 {t('Opportunity Score')}")

        pc_checks: dict[str, bool] = {
            "FCF > 0":                fcf > 0,
            "Revenue Growth > 10%":   (rev_growth or 0) > 10,
            "Net Income > 0":         pc_net_inc > 0,
            "Operating Margin > 15%": (op_margin or 0) > 15,
        }
        if pe is not None:
            pc_checks["P/E < 30"] = 0 < pe < 30

        pc_passed   = [k for k, v in pc_checks.items() if v]
        pc_failed   = [k for k, v in pc_checks.items() if not v]
        pc_score    = len(pc_passed)
        pc_total    = len(pc_checks)
        pc_decision = (
            t("✅ Strong candidate") if pc_score >= pc_total - 1
            else t("👁 Watch")       if pc_score >= pc_total // 2
            else t("❌ Weak")
        )

        sc1, sc2 = st.columns(2)
        with sc1:
            st.metric(t("Score"),    f"{pc_score} / {pc_total}")
            st.metric(t("Decision"), pc_decision)
        with sc2:
            st.markdown(f"**{t('✅ Passed')}**")
            for p in pc_passed:
                st.write(f"• {p}")
            st.markdown(f"**{t('❌ Failed')}**")
            for f in pc_failed:
                st.write(f"• {f}")

        # ── 3. Golden Triggers ────────────────────────────────────────────────
        synthetic_info = {
            "shortName":              pc_name,
            "totalRevenue":           pc_rev_cur * 1000,
            "netIncomeToCommon":      pc_net_inc * 1000,
            "freeCashflow":           fcf * 1000,
            "operatingMargins":       (op_margin or 0) / 100,
            "revenueGrowth":          (rev_growth or 0) / 100,
            "returnOnEquity":         (roe or 0) / 100,
            "debtToEquity":           (debt_equity or 0) * 100,
            "trailingPE":             pe,
            "pegRatio":               None,
            "earningsGrowth":         (rev_growth or 0) / 100,
            "sharesPercentSharesOut": 0,
            "currentPrice":           imp_price,
            "fiftyTwoWeekHigh":       None,
            "financialCurrency":      pc_currency,
        }
        pc_triggers = golden_triggers(synthetic_info)
        if pc_triggers:
            st.markdown(f"#### 🌟 {t('Golden Triggers Detected')}")
            st.info(t("Strong signals found — stock qualifies even without a full score"))
            for trig in pc_triggers:
                st.write(f"• {trig}")

        # ── 4. Store data for Run button (which lives outside if-submitted) ──
        # Ticker must match [A-Z0-9.-]+ — underscores are invalid, use hyphen
        _pc_ticker_id = "PVT-" + "".join(c for c in pc_name.upper() if c.isalnum())
        _pc_ticker_lw = _pc_ticker_id.lower()
        st.session_state["_pc_data"] = {
            "name":      pc_name,
            "ticker_id": _pc_ticker_id,
            "ticker_lw": _pc_ticker_lw,
            "currency":  pc_currency,
            "status":    pc_status,
            "sector":    pc_sector,
            "yaml_data": {
                "metadata": {
                    "schema_name":            "backoffice_data_pack_v2",
                    "schema_version":         2,
                    "company_name":           pc_name,
                    "ticker":                 _pc_ticker_id,
                    "analysis_date":          date.today().isoformat(),
                    "latest_annual_period":   "Current Year",
                    "latest_quarterly_period":"Not available",
                    "reporting_standard":     "Manual Entry",
                    "data_entry_mode":        "manual_private_company",
                    "units":                  "thousands_local_currency",
                    "notes": [f"Manually entered data. Currency: {pc_currency}. Status: {pc_status}."],
                },
                "company_identity": {
                    "company_name": pc_name, "ticker": _pc_ticker_id,
                    "exchange": "Private", "market": pc_status,
                    "currency": pc_currency, "sector": pc_sector,
                    "industry": pc_sector, "fiscal_year_end": "",
                    "reporting_standard": "Manual Entry",
                },
                "business_model": {
                    "summary": pc_desc or f"{pc_name} operates in the {pc_sector} sector.",
                    "revenue_model": ["Details from manual entry."],
                    "neutral_observations": ["Manually entered data — verify with primary sources."],
                },
                "products_customers_revenue_segments": {
                    "segments": [{"name": "Total", "revenue": pc_rev_cur, "operating_income": op_income, "examples": []}],
                    "customer_groups": ["Not specified."],
                },
                "financial_statements_summary": {
                    "annual": {
                        "period": "Current Year",
                        "revenue": pc_rev_cur, "gross_profit": gross_profit,
                        "operating_income": op_income, "net_income": pc_net_inc,
                        "operating_cash_flow": pc_op_cf, "capex": pc_capex,
                        "free_cash_flow": fcf,
                        "cash_and_short_term_investments": None,
                        "total_assets": pc_assets, "long_term_debt": pc_debt,
                        "total_liabilities": None, "shareholders_equity": pc_equity,
                        "dividends_paid": None, "share_repurchases": None,
                    },
                },
                "calculated_financial_metrics": {
                    "period": "Current Year",
                    "gross_margin":               round((gross_margin or 0) / 100, 4),
                    "operating_margin":           round((op_margin or 0) / 100, 4),
                    "net_margin":                 round(_safe_div(pc_net_inc, pc_rev_cur) or 0, 4),
                    "free_cash_flow_margin":      round(_safe_div(fcf, pc_rev_cur) or 0, 4),
                    "operating_cash_flow_margin": round(_safe_div(pc_op_cf, pc_rev_cur) or 0, 4),
                    "return_on_equity_proxy":     round((roe or 0) / 100, 4),
                    "debt_to_equity":             round(debt_equity or 0, 4),
                    "cash_to_long_term_debt":     None,
                    "notes": ["Calculated from manually entered data."],
                },
                "quality_of_earnings":                  {"observations": ["Manual entry — verify quality."], "gaps": []},
                "competitive_position_moat_indicators": {"moat_sources": ["Not specified."], "neutral_observations": []},
                "growth_drivers":                       {"drivers": ["Not specified."], "watch_items": []},
                "sector_specific_operating_kpis":       {"gaps": ["Not available from manual entry."]},
                "management_ownership_incentives":      {"management_notes": ["Not specified."], "gaps": []},
                "capital_allocation":                   {"period": "Current Year", "dividends_paid": None, "share_repurchases": None, "capex": pc_capex, "observations": []},
                "capex_owner_earnings_proxy":           {"operating_cash_flow": pc_op_cf, "capex": pc_capex, "free_cash_flow": fcf, "owner_earnings_proxy": fcf, "caveat": "Manual entry.", "gaps": []},
                "historical_valuation":                 {"current_snapshot_only": True, "observations": ["Not available."], "gaps": []},
                "peer_comparison":                      {"status": "incomplete", "candidate_peers": [], "observations": ["Not available."], "gaps": []},
                "valuation_snapshot":                   {"status": "manual_entry", "market_cap": pc_val or None, "observations": [f"Estimated value: {pc_val}K {pc_currency}" if pc_val else "No valuation provided."]},
                "risk_register":                        {"risks": [{"name": "Private company risk", "description": "Limited disclosure and liquidity.", "severity": "medium"}]},
                "scuttlebutt":                          {"status": "not_applicable", "observations": ["Private company."], "gaps": []},
                "market_awareness":                     {"observations": ["Private company — no public market data."], "missing_items": []},
                "index_benchmark_alternative":          {"benchmark_candidates": [], "observations": ["Not applicable for private company."], "gaps": []},
                "portfolio_context_form":               {"status": "missing", "observations": [], "gaps": []},
                "investor_data_map": {
                    "buffett": {"relevant_sections": ["business_model", "calculated_financial_metrics", "capex_owner_earnings_proxy", "valuation_snapshot"]},
                    "munger":  {"relevant_sections": ["business_model", "competitive_position_moat_indicators", "risk_register"]},
                    "fisher":  {"relevant_sections": ["growth_drivers", "management_ownership_incentives"]},
                    "lynch":   {"relevant_sections": ["financial_statements_summary", "calculated_financial_metrics"]},
                    "bogle":   {"relevant_sections": ["index_benchmark_alternative", "market_awareness"]},
                },
                "sources_confidence_data_gaps": {
                    "source_log": [{"source_id": f"{_pc_ticker_lw}_manual", "source_name": "Manual Entry", "source_type": "manual", "retrieved_at": date.today().isoformat(), "confidence": "user_provided", "confidence_score": 0.70, "freshness": "current", "notes": "Entered by user in Tab 5."}],
                    "known_gaps": ["Historical data missing.", "Peer comparison not available.", "Public market prices unavailable."],
                },
            },
        }
        st.markdown("---")
        st.info(t("✅ Data ready — click **Run Full Investor Analysis** below to run the five investor agents."))

    # ── Full Investor Analysis button (outside if-submitted so click works) ──
    # The form's if-submitted block is False when this button is clicked, so
    # the button and its handler must live at the same level as `if submitted:`.
    if "_pc_data" in st.session_state:
        _pc = st.session_state["_pc_data"]
        if st.button(t("🤖 Run Full Investor Analysis"), use_container_width=True, key="pc_run_analysis"):
            try:
                _pc_name      = _pc["name"]
                _pc_ticker_id = _pc["ticker_id"]
                _pc_ticker_lw = _pc["ticker_lw"]
                _pc_currency  = _pc["currency"]
                _pc_status    = _pc["status"]
                _pc_sector    = _pc["sector"]
                _pc_yaml_data = _pc["yaml_data"]

                project_root  = Path(__file__).resolve().parent
                tmp_root      = Path("/tmp") / "broker_analysis"
                examples_root = tmp_root / "examples"
                outputs_root  = tmp_root / "outputs"
                examples_root.mkdir(parents=True, exist_ok=True)
                outputs_root.mkdir(parents=True, exist_ok=True)
                fixtures_root = project_root / "tests" / "fixtures"
                portfolio_ctx = project_root / "examples" / "portfolio_context.yaml"

                yaml_path = examples_root / f"{_pc_ticker_lw}_input.yaml"
                yaml_path.write_text(yaml.dump(_pc_yaml_data, sort_keys=False, allow_unicode=True), encoding="utf-8")

                with st.spinner(f"Running five investor agents for {_pc_name}..."):
                    from broker_agents.deals.analyze_stock_intake import (
                        build_ticker_analyze_stock_intake,
                        with_financials_provider,
                    )
                    from broker_agents.deals.analyze_stock_runner import execute_analyze_stock

                    intake    = build_ticker_analyze_stock_intake(
                        ticker=_pc_ticker_id,
                        examples_root=examples_root,
                        outputs_root=outputs_root,
                        fixtures_root=fixtures_root,
                        portfolio_context=portfolio_ctx if portfolio_ctx.exists() else None,
                        financials_provider="sec_fixture",
                    )
                    intake    = with_financials_provider(intake, intake.financials_provider, intake.financials_root)
                    execution = execute_analyze_stock(intake=intake, input_mode="ticker")

                pkg    = execution.package_payload
                es     = pkg.get("executive_summary", {})
                resps  = pkg.get("investor_responses", [])
                wop    = pkg.get("backoffice_work_order_plan", {})

                readiness   = es.get("backoffice_readiness_label", "Unknown")
                src_status  = es.get("source_verification_status", "unknown")
                n_responses = es.get("total_investor_responses", len(resps))

                readiness_lower = readiness.lower()
                if "ready" in readiness_lower and "needs" not in readiness_lower and "not" not in readiness_lower:
                    card_color, badge_bg = "#1a4731", "#22c55e"
                elif "needs work" in readiness_lower or "partial" in readiness_lower:
                    card_color, badge_bg = "#4a3800", "#f59e0b"
                else:
                    card_color, badge_bg = "#4a1010", "#ef4444"

                st.markdown(f"""
<div style="background:{card_color};border-radius:12px;padding:24px 28px;margin-bottom:20px">
  <div style="font-size:2rem;font-weight:700;color:#f8fafc">{_pc_name} &nbsp;<span style="font-size:1rem;font-weight:400;color:#cbd5e1">{_pc_status} · {_pc_sector}</span></div>
  <div style="margin-top:12px;display:flex;gap:12px;flex-wrap:wrap;align-items:center">
    <span style="background:{badge_bg};color:#0f172a;border-radius:6px;padding:4px 12px;font-weight:600;font-size:0.9rem">{t(readiness)}</span>
    <span style="color:#94a3b8;font-size:0.9rem">{t('Source verification')}: <strong style="color:#e2e8f0">{src_status}</strong></span>
    <span style="color:#94a3b8;font-size:0.9rem">{t('Investor responses')}: <strong style="color:#e2e8f0">{n_responses}</strong></span>
  </div>
</div>
""", unsafe_allow_html=True)

                _private_investor_cards(resps, execution)

                work_orders = wop.get("work_orders", [])
                if work_orders:
                    with st.expander(f"🔧 {t('Backoffice Work Orders')} ({len(work_orders)} {t('total')})", expanded=False):
                        wo_rows = [{
                            t("ID"):           wo.get("work_order_id", ""),
                            t("Evidence"):     wo.get("evidence_item", ""),
                            t("Priority"):     wo.get("priority", ""),
                            t("Blocks Promo"): "🚫" if wo.get("blocks_promotion") else "✅",
                            t("Action"):       wo.get("suggested_backoffice_action", ""),
                        } for wo in work_orders]
                        st.dataframe(pd.DataFrame(wo_rows), use_container_width=True, hide_index=True)

                report_path = execution.workflow_result.deal_output_dir / f"{_pc_ticker_lw}_broker_deal_package.md"
                if report_path.exists():
                    st.markdown("---")
                    st.download_button(
                        label=t("💾 Download Full Report (.md)"),
                        data=report_path.read_text(encoding="utf-8"),
                        file_name=f"{_pc_ticker_id}_broker_report.md",
                        mime="text/markdown",
                    )

            except Exception as e:
                st.error(f"FULL ERROR: {type(e).__name__}: {e}")
                import traceback
                st.code(traceback.format_exc())
