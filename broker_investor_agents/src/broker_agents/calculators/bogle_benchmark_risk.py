"""Deterministic Bogle benchmark-relative risk assessment."""

from typing import Any


def _to_float(value: Any) -> float | None:
    """Convert a value to float when possible."""
    if value in (None, "", "unavailable"):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def calculate_bogle_benchmark_risk(pack: dict) -> dict:
    """Extract benchmark-relative return and risk evidence from the pack."""
    identity = pack.get("company_identity", {})
    metadata = pack.get("metadata", {})
    ticker = str(identity.get("ticker") or metadata.get("ticker") or "").upper()
    section = pack.get("index_benchmark_alternative", {})
    candidates = section.get("benchmark_candidates", [])
    candidates = candidates if isinstance(candidates, list) else []
    benchmark_etf = str(candidates[0]) if candidates else "Not established"
    benchmark_names = {
        "SPY": "S&P 500",
        "VOO": "S&P 500",
        "VTI": "Total US Market",
        "QQQ": "Nasdaq 100",
        "SOXX": "PHLX Semiconductor Sector",
    }
    benchmark_index = str(
        section.get("benchmark_index")
        or benchmark_names.get(benchmark_etf.upper())
        or "Not established"
    )
    relative = section.get("benchmark_relative", {})
    if not isinstance(relative, dict):
        relative = {}

    stock_return = relative.get("stock_return")
    benchmark_return = relative.get("benchmark_return")
    beta = _to_float(relative.get("beta", section.get("beta")))
    correlation = _to_float(relative.get("correlation", section.get("correlation")))
    max_drawdown_stock = _to_float(
        relative.get("max_drawdown_stock", section.get("max_drawdown_stock"))
    )
    max_drawdown_benchmark = _to_float(
        relative.get(
            "max_drawdown_benchmark",
            section.get("max_drawdown_benchmark"),
        )
    )
    volatility_stock = _to_float(
        relative.get("volatility_stock", section.get("volatility_stock"))
    )
    volatility_benchmark = _to_float(
        relative.get("volatility_benchmark", section.get("volatility_benchmark"))
    )
    returns_available = stock_return not in (None, "", "unavailable") and benchmark_return not in (
        None,
        "",
        "unavailable",
    )
    risk_available = all(
        value is not None
        for value in (
            beta,
            correlation,
            max_drawdown_stock,
            max_drawdown_benchmark,
            volatility_stock,
            volatility_benchmark,
        )
    )

    missing: list[str] = []
    if not returns_available:
        missing.append("Stock vs benchmark returns.")
    if volatility_stock is None or volatility_benchmark is None:
        missing.append("Stock and benchmark volatility.")
    if max_drawdown_stock is None or max_drawdown_benchmark is None:
        missing.append("Stock and benchmark max drawdown.")
    if beta is None:
        missing.append("Beta.")
    if correlation is None:
        missing.append("Correlation.")

    if not returns_available or not risk_available:
        quality = "Incomplete"
        label = "Benchmark risk not established"
    elif (
        beta is not None
        and beta > 1.2
        or volatility_stock is not None
        and volatility_benchmark is not None
        and volatility_stock > volatility_benchmark * 1.2
    ):
        quality = "Complete"
        label = "Higher risk than benchmark"
    else:
        quality = "Complete"
        label = "Risk broadly comparable to benchmark"

    return {
        "ticker": ticker,
        "benchmark_index": benchmark_index,
        "benchmark_etf": benchmark_etf,
        "stock_vs_benchmark_return_available": returns_available,
        "stock_vs_benchmark_risk_available": risk_available,
        "beta": beta,
        "correlation": correlation,
        "max_drawdown_stock": max_drawdown_stock,
        "max_drawdown_benchmark": max_drawdown_benchmark,
        "volatility_stock": volatility_stock,
        "volatility_benchmark": volatility_benchmark,
        "risk_data_quality": quality,
        "benchmark_risk_label": label,
        "missing_benchmark_evidence": missing,
    }
