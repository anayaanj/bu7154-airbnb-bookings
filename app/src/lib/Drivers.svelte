<script>
  // Every predictor of Model A for the selected city, strongest first.
  import { scaleLog } from 'd3';
  import { PREDICTORS, ratio, pValue, longStayNote } from './predictors.js';
  import { effect, whole, date, WIDTH } from './format.js';
  import Method from './Method.svelte';

  let { city } = $props();
  let hover = $state(null);

  const W = WIDTH, ROW = 46, M = { top: 28, right: 48, left: 138 };
  let rows = $derived(Object.keys(PREDICTORS)
    .map((name) => ratio(city.negative_binomial, name))
    .sort((a, b) => b.value - a.value));
  let x = $derived(scaleLog([Math.min(0.5, ...rows.map((r) => r.low)), Math.max(2, ...rows.map((r) => r.high))], [M.left, W - M.right]));
  let H = $derived(M.top + rows.length * ROW + 4);
  let note = $derived(longStayNote(city));
  // The headline skips "no price" (a closed listing) and a price estimate distorted by long stays.
  let top = $derived(rows.filter((r) => r.clear && r.name !== 'price_missing' && !(note && r.name === 'log_price_z'))
    .sort((a, b) => Math.abs(Math.log(b.value)) - Math.abs(Math.log(a.value)))[0]);
  let title = $derived(top
    ? `In ${city.city}, ${PREDICTORS[top.name].who.toLowerCase()} stand out most: ${effect(top.value)}.`
    : `In ${city.city}, no feature clearly predicts reviews.`);
</script>

<figure>
  <h3>{title}</h3>
  {#if note}<p class="note">Price: {note}</p>{/if}
  <div class="plot">
    <svg viewBox="0 0 {W} {H}" role="img" aria-label={title} onpointerleave={() => (hover = null)}>
      {#each [0.25, 0.5, 1, 2, 3, 4].filter((t) => t >= x.domain()[0] && t <= x.domain()[1]) as t}
        <line class="grid" class:one={t === 1} x1={x(t)} x2={x(t)} y1={M.top - 6} y2={H} />
        <text class="tick" x={x(t)} y={M.top - 12} text-anchor="middle">{t === 1 ? 'no difference' : t + '×'}</text>
      {/each}
      {#each rows as r, i (r.name)}
        <g class="row" class:ns={!r.clear} class:up={r.clear && r.value > 1} class:down={r.clear && r.value < 1}
           style="transform: translateY({M.top + i * ROW + ROW / 2}px)" onpointerenter={() => (hover = { r, i })} role="presentation">
          <rect x="0" y={-ROW / 2} width={W} height={ROW} />
          <text class="name" x={M.left - 12} dy="-0.25em" text-anchor="end">{PREDICTORS[r.name].label}</text>
          <text class="unit" x={M.left - 12} dy="1.35em" text-anchor="end">{PREDICTORS[r.name].unit(city)}</text>
          <line class="bar" x1={x(1)} x2={x(r.value)} />
          <line class="ci" x1={x(r.low)} x2={x(r.high)} />
          <circle cx={x(r.value)} r="5" />
          <text class="value" x={W - M.right + 10} dy="0.32em">{r.value.toFixed(2)}×</text>
        </g>
      {/each}
    </svg>
    {#if hover}
      {@const r = hover.r}
      <div class="tip" style="left: {(x(r.value) / W) * 100}%; top: {((M.top + hover.i * ROW) / H) * 100}%" class:flip={hover.i > rows.length / 2}>
        <b>{PREDICTORS[r.name].label}</b>
        <span>{effect(r.value)} <i>{r.value.toFixed(2)}×</i></span>
        <span>95% interval <i>{r.low.toFixed(2)}× to {r.high.toFixed(2)}×</i></span>
        <span>{r.clear ? 'Significant' : 'Not significant'} <i>p {pValue(r.p)}</i></span>
      </div>
    {/if}
  </div>
  <Method
    summary="One Negative Binomial model with all eight features at once, so each estimate is the feature's effect with the other seven held equal."
    formula="reviews ~ superhost + tenure + host's listings + capacity + amenities + entire home + price + no price"
    rows={[
      ['Number shown', 'Incidence rate ratio', { hint: 'The multiplier on expected reviews. 2× means twice as many as an otherwise identical listing; 0.8× means 20% fewer.' }],
      ['Thin line', '95% confidence interval, clustered by host', { hint: 'The range the true effect plausibly lies in. One host’s listings are not independent, so they are grouped when measuring uncertainty.' }],
      ['"per … more"', 'One standard deviation in this city', { hint: 'For features measured on a scale, the comparison is between two listings one typical spread apart. Price and host’s listings are compared in ratios because they were modelled on a log scale.' }],
      ['No price shown', 'The listing has no bookable dates', { hint: 'Listings without a price have a median of 0 available days, so a missing price marks a closed listing, not a free one.' }],
      ['Listings', `${whole(city.listings_analysed)} in ${city.city}, snapshot of ${date(city.snapshot)}`],
    ]}
    source={{ label: 'Code: build_atlas.py', href: 'https://github.com/anayaanj/predicting-airbnb-bookings' }}
  />
</figure>

<style>
  figure { margin: 0; }
  .plot { position: relative; }
  svg { width: 100%; height: auto; display: block; }
  h3 { margin-bottom: 20px; }
  .context { color: var(--muted); font-size: 14px; margin-bottom: 12px; }
  .note { color: var(--muted-strong); font-size: 13px; margin: -8px 0 16px; padding-left: 10px; border-left: 2px solid var(--accent); }
  .grid { stroke: #ffffff10; }
  .grid.one { stroke: #ffffff55; stroke-dasharray: 3 3; }
  .tick, .value, .unit { fill: var(--muted); font-size: 11px; }
  .row rect { fill: transparent; }
  .row:hover rect { fill: #ffffff0a; }
  .row { transition: transform 0.6s ease; }
  .name { fill: var(--text); font-size: 13px; }
  .bar { stroke-width: 10; stroke: #ffffff14; }
  .up .bar { stroke: #6fb1ff33; }
  .down .bar { stroke: #ff6b5e33; }
  .ci { stroke: #9aa3b2; stroke-width: 1.5; }
  circle { fill: #b8c0cc; stroke: #b8c0cc; stroke-width: 1.5; }
  .up circle { fill: var(--cool); stroke: var(--cool); }
  .down circle { fill: var(--accent); stroke: var(--accent); }
  .ns circle { fill: var(--panel); }
  .tip { transform: translate(14px, 30px); }
  .tip.flip { transform: translate(14px, calc(-100% - 4px)); }
</style>
