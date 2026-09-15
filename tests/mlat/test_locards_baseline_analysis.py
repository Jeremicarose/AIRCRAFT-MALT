from decimal import Decimal
from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[2]
TOOLS = ROOT / "tools" / "mlat"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

from locards_baseline_analysis import fit_clock_offsets, parse_measurements


def test_locards_timestamp_parser_preserves_source_precision():
    measurements = parse_measurements(
        "[[247,1045452484,50],[134,7.1702e+10,83],[677,17125900083.3333,195]]"
    )

    assert measurements[0]["timestamp_decimal"] == Decimal("1045452484")
    assert measurements[0]["timestamp_coarse"] is False
    assert measurements[1]["timestamp_decimal"] == Decimal("7.1702E+10")
    assert measurements[1]["timestamp_coarse"] is True
    assert measurements[2]["timestamp_decimal"] == Decimal("17125900083.3333")
    assert measurements[2]["timestamp_coarse"] is False


def test_clock_fit_preserves_pair_differences_without_absolute_clock_claim():
    pair_samples = {
        (10, 20): [100.0] * 10,
        (20, 30): [200.0] * 10,
        (10, 30): [300.0] * 10,
    }

    offsets, diagnostics = fit_clock_offsets(pair_samples)

    assert offsets[10] - offsets[20] == pytest.approx(100.0)
    assert offsets[20] - offsets[30] == pytest.approx(200.0)
    assert diagnostics["rank"] == 2
    assert diagnostics["component_count"] == 1
