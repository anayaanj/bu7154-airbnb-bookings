<script>
  // Two stages of the hurdle model: getting a first review, then collecting more.
  import { scaleLog } from 'd3';
  import { PREDICTORS, ratio, pValue } from './predictors.js';
  import { pct, whole, WIDTH } from './format.js';
  import Method from './Method.svelte';

  let { city } = $props();
  let hover = $state(null);

  const NAMES = Object.keys(PREDICTORS).filter((n) => n !== 'price_missing');
  const W = WIDTH, ROW = 46, M = { top: 28, right: 20, left: 138 };
  let rows = $derived(NAMES.map((name) => ({
    name, first: ratio(city.any_review_logit, name), more: ratio(city.more_reviews, name) })));
  let all = $derived(rows.flatMap((r) => [r.first.value, r.more.value]));
  let x = $derived(scaleLog([Math.min(0.5, ...all) / 1.1, Math.max(2, ...all) * 1.1], [M.left, W - M.right]));
  let H = $derived(M.top + rows.length * ROW + 4);

  // The feature whose two stages disagree most: helps one, hurts the other.
  let split = $derived(rows
    .filter((r) => r.first.clear && r.more.clear && r.first.value > 1 !== r.more.value > 1)
    .sort((a, b) => Math.abs(Math.log(b.first.value / b.more.value)) - Math.abs(Math.log(a.first.value / a.more.value)))[0]);
  let title = $derived(split
    ? `${PREDICTORS[split.name].who} in ${city.city} are ${split.first.value > 1 ? 'more' : 'less'} likely to get a first review, but collect ${split.more.value > 1 ? 'more' : 'fewer'} after it.`
    : `In ${city.city}, no feature clearly helps one stage and hurts the other.`);
</script>

<figure>
  <h3>{title}</h3>
  <p class="context">
    <span class="key first"></span>Odds of a first review
    <span class="key more"></span>Reviews after the first
  </p>
  <div class="plot">
    <svg viewBox="0 0 {W} {H}" role="img" aria-label={title} onpointerleave={() => (hover = null)}>
      {#each [0.25, 0.5, 1, 2, 3, 4].filter((t) => t >= x.domain()[0] && t <= x.domain()[1]) as t}
        <line class="grid" class:one={t === 1} x1={x(t)} x2={x(t)} y1={M.top - 6} y2={H} />
        <text class="tick" x={x(t)} y={M.top - 12} text-anchor="middle">{t === 1 ? 'no difference' : t + '×'}</text>
      {/each}
      {#each rows as r, i (r.name)}
        <g class="row" style="transform: translateY({M.top + i * ROW + ROW / 2}px)" onpointerenter={() => (hover = { r, i })} role="presentation">
          <rect x="0" y={-ROW / 2} width={W} height={ROW} />
          <text class="name" x={M.left - 12} dy="-0.25em" text-anchor="end">{PREDICTORS[r.name].label}</text>
          <text class="unit" x={M.left - 12} dy="1.35em" text-anchor="end">{PREDICTORS[r.name].unit(city)}</text>
          <line class="link" x1={x(r.first.value)} x2={x(r.more.value)} />
          <circle class="first" class:ns={!r.first.clear} cx={x(r.first.value)} r="5.5" />
          <circle class="more" class:ns={!r.more.clear} cx={x(r.more.value)} r="5.5" />
        </g>
      {/each}
    </svg>
    {#if hover}
      {@const r = hover.r}
      <div class="tip" style="left: {(x(Math.max(r.first.value, r.more.value)) / W) * 100}%; top: {((M.top + hover.i * ROW) / H) * 100}%" class:flip={hover.i > rows.length / 2}>
        <b>{PREDICTORS[r.name].label}</b>
        <span>Odds of a first review <i>{r.first.value.toFixed(2)}×</i></span>
        <span>95% interval <i>{r.first.low.toFixed(2)}× to {r.first.high.toFixed(2)}× · p {pValue(r.first.p)}</i></span>
        <span>Reviews after the first <i>{r.more.value.toFixed(2)}×</i></span>
        <span>95% interval <i>{r.more.low.toFixed(2)}× to {r.more.high.toFixed(2)}× · p {pValue(r.more.p)}</i></span>
      </div>
    {/if}
  </div>
  <Method
    summary="A hurdle model splits the question in two, as Sengupta et al. (2021) do. First: does a listing get any review at all? Second: among listings that did, how many?"
    rows={[
      ['First review', `Logit model on all ${whole(city.listings_analysed)} listings`, { hint: 'Shown as an odds ratio: above 1 means better odds of having at least one review.' }],
      ['Reviews after', `Zero-truncated Negative Binomial on the ${whole(city.listings_analysed * (1 - city.share_zero_reviews))} reviewed listings`, { hint: 'A count model that only looks at listings with one review or more, so it measures what goes with collecting more of them.' }],
      ['Reviewed', pct(1 - city.share_zero_reviews) + ' of listings'],
      ['Hollow dot', 'Not significant at 5%'],
      ['Reading the two dots', 'They are on different scales', { hint: 'Odds ratios and rate ratios are not the same unit. Compare which side of the dashed line each dot is on, not the distance between them.' }],
    ]}
    source={{ label: 'Code: build_atlas.py', href: 'https://github.com/anayaanj/predicting-airbnb-bookings' }}
  />
</figure>

<style>
  figure { margin: 0; }
  .plot { position: relative; }
  svg { width: 100%; height: auto; display: block; }
  h3 { margin-bottom: 12px; }
  .context { color: var(--muted-strong); font-size: 13px; margin-bottom: 20px; display: flex; align-items: center; gap: 8px; }
  .key { width: 10px; height: 10px; border-radius: 50%; display: inline-block; }
  .key.more { margin-left: 16px; }
  .key.first, circle.first { background: var(--accent); fill: var(--accent); stroke: var(--accent); }
  .key.more, circle.more { background: var(--cool); fill: var(--cool); stroke: var(--cool); }
  circle { stroke-width: 1.5; }
  circle.ns { fill: var(--panel); }
  .grid { stroke: #ffffff10; }
  .grid.one { stroke: #ffffff55; stroke-dasharray: 3 3; }
  .tick, .unit { fill: var(--muted); font-size: 11px; }
  .row rect { fill: transparent; }
  .row:hover rect { fill: #ffffff0a; }
  .name { fill: var(--text); font-size: 13px; }
  .link { stroke: #7d8696; stroke-width: 2; }
  .tip { transform: translate(14px, 30px); }
  .tip.flip { transform: translate(14px, calc(-100% - 4px)); }
</style>
