<script>
  // Why a higher rating goes with fewer reviews: perfect scores belong to listings with few reviews.
  import { scaleLinear, format } from 'd3';
  import { perfectRatings } from './data.js';
  import { pct, whole, date, WIDTH } from './format.js';
  import Method from './Method.svelte';

  let { city } = $props();
  let result = $state(null);
  let rating = $derived(city.deep?.estimates.review_scores_rating_z);
  let hover = $state(null);
  $effect(() => {
    const slug = city.slug;
    result = null;
    perfectRatings(slug).then((r) => { if (slug === city.slug) result = r; });
  });

  const W = WIDTH, H = 280, M = { top: 28, right: 16, bottom: 44, left: 44 };
  let rows = $derived(result?.rows ?? []);
  let band = $derived((W - M.left - M.right) / Math.max(1, rows.length));
  let y = $derived(scaleLinear([0, Math.max(0.1, ...rows.map((r) => r.perfect)) * 1.15], [H - M.bottom, M.top]));
  const share = (v) => (v < 0.005 ? 'under 1%' : format('.0%')(v));
  let title = $derived(rows.length
    ? `${format('.0%')(rows[0].perfect)} of ${city.city} listings with 1–2 reviews have a perfect 5.0. With over 50 reviews, ${share(rows.at(-1).perfect)} do.`
    : 'Perfect scores belong to listings with few reviews.');
</script>

<figure>
  <h3>{title}</h3>
  {#if rating}
    <p class="context">
      {#if rating.p >= 0.05}In the full model, the rating shows no clear effect on reviews here ({rating.irr.toFixed(2)}×).
      {:else if rating.irr < 1}So in the full model a higher rating goes with <em>fewer</em> reviews: {rating.irr.toFixed(2)}×.
      {:else}Even so, in the full model a higher rating goes with <em>more</em> reviews here: {rating.irr.toFixed(2)}×.{/if}
    </p>
  {/if}
  <div class="plot">
    <svg viewBox="0 0 {W} {H}" role="img" aria-label={title} onpointerleave={() => (hover = null)}>
      {#each y.ticks(4) as t}
        <line class="grid" x1={M.left} x2={W - M.right} y1={y(t)} y2={y(t)} />
        <text class="tick" x={M.left - 8} y={y(t)} dy="0.32em" text-anchor="end">{format('.0%')(t)}</text>
      {/each}
      {#each rows as r, i (r.label)}
        <g onpointerenter={() => (hover = i)} role="presentation">
          <rect class="hit" x={M.left + i * band} width={band} y={M.top} height={H - M.top - M.bottom} />
          <rect class="bar" class:first={i === 0} class:hover={hover === i} x={M.left + i * band + band * 0.18} width={band * 0.64}
                y={y(r.perfect)} height={y(0) - y(r.perfect)} />
          <text class="value" x={M.left + (i + 0.5) * band} y={y(r.perfect) - 8} text-anchor="middle">{format('.0%')(r.perfect)}</text>
          <text class="tick" x={M.left + (i + 0.5) * band} y={H - M.bottom + 18} text-anchor="middle">{r.label}</text>
        </g>
      {/each}
      <text class="tick" x={W - M.right} y={H - 4} text-anchor="end">reviews per listing</text>
    </svg>
    {#if hover !== null}
      {@const r = rows[hover]}
      <div class="tip" style="left: {((M.left + (hover + 0.5) * band) / W) * 100}%; top: 10%" class:flip={hover > 2}>
        <b>{r.label} reviews</b>
        <span>Perfect 5.0 <i>{pct(r.perfect)}</i></span>
        <span>Average rating <i>{r.mean.toFixed(2)}</i></span>
        <span>Listings <i>{whole(r.listings)}</i></span>
      </div>
    {/if}
  </div>
  {#if result}
    <Method
      summary="Reviewed listings are grouped by how many reviews they have. Each bar is the share of that group whose overall rating is exactly 5.0. With one or two reviews, a single happy guest gives a perfect average; it takes many stays to keep one."
      rows={[
        ['Query', result.sql, { code: true }],
        ...(rating ? [['Rating effect', `${rating.irr.toFixed(2)}× per standard deviation of the rating`, { hint: 'From the full model (Model B), which adds review scores and review sentiment and uses reviewed listings only.' }]] : []),
        ['Data', `InsideAirbnb, ${city.city}, snapshot of ${date(city.snapshot)}`],
      ]}
      source={{ label: 'Model B: Airbnb_Project_Guided.ipynb', href: 'https://github.com/anayaanj/predicting-airbnb-bookings' }}
    />
  {/if}
</figure>

<style>
  figure { margin: 0; }
  .plot { position: relative; min-height: 120px; }
  svg { width: 100%; height: auto; display: block; }
  h3 { margin-bottom: 6px; }
  .context { color: var(--muted); font-size: 14px; margin-bottom: 16px; }
  em { color: var(--text); font-style: normal; font-weight: 600; }
  .grid { stroke: #ffffff12; }
  .tick { fill: var(--muted); font-size: 11px; }
  .hit { fill: transparent; }
  .bar { fill: #4b5261; }
  .bar.first { fill: var(--accent); }
  .bar.hover { fill: #8a93a5; }
  .bar.first.hover { fill: #ff9388; }
  .value { fill: var(--text); font-size: 12px; font-weight: 600; }
  .tip { transform: translateX(14px); }
  .tip.flip { transform: translateX(calc(-100% - 14px)); }
</style>
