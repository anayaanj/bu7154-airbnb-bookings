<script>
  // One predictor's effect on reviews in every city: incidence rate ratio with its 95% confidence interval.
  import { scaleLog } from 'd3';
  import { app, city } from './state.svelte.js';
  import { effect, whole, WIDTH } from './format.js';
  import { longStayNote } from './predictors.js';
  import Method from './Method.svelte';

  let { onpick } = $props();

  // label, the sentence's subject for a city, and what "one standard deviation more" means there
  const PREDICTORS = {
    superhost: ['Superhost', (c) => `${c.city} superhosts get`, (irr) => (irr >= 1.5 ? 'of other hosts' : 'than other hosts')],
    n_amenities_z: ['Amenities', (c) => `In ${c.city}, ${Math.round(c.scale.n_amenities.sd)} more amenities go with`, () => ''],
    log_price_z: ['Price', (c) => `In ${c.city}, a price ${Math.exp(c.scale.log_price.sd).toFixed(1)}× higher goes with`, () => ''],
    entire_home: ['Entire home', (c) => `${c.city} entire homes get`, (irr) => (irr >= 1.5 ? 'of private or shared rooms' : 'than private or shared rooms')],
    host_years_z: ['Host tenure', (c) => `In ${c.city}, ${Math.round(c.scale.host_years.sd)} more years of hosting go with`, () => ''],
  };
  let predictor = $state('superhost');
  let hover = $state(null);

  const W = WIDTH, ROW = 20, M = { top: 28, right: 48, left: 116 };
  let rows = $derived(app.cities
    .map((c) => {
      const e = c.negative_binomial[predictor];
      return { c, irr: Math.exp(e.b), low: Math.exp(e.low), high: Math.exp(e.high), p: e.p };
    })
    .sort((a, b) => b.irr - a.irr));
  let x = $derived(scaleLog(
    [Math.min(0.5, ...rows.map((r) => r.low)), Math.max(2, ...rows.map((r) => r.high))], [M.left, W - M.right]));
  let H = $derived(M.top + rows.length * ROW + 8);
  const clear = (r) => r.low > 1 || r.high < 1;

  let selected = $derived(rows.find((r) => r.c.slug === app.slug));
  let rises = $derived(rows.filter((r) => r.low > 1));
  let drops = $derived(rows.filter((r) => r.high < 1).reverse());   // largest drop first
  let title = $derived.by(() => {
    const [label, subject, versus] = PREDICTORS[predictor];
    if (!clear(selected)) return `In ${selected.c.city}, ${label.toLowerCase()} makes no clear difference to reviews.`;
    return `${subject(selected.c)} ${effect(selected.irr)} ${versus(selected.irr)}`.trim() + '.';
  });
  // Where the selected city sits among all places, and how the others split.
  let context = $derived.by(() => {
    if (!clear(selected)) return `Clear in ${rises.length + drops.length} of ${rows.length} places.`;
    const group = selected.irr > 1 ? rises : drops;
    return `Same direction in ${group.length} of ${rows.length} places.`;
  });
  let note = $derived(predictor === 'log_price_z' ? longStayNote(selected.c) : null);
</script>

