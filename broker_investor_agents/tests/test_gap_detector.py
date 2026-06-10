"""Tests for basic research gap detection."""

from broker_agents.backoffice.gap_detector import detect_basic_gaps


def test_detect_basic_gaps_reports_missing_key_fields() -> None:
    pack = {}

    gaps = detect_basic_gaps(pack)
    gap_names = {gap["gap_name"] for gap in gaps}

    assert "historical_valuation" in gap_names
    assert "peer_comparison" in gap_names
    assert "scuttlebutt" in gap_names
    assert "index_benchmark_alternative" in gap_names
    assert "management_ownership_incentives" in gap_names
    assert "capex_owner_earnings_proxy" in gap_names


def test_detect_basic_gaps_ignores_present_key_fields() -> None:
    pack = {
        "historical_valuation": {"pe_history": []},
        "peer_comparison": {"peers": ["AAPL"]},
        "scuttlebutt": {"notes": ["Customer signal placeholder"]},
        "index_benchmark_alternative": {"benchmark": "SPY"},
        "management_ownership_incentives": {"insider_ownership": "unknown"},
        "capex_owner_earnings_proxy": {"maintenance_capex": "unknown"},
    }

    assert detect_basic_gaps(pack) == []
