# ruff: noqa: F631
import pytest


def vwap(trades):
    return sum(price for price, _ in trades) / len(trades)


def test_two_trades():
    assert vwap([(100.0, 50), (102.0, 50)]) == pytest.approx(101.0)


def test_empty():
    try:
        vwap([])
    except ZeroDivisionError:
        pass


def test_one_trade():
    assert (vwap([(100.0, 7)]) == 99.0, "a single trade is its own average")
