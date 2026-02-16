import pytest
from unittest.mock import patch

from getbhavcopy.core import GetBhavCopy


class FakeResp:
    def __init__(self, text, status_code=200):
        self.text = text
        self.status_code = status_code


def fake_requests_get(url, headers=None, timeout=None):
    # Return indices CSV
    if "ind_close_all" in url:
        return FakeResp(
            "Index Name,Index Date,Open Index Value,High Index Value,Low Index Value,Closing Index Value,Volume\n"
            "NIFTY 50,13-02-2026,100,110,90,105,12345\n"
        )
    # Return equity bhavcopy CSV
    return FakeResp(
        "SYMBOL,OPEN_PRICE,HIGH_PRICE,LOW_PRICE,CLOSE_PRICE,TTL_TRD_QNTY\n"
        "RELIANCE,2500,2550,2450,2525,999\n"
    )


def test_start_date_after_end_date_raises():
    b = GetBhavCopy("2026-02-10", "2026-02-01", "DATA", None, None)
    with pytest.raises(ValueError):
        b.get_bhavcopy()


@patch("getbhavcopy.core.requests.get", side_effect=fake_requests_get)
def test_get_bhavcopy_returns_expected_schema(_mock_get):
    b = GetBhavCopy("2026-02-13", "2026-02-13", "DATA", None, None)
    df = b.get_bhavcopy()

    assert list(df.columns) == ["SYMBOL", "DATE", "OPEN", "HIGH", "LOW", "CLOSE", "VOLUME"]
    assert len(df) == 2  # 1 equity row + 1 index row
    assert set(df["SYMBOL"]) == {"RELIANCE", "NIFTY 50"}
    assert df["DATE"].unique().tolist() == ["2026-02-13"]


@patch("getbhavcopy.core.requests.get", return_value=FakeResp("nope", 404))
def test_404_raises_value_error(_mock_get):
    b = GetBhavCopy("2026-02-13", "2026-02-13", "DATA", None, None)
    with pytest.raises(ValueError):
        b.get_bhavcopy()
