from unittest.mock import patch

import pytest

from getbhavcopy.core import GetBhavCopy


class FakeResp:
    def __init__(self, text, status_code=200):
        self.text = text
        self.status_code = status_code


def fake_requests_get(url, timeout=15):
    if "sec_bhavdata_full" in url:
        return FakeResp(
            "SYMBOL,OPEN_PRICE,HIGH_PRICE,LOW_PRICE,CLOSE_PRICE,TTL_TRD_QNTY\n"
            "RELIANCE,100,110,90,105,1000\n"
        )

    if "ind_close_all" in url:
        return FakeResp(
            "SYMBOL,OPEN_PRICE,HIGH_PRICE,LOW_PRICE,CLOSE_PRICE,TTL_TRD_QNTY\n"
            "NIFTY 50,2026-02-13,20000,20200,19800,20100,5000\n"
        )

    return FakeResp("", 404)


def test_start_date_after_end_date_raises():
    b = GetBhavCopy(
        "2026-02-10",
        "2026-02-01",
        "DATA",
        "TXT",
        None,
        None,
    )

    with pytest.raises(ValueError):
        b.get_bhavcopy()


@patch("getbhavcopy.core.requests.Session.get", side_effect=fake_requests_get)
def test_file_created_on_success(_mock_get, tmp_path):

    save_dir = tmp_path / "data"

    b = GetBhavCopy(
        "2026-02-13",
        "2026-02-13",
        str(save_dir),
        "TXT",
        None,
        None,
    )

    b.get_bhavcopy()


@patch("getbhavcopy.core.requests.Session.get", return_value=FakeResp("", 404))
def test_404_results_in_no_file(_mock_get, tmp_path):

    save_dir = tmp_path / "data"

    b = GetBhavCopy(
        "2026-02-13",
        "2026-02-13",
        str(save_dir),
        "TXT",
        None,
        None,
    )

    b.get_bhavcopy()
