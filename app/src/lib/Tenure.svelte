<script>
  // Host tenure on lifetime reviews against reviews from the last 12 months, for every place.
  import { scaleLog } from 'd3';
  import { app } from './state.svelte.js';
  import { ratio, pValue } from './predictors.js';
  import { effect, whole, WIDTH } from './format.js';
  import Method from './Method.svelte';

  let { city, onpick } = $props();
  let hover = $state(null);

  const W = WIDTH, H = 340, M = { top: 40, bottom: 20 }, X = [W * 0.36, W * 0.64];
  let lines = $derived(app.cities.map((c) => ({
    c, life: ratio(c.negative_binomial, 'host_years_z'), recent: ratio(c.last_12_months, 'host_years_z') })));
  let all = $derived(lines.flatMap((l) => [l.life.value, l.recent.value]));
  let y = $derived(scaleLog([Math.min(...all) / 1.05, Math.max(...all) * 1.05], [H - M.bottom, M.top]));
  let mine = $derived(lines.find((l) => l.c.slug === city.slug));
  let shown = $derived(hover ?? mine);
  const rank = (l) => (l === shown ? 2 : l.c.slug === app.versus ? 1 : 0);   // drawn last = on top
  let years = $derived(Math.round(city.scale.host_years.sd));
  let title = $derived(mine.recent.value < 1 && mine.recent.clear
    ? `Long-time ${city.city} hosts: ${effect(mine.life.value)} ever, but ${effect(mine.recent.value).replace(' reviews', '')} last year.`
    : `Long-time ${city.city} hosts: ${effect(mine.life.value)} ever, ${mine.recent.clear ? effect(mine.recent.value).replace(' reviews', '') : 'no clear difference'} last year.`);
  let flipped = $derived(lines.filter((l) => l.life.value > 1 && l.recent.value < 1).length);
</script>

<figure>
  <h3>{title}</h3>
  <p class="context">Older listings have simply had longer to collect reviews. The advantage reverses in {flipped} of {lines.length} places.</p>
  <div class="plot">
    <svg viewBox="0 0 {W} {H}" role="img" aria-label={title} onpointerleave={() => (hover = null)}>
      <line class="one" x1={X[0] - 40} x2={X[1] + 40} y1={y(1)} y2={y(1)} />
      <text class="tick" x={X[1] + 44} y={y(1)} dy="-0.5em">no difference</text>
      <text class="head" x={X[0]} y="16" text-anchor="middle">All reviews ever</text>
      <text class="head" x={X[1]} y="16" text-anchor="middle">Last 12 months</text>
      {#each [...lines].sort((a, b) => rank(a) - rank(b)) as l (l.c.slug)}
        <g class="slope" class:selected={l === shown} class:versus={l.c.slug === app.versus} onpointerenter={() => (hover = l)} onclick={() => onpick(l.c.slug)} role="presentation">
          <line class="hit" x1={X[0]} x2={X[1]} y1={y(l.life.value)} y2={y(l.recent.value)} />
          <line x1={X[0]} x2={X[1]} y1={y(l.life.value)} y2={y(l.recent.value)} />
          <circle cx={X[0]} cy={y(l.life.value)} r="3.5" />
          <circle cx={X[1]} cy={y(l.recent.value)} r="3.5" />
        </g>
      {/each}
      <text class="end" x={X[0] - 12} y={y(shown.life.value)} dy="0.32em" text-anchor="end">{shown.c.city} {shown.life.value.toFixed(2)}×</text>
      <text class="end" x={X[1] + 12} y={y(shown.recent.value)} dy="0.32em">{shown.recent.value.toFixed(2)}×</text>
    </svg>
    {#if hover}
      <div class="tip" style="left: 50%; top: 14%">
        <b>{hover.c.city}</b>
        <span>All reviews ever <i>{hover.life.value.toFixed(2)}× · p {pValue(hover.life.p)}</i></span>
        <span>Last 12 months <i>{hover.recent.value.toFixed(2)}× · p {pValue(hover.recent.p)}</i></span>
        <span>Listings <i>{whole(hover.c.listings_analysed)}</i></span>
      </div>
    {/if}
  </div>
  <Method
    summary="The same model is fitted twice per place: once on every review a listing has ever had, once on the reviews from the 12 months before the snapshot. Each line joins the two estimates for host tenure."
    rows={[
      ['Left', 'number_of_reviews', { hint: 'InsideAirbnb’s lifetime count of reviews for the listing.' }],
      ['Right', 'number_of_reviews_ltm', { hint: 'InsideAirbnb’s count of reviews in the last twelve months, which cannot build up with a listing’s age.' }],
      ['Estimate', `Per ${years} more years of hosting in ${city.city} (one standard deviation)`],
      ['Model', 'Negative Binomial, same eight features, errors clustered by host'],
    ]}
    source={{ label: 'Code: build_atlas.py', href: 'https://github.com/anayaanj/predicting-airbnb-bookings' }}
  />
</figure>

<style>
  figure { margin: 0; }
  .plot { position: relative; }
  svg { width: 100%; height: auto; display: block; }
  h3 { margin-bottom: 6px; }
  .context { color: var(--muted); font-size: 14px; margin-bottom: 16px; }
  .one { stroke: #ffffff55; stroke-dasharray: 3 3; }
  .tick { fill: var(--muted); font-size: 11px; }
  .head { fill: var(--muted-strong); font-size: 12px; }
  .slope { cursor: pointer; }
  .slope line { stroke: #5d6573; stroke-width: 1.2; }
  .slope .hit { stroke: transparent; stroke-width: 12; }
  .slope circle { fill: #5d6573; }
  .slope.versus line:not(.hit) { stroke: var(--warm); stroke-width: 2; }
  .slope.versus circle { fill: var(--warm); }
  .slope.selected line:not(.hit) { stroke: var(--accent); stroke-width: 2.5; }
  .slope.selected circle { fill: var(--accent); }
  .end { fill: var(--accent); font-size: 12px; font-weight: 600; pointer-events: none; }
  .tip { transform: translateX(-50%); }
</style>
