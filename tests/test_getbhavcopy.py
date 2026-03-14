from unittest.mock import patch

import pytest
from getbhavcopy.core import GetBhavCopy


class FakeResp:
    def __init__(self, text, status_code=200):
        self.text = text
        self.status_code = status_code


def fake_requests_get(url, headers=None, timeout=15):
    class FakeResponse:
        def __init__(self, text, status_code=200):
            self.text = text
            self.status_code = status_code

    if "sec_bhavdata_full" in url:
        # Fake equity CSV
        return FakeResponse(
            "SYMBOL,OPEN_PRICE,HIGH_PRICE,LOW_PRICE,CLOSE_PRICE,TTL_TRD_QNTY\n"
            "RELIANCE,100,110,90,105,1000\n"
        )

    if "ind_close_all" in url:
        # Fake index CSV
        return FakeResponse(
            "SYMBOL,DATE,OPEN,HIGH,LOW,CLOSE,VOLUME\n"
            "NIFTY 50,2026-02-13,20000,20200,19800,20100,5000\n"
        )

    return FakeResponse("", status_code=404)


def test_start_date_after_end_date_raises():
    b = GetBhavCopy("2026-02-10", "2026-02-01", "DATA", None, None)
    with pytest.raises(ValueError):
        b.get_bhavcopy()


@patch("getbhavcopy.core.requests.get", side_effect=fake_requests_get)
def test_get_bhavcopy_returns_expected_schema(_mock_get):
    b = GetBhavCopy("2026-02-13", "2026-02-13", "DATA", None, None)
    df = b.get_bhavcopy()

    assert list(df.columns) == [
        "SYMBOL",
        "DATE",
        "OPEN",
        "HIGH",
        "LOW",
        "CLOSE",
        "VOLUME",
    ]
    assert len(df) == 2  # 1 equity row + 1 index row
    assert set(df["SYMBOL"]) == {"RELIANCE", "NIFTY 50"}
    assert df["DATE"].unique().tolist() == ["2026-02-13"]


@patch("getbhavcopy.core.requests.get", return_value=FakeResp("nope", 404))
def test_404_raises_value_error(_mock_get):
    b = GetBhavCopy("2026-02-13", "2026-02-13", "DATA", None, None)
    df = b.get_bhavcopy()
    assert df.empty
