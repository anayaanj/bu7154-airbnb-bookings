import { format } from 'd3';

export const pct = format('.1%');
export const whole = (n) => Math.round(n).toLocaleString('en');
export const money = (value, currency) =>
  new Intl.NumberFormat('en', { style: 'currency', currency, maximumFractionDigits: 0 }).format(value);
export const date = (iso) =>
  new Date(iso).toLocaleDateString('en-GB', { day: 'numeric', month: 'short', year: 'numeric', timeZone: 'UTC' });

// An incidence rate ratio in words: "2.1× the reviews", "24% more reviews", "23% fewer reviews".
export function effect(irr) {
  if (irr >= 1.5) return `${irr.toFixed(1)}× the reviews`;
  return `${Math.abs((irr - 1) * 100).toFixed(0)}% ${irr >= 1 ? 'more' : 'fewer'} reviews`;
}

export const ordinal = (n) => n + (['th', 'st', 'nd', 'rd'][n % 100 > 10 && n % 100 < 14 ? 0 : n % 10] ?? 'th');

// Phones get a narrower chart canvas, so labels stay readable when the chart is scaled to the screen.
export const WIDTH = matchMedia('(max-width: 640px)').matches ? 420 : 640;
