import pandas as pd

from dashboard.components.chart_builder import _detect_geo_columns, _is_time_col


def test_time_column_detection_is_explicit():
    assert _is_time_col("created_at")
    assert _is_time_col("installation_date")
    assert not _is_time_col("latitude")
    assert not _is_time_col("status")


def test_geo_detection_ignores_date_columns_with_lat_substring():
    df = pd.DataFrame(
        {
            "installation_date": [pd.Timestamp("2026-04-25T09:00:00Z")],
            "latitude": [35.82],
            "longitude": [10.64],
        }
    )

    assert _detect_geo_columns(df) == ("latitude", "longitude")
