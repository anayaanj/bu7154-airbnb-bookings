// The fitted Model A, evaluated in the browser from the coefficients in cities.json.
const TRANSFORM = {
  host_years: (x) => x.host_years,
  log_host_listings: (x) => Math.log1p(x.host_listings),
  accommodates: (x) => x.accommodates,
  n_amenities: (x) => x.n_amenities,
  log_price: (x) => Math.log(x.price),
};

function linear(coef, scale, x) {
  let eta = coef.Intercept.b + coef.superhost.b * x.superhost + coef.entire_home.b * x.entire_home;
  for (const [name, value] of Object.entries(TRANSFORM)) {
    eta += coef[`${name}_z`].b * ((value(x) - scale[name].mean) / scale[name].sd);
  }
  return eta;
}

// Expected lifetime reviews (Negative Binomial) and the chance of at least one review (hurdle logit).
export function predict(c, x) {
  return {
    reviews: Math.exp(linear(c.negative_binomial, c.scale, x)),
    anyReview: 1 / (1 + Math.exp(-linear(c.any_review_logit, c.scale, x))),
  };
}

// The city's typical listing: the simulator's starting point and comparison.
export function typical(c) {
  return {
    superhost: 0,
    entire_home: c.share_entire_home > 0.5 ? 1 : 0,
    host_years: Math.round(c.scale.host_years.mean),
    host_listings: 1,
    accommodates: Math.round(c.scale.accommodates.mean),
    n_amenities: c.median_amenities,
    price: c.median_price,
  };
}

function logGamma(z) {
  const g = [76.18009172947146, -86.50532032941677, 24.01409824083091, -1.231739572450155, 0.001208650973866179, -0.000005395239384953];
  let x = z, y = z, tmp = x + 5.5, sum = 1.000000000190015;
  tmp -= (x + 0.5) * Math.log(tmp);
  for (const c of g) sum += c / ++y;
  return -tmp + Math.log((2.5066282746310005 * sum) / x);
}

// Negative Binomial probabilities for 0..max reviews, given the expected count and the dispersion alpha.
export function negativeBinomial(mu, alpha, max) {
  const size = 1 / alpha, p = size / (size + mu);
  return Array.from({ length: max + 1 }, (_, k) =>
    Math.exp(logGamma(k + size) - logGamma(size) - logGamma(k + 1) + size * Math.log(p) + k * Math.log(1 - p)));
}
