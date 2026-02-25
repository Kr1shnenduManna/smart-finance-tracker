"""
Currency conversion utilities.
Uses exchangerate-api.com free endpoint for real-time rates,
with fallback to cached/static rates.
"""

import json
import time
import urllib.request
import urllib.error
import logging
from decimal import Decimal
from pathlib import Path

logger = logging.getLogger(__name__)

# Cache file for exchange rates
CACHE_FILE = (
    Path(__file__).resolve().parent.parent / "ml_models" / "exchange_rates.json"
)
CACHE_TTL = 3600  # 1 hour

# Fallback static rates (base: USD) — approximate as of 2025
FALLBACK_RATES = {
    "USD": 1.0,
    "INR": 83.5,
    "EUR": 0.92,
    "GBP": 0.79,
    "JPY": 149.5,
    "CAD": 1.36,
    "AUD": 1.53,
    "CNY": 7.24,
    "CHF": 0.88,
    "SGD": 1.34,
    "AED": 3.67,
    "BDT": 109.5,
    "BRL": 4.97,
    "KRW": 1310.0,
    "MYR": 4.72,
    "THB": 35.6,
    "ZAR": 18.9,
    "SEK": 10.5,
    "NOK": 10.6,
    "NZD": 1.64,
}


def _load_cache():
    """Load cached rates from disk."""
    try:
        if CACHE_FILE.exists():
            data = json.loads(CACHE_FILE.read_text())
            if time.time() - data.get("timestamp", 0) < CACHE_TTL:
                return data.get("rates")
    except Exception:
        pass
    return None


def _save_cache(rates):
    """Save rates to disk cache."""
    try:
        CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
        CACHE_FILE.write_text(
            json.dumps(
                {
                    "timestamp": time.time(),
                    "rates": rates,
                }
            )
        )
    except Exception:
        pass


def fetch_exchange_rates(base="USD"):
    """
    Fetch latest exchange rates.
    Uses free API: https://open.er-api.com/v6/latest/{base}
    Falls back to cached or static rates on failure.
    """
    # Try cache first
    cached = _load_cache()
    if cached:
        return cached

    # Try fetching from free API
    try:
        url = f"https://open.er-api.com/v6/latest/{base}"
        req = urllib.request.Request(
            url, headers={"User-Agent": "SmartFinanceTracker/1.0"}
        )
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode())
            if data.get("result") == "success":
                rates = data["rates"]
                _save_cache(rates)
                return rates
    except Exception as e:
        logger.warning(f"Failed to fetch exchange rates: {e}")

    # Fallback to static rates
    return FALLBACK_RATES


def convert_currency(amount, from_currency, to_currency):
    """
    Convert amount from one currency to another.
    Returns (converted_amount, exchange_rate) tuple.
    """
    if from_currency == to_currency:
        return Decimal(str(amount)), Decimal("1.0")

    rates = fetch_exchange_rates("USD")

    from_rate = rates.get(from_currency)
    to_rate = rates.get(to_currency)

    if not from_rate or not to_rate:
        raise ValueError(f"Unsupported currency pair: {from_currency} -> {to_currency}")

    # Convert: amount_in_from -> USD -> to_currency
    rate = Decimal(str(to_rate)) / Decimal(str(from_rate))
    converted = Decimal(str(amount)) * rate

    return converted.quantize(Decimal("0.01")), rate.quantize(Decimal("0.000001"))


def get_exchange_rate(from_currency, to_currency):
    """Get the exchange rate between two currencies."""
    if from_currency == to_currency:
        return Decimal("1.0")

    rates = fetch_exchange_rates("USD")
    from_rate = rates.get(from_currency)
    to_rate = rates.get(to_currency)

    if not from_rate or not to_rate:
        raise ValueError(f"Unsupported currency pair: {from_currency} -> {to_currency}")

    rate = Decimal(str(to_rate)) / Decimal(str(from_rate))
    return rate.quantize(Decimal("0.000001"))