<figure>
  <div class="tabs" role="tablist">
    {#each Object.entries(PREDICTORS) as [key, [label]]}
      <button role="tab" aria-selected={predictor === key} onclick={() => (predictor = key)}>{label}</button>
    {/each}
  </div>
  <h3>{title}</h3>
  <p class="context">{context}</p>
  {#if note}<p class="note">{note}</p>{/if}
  <div class="plot">
    <svg viewBox="0 0 {W} {H}" role="img" aria-label={title} onpointerleave={() => (hover = null)}>
      {#each [0.25, 0.5, 1, 2, 3, 4].filter((t) => t >= x.domain()[0] && t <= x.domain()[1]) as t}
        <line class="grid" class:one={t === 1} x1={x(t)} x2={x(t)} y1={M.top - 6} y2={H} />
        <text class="tick" x={x(t)} y={M.top - 12} text-anchor="middle">{t === 1 ? 'no difference' : t + '×'}</text>
      {/each}
      {#each rows as r, i (r.c.slug)}
        {@const y = M.top + i * ROW + ROW / 2}
        <g class="row" class:selected={r.c.slug === app.slug} class:versus={r.c.slug === app.versus} class:ns={!clear(r)} style="transform: translateY({y}px)"
           onclick={() => onpick(r.c.slug)} onpointerenter={() => (hover = { r, i })} role="presentation">
          <rect x="0" y={-ROW / 2} width={W} height={ROW} />
          <text class="name" x={M.left - 12} dy="0.32em" text-anchor="end">{r.c.city}</text>
          <line class="ci" x1={x(r.low)} x2={x(r.high)} />
          <circle cx={x(r.irr)} r="4.5" />
          <text class="value" x={W - M.right + 10} dy="0.32em">{r.irr.toFixed(2)}×</text>
        </g>
      {/each}
    </svg>
    {#if hover}
      {@const r = hover.r}
      <div class="tip" style="left: {(x(r.irr) / W) * 100}%; top: {((M.top + hover.i * ROW) / H) * 100}%" class:flip={hover.i > rows.length / 2}>
        <b>{r.c.city}</b>
        <span>{effect(r.irr)} <i>{r.irr.toFixed(2)}×</i></span>
        <span>95% interval <i>{r.low.toFixed(2)}× to {r.high.toFixed(2)}×</i></span>
        <span>{clear(r) ? 'Significant' : 'Not significant'} <i>p {r.p < 0.001 ? '< 0.001' : '= ' + r.p.toFixed(3)}</i></span>
        <span>Listings <i>{whole(r.c.listings_analysed)}</i></span>
        {#if predictor === 'log_price_z' && r.c.share_long_stay >= 0.1}
          <span>Allowing for 30-night stays <i>{Math.exp(r.c.with_long_stay.log_price_z.b).toFixed(2)}×</i></span>
        {/if}
      </div>
    {/if}
  </div>
  <Method
    summary="Each dot is one place's estimate from the same Negative Binomial model. 2× means twice the expected reviews of an otherwise identical listing; the dashed line means no difference."
    rows={[
      ['Line through the dot', '95% confidence interval', { hint: 'The range the true effect plausibly lies in. Standard errors are clustered by host, because one host’s listings are not independent.' }],
      ['Hollow dot', 'Not significant at 5%', { hint: 'The interval crosses the no-difference line, so the data cannot tell this effect from zero.' }],
      ['Amenities, price, tenure', 'Per one standard deviation in that place', { hint: 'A standard deviation is the typical spread of a feature within a city. It lets cities with different prices and currencies be compared.' }],
      ['Sample', 'Up to 50,000 listings per place, random, seed BU7154G11'],
      ['Data', `${app.cities.length} InsideAirbnb snapshots, ${whole(app.cities.reduce((n, c) => n + c.listings_analysed, 0))} listings`],
    ]}
    source={{ label: 'Snapshot dates and file checks: atlas_data_log.csv', href: 'https://github.com/anayaanj/predicting-airbnb-bookings' }}
  />
</figure>

<style>
  figure { margin: 0; }
  .plot { position: relative; }
  svg { width: 100%; height: auto; display: block; }
  .tabs { margin-bottom: 16px; }
  h3 { margin-bottom: 6px; }
  .context { color: var(--muted); font-size: 14px; margin-bottom: 20px; }
  .note { color: var(--muted-strong); font-size: 13px; margin: -4px 0 12px; padding-left: 10px; border-left: 2px solid var(--accent); }
  .grid { stroke: #ffffff10; }
  .grid.one { stroke: #ffffff55; stroke-dasharray: 3 3; }
  .tick, .value { fill: var(--muted); font-size: 11px; }
  .row { cursor: pointer; transition: transform 0.6s ease; }
  .row rect { fill: transparent; }
  .row:hover rect { fill: #ffffff0a; }
  .name { fill: var(--muted-strong); font-size: 12px; }
  .ci { stroke: #7d8696; stroke-width: 1.5; }
  circle { fill: #b8c0cc; stroke: #b8c0cc; stroke-width: 1.5; }
  .ns circle { fill: var(--panel); }
  .selected .name, .selected .value { fill: var(--accent); font-weight: 600; }
  .selected .ci { stroke: var(--accent); }
  .selected circle { fill: var(--accent); stroke: var(--accent); }
  .versus .name, .versus .value { fill: var(--warm); font-weight: 600; }
  .versus .ci { stroke: var(--warm); }
  .versus circle { fill: var(--warm); stroke: var(--warm); }
  .selected.ns circle, .versus.ns circle { fill: var(--panel); }
  .tip { transform: translate(14px, 24px); }
  .tip.flip { transform: translate(14px, calc(-100% - 4px)); }
</style>
