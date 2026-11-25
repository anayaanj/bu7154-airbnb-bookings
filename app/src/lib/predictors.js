// Model A's predictors in plain words. unit(c): what the estimate compares, in city c.
const sd = (c, name) => c.scale[name].sd;

export const PREDICTORS = {
  superhost: { label: 'Superhost', who: 'Superhosts', unit: () => 'vs other hosts' },
  n_amenities_z: { label: 'Amenities', who: 'Listings with more amenities', unit: (c) => `per ${Math.round(sd(c, 'n_amenities'))} more amenities` },
  host_years_z: { label: 'Host tenure', who: 'Longer-tenured hosts', unit: (c) => `per ${Math.round(sd(c, 'host_years'))} more years hosting` },
  log_host_listings_z: { label: "Host's listings", who: 'Hosts with more listings', unit: (c) => `per ${Math.exp(sd(c, 'log_host_listings')).toFixed(1)}× more listings` },
  accommodates_z: { label: 'Capacity', who: 'Bigger listings', unit: (c) => `per ${Math.round(sd(c, 'accommodates'))} more guests` },
  entire_home: { label: 'Entire home', who: 'Entire homes', unit: () => 'vs private or shared rooms' },
  log_price_z: { label: 'Price', who: 'Pricier listings', unit: (c) => `per ${Math.exp(sd(c, 'log_price')).toFixed(1)}× higher price` },
  price_missing: { label: 'No price shown', who: 'Listings with no price', unit: () => 'vs listings with a price' },
};

// exp(coefficient) with its 95% interval, for one predictor of one fitted model.
export function ratio(model, name) {
  const e = model[name];
  return { name, value: Math.exp(e.b), low: Math.exp(e.low), high: Math.exp(e.high), p: e.p, clear: e.low > 0 || e.high < 0 };
}

export const pValue = (p) => (p < 0.001 ? '< 0.001' : '= ' + p.toFixed(3));

// Listings that only take stays of 30 nights or more are cheap and rarely reviewed.
// Where they are common, they distort the price estimate; this says so, with the estimate allowing for them.
export function longStayNote(c) {
  if (c.share_long_stay < 0.1) return null;
  const adjusted = Math.exp(c.with_long_stay.log_price_z.b);
  return `${(c.share_long_stay * 100).toFixed(0)}% of ${c.city} listings only take stays of 30 nights or more: cheap and rarely reviewed. Allowing for that, the price effect is ${adjusted.toFixed(2)}×.`;
}
