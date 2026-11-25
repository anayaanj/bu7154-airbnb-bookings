<script>
  // Host simulator: Model A's prediction for a listing the reader describes, against the city's typical listing.
  import { Tween } from 'svelte/motion';
  import { cubicOut } from 'svelte/easing';
  import { scaleLinear, area, format } from 'd3';
  import { predict, typical, negativeBinomial } from './model.js';
  import { money, whole, date } from './format.js';
  import Method from './Method.svelte';

  let { city } = $props();

  // svelte-ignore state_referenced_locally (the component is re-created when the city changes)
  let features = $state(typical(city));
  let priceStep = $state(0);   // price slider position: log steps around the city's median price
  let listing = $derived({ ...features, price: city.median_price * Math.exp(priceStep) });

  let base = $derived(predict(city, typical(city)));
  let now = $derived(predict(city, listing));
  const smooth = { duration: 450, easing: cubicOut };
  const reviews = Tween.of(() => now.reviews, smooth);
  const anyReview = Tween.of(() => now.anyReview, smooth);
  let change = $derived(now.reviews / base.reviews - 1);

  const W = 520, H = 150, MAX = 60;
  const x = scaleLinear([0, MAX], [0, W]);
  let pmf = $derived(negativeBinomial(reviews.current, city.alpha, MAX));
  let y = $derived(scaleLinear([0, 0.12], [H, 0]).clamp(true));
  let curve = $derived(area((d, k) => x(k), H, (d) => y(d))(pmf));
</script>

<div class="simulator">
  <div class="controls">
    <label class="switch"><input type="checkbox" bind:checked={() => !!features.superhost, (v) => (features.superhost = +v)} /> Superhost</label>
    <label class="switch"><input type="checkbox" bind:checked={() => !!features.entire_home, (v) => (features.entire_home = +v)} /> Entire home</label>
    <label>Amenities <output>{listing.n_amenities}</output>
      <input type="range" min="1" max="90" bind:value={features.n_amenities} /></label>
    <label>Price per night <output>{money(listing.price, city.currency)}</output>
      <input type="range" min="-1.4" max="1.4" step="0.02" bind:value={priceStep} /></label>
    <label>Guests <output>{listing.accommodates}</output>
      <input type="range" min="1" max="12" bind:value={features.accommodates} /></label>
    <label>Years hosting <output>{listing.host_years}</output>
      <input type="range" min="0" max="15" bind:value={features.host_years} /></label>
    <label>Host's listings <output>{listing.host_listings}</output>
      <input type="range" min="1" max="30" bind:value={features.host_listings} /></label>
  </div>

  <div class="result">
    <div class="numbers">
      <div><b>{reviews.current.toFixed(0)}</b><span>expected reviews</span></div>
      <div><b>{format('.0%')(anyReview.current)}</b><span>chance of a first review</span></div>
      <div class:up={change > 0.005} class:down={change < -0.005}>
        <b>{format('+.0%')(change)}</b><span>vs typical {city.city} listing</span>
      </div>
    </div>
    <svg viewBox="0 0 {W} {H + 18}" role="img" aria-label="Predicted distribution of reviews for this listing">
      <path d={curve} />
      <line x1={x(Math.min(MAX, reviews.current))} x2={x(Math.min(MAX, reviews.current))} y1="0" y2={H} />
      {#each [0, 20, 40, 60] as t}
        <text x={x(t)} y={H + 14} text-anchor={t === 0 ? 'start' : t === MAX ? 'end' : 'middle'}>{t}{t === MAX ? '+ reviews' : ''}</text>
      {/each}
    </svg>
    <p class="note">An association in today's listings, not a promise: superhost status is partly earned through bookings.</p>
    <Method
      summary="The listing you describe is put through the model fitted on this city's real listings. Each feature moves the prediction by its estimated effect."
      formula="expected reviews = exp(intercept + Σ coefficient × feature)"
      rows={[
        ['Expected reviews', 'Negative Binomial model of lifetime reviews'],
        ['Chance of a first review', 'Logit model of having at least one review', { hint: 'A separate model, because getting the first booking and getting more of them can depend on different things.' }],
        ['Shaded curve', 'How many reviews listings like this end up with', { hint: `The Negative Binomial spread around the expected value. Its dispersion in ${city.city} is α = ${city.alpha.toFixed(2)}.` }],
        ['Typical listing', `Not a superhost, ${money(city.median_price, city.currency)} a night, ${city.median_amenities} amenities, average capacity and tenure`],
        ['Fitted on', `${whole(city.listings_analysed)} ${city.city} listings, snapshot of ${date(city.snapshot)}`],
      ]}
      source={{ label: 'Coefficients: cities.json', href: 'https://github.com/anayaanj/predicting-airbnb-bookings' }}
    />
  </div>
</div>

<style>
  .simulator { display: grid; grid-template-columns: 240px 1fr; gap: 40px; align-items: start; }
  .controls { display: grid; gap: 14px; font-size: 13px; color: var(--muted-strong); }
  label { display: grid; grid-template-columns: 1fr auto; gap: 6px; }
  label input[type='range'] { grid-column: 1 / -1; width: 100%; accent-color: var(--accent); }
  output { color: var(--text); font-variant-numeric: tabular-nums; }
  .switch { display: flex; align-items: center; gap: 10px; cursor: pointer; }
  .switch input { width: 18px; height: 18px; accent-color: var(--accent); }
  .numbers { display: grid; grid-template-columns: repeat(3, 1fr); gap: 16px; margin-bottom: 20px; }
  .numbers b { display: block; font-size: 40px; font-weight: 600; letter-spacing: -0.02em; font-variant-numeric: tabular-nums; }
  .numbers span { font-size: 12px; color: var(--muted); }
  .up b { color: var(--cool); }
  .down b { color: var(--accent); }
  svg { width: 100%; height: auto; display: block; overflow: visible; }
  path { fill: #ffffff1c; stroke: none; }
  line { stroke: var(--text); stroke-width: 1.5; }
  text { fill: var(--muted); font-size: 11px; }
  .note { font-size: 12px; color: var(--muted); margin: 14px 0 0; }
  @media (max-width: 760px) {
    .simulator { grid-template-columns: 1fr; gap: 24px; }
    .numbers b { font-size: 28px; }
  }
</style>
