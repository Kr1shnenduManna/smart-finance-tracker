/**
 * Shared currency formatting utility.
 * Import this instead of defining formatCurrency in each page.
 */

export const CURRENCY_SYMBOLS = {
  INR: '₹', USD: '$', EUR: '€', GBP: '£', JPY: '¥',
  CAD: 'C$', AUD: 'A$', CNY: '¥', CHF: 'CHF', SGD: 'S$',
  AED: 'د.إ', BDT: '৳', BRL: 'R$', KRW: '₩', MYR: 'RM',
  THB: '฿', ZAR: 'R', SEK: 'kr', NOK: 'kr', NZD: 'NZ$',
};

// Locale map for better number formatting per currency
const CURRENCY_LOCALES = {
  INR: 'en-IN', USD: 'en-US', EUR: 'de-DE', GBP: 'en-GB', JPY: 'ja-JP',
  CAD: 'en-CA', AUD: 'en-AU', CNY: 'zh-CN', CHF: 'de-CH', SGD: 'en-SG',
  AED: 'ar-AE', BDT: 'bn-BD', BRL: 'pt-BR', KRW: 'ko-KR', MYR: 'ms-MY',
  THB: 'th-TH', ZAR: 'en-ZA', SEK: 'sv-SE', NOK: 'nb-NO', NZD: 'en-NZ',
};

/**
 * Format a number as currency.
 * @param {number} n - The amount
 * @param {string} currency - ISO 4217 currency code (default: 'INR')
 * @returns {string}
 */
export function formatCurrency(n, currency = 'INR') {
  const locale = CURRENCY_LOCALES[currency] || 'en-US';
  const noDecimals = ['JPY', 'KRW'].includes(currency);
  try {
    return new Intl.NumberFormat(locale, {
      style: 'currency',
      currency,
      maximumFractionDigits: noDecimals ? 0 : 2,
    }).format(n || 0);
  } catch {
    return `${CURRENCY_SYMBOLS[currency] || currency} ${Number(n || 0).toLocaleString()}`;
  }
}
