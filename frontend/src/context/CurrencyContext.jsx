import { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { getAllExchangeRates } from '../api/endpoints';
import { useAuth } from './AuthContext';
import { formatCurrency, CURRENCY_SYMBOLS } from '../utils/currency';

const CurrencyContext = createContext(null);

// All existing data is stored in INR
const BASE_CURRENCY = 'INR';

export function CurrencyProvider({ children }) {
  const { user } = useAuth();
  const [rates, setRates] = useState(null);
  const preferredCurrency = user?.preferred_currency || 'INR';

  useEffect(() => {
    loadRates();
  }, [preferredCurrency]);

  const loadRates = async () => {
    try {
      const res = await getAllExchangeRates();
      if (res.data?.rates) {
        setRates(res.data.rates);
      }
    } catch (err) {
      console.error('Failed to load exchange rates:', err);
    }
  };

  /**
   * Convert an amount from one currency to the user's preferred currency.
   * @param {number} amount - The amount to convert
   * @param {string} fromCurrency - Source currency (defaults to 'INR')
   * @returns {number} converted amount
   */
  const convert = useCallback((amount, fromCurrency = BASE_CURRENCY) => {
    const n = parseFloat(amount) || 0;
    if (!rates || fromCurrency === preferredCurrency) return n;

    const fromRate = rates[fromCurrency];
    const toRate = rates[preferredCurrency];
    if (!fromRate || !toRate) return n;

    return n * (toRate / fromRate);
  }, [rates, preferredCurrency]);

  /**
   * Format and convert an amount for display.
   * Converts from fromCurrency to user's preferred currency, then formats.
   * @param {number} amount
   * @param {string} fromCurrency - Source currency (defaults to 'INR')
   * @returns {string} formatted string like "$405.12"
   */
  const fc = useCallback((amount, fromCurrency = BASE_CURRENCY) => {
    const converted = convert(amount, fromCurrency);
    return formatCurrency(converted, preferredCurrency);
  }, [convert, preferredCurrency]);

  const symbol = CURRENCY_SYMBOLS[preferredCurrency] || preferredCurrency;

  return (
    <CurrencyContext.Provider value={{ fc, convert, symbol, preferredCurrency, rates }}>
      {children}
    </CurrencyContext.Provider>
  );
}

export const useCurrency = () => useContext(CurrencyContext);
