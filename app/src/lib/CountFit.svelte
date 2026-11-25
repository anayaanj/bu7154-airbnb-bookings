<script>
  // Observed distribution of reviews against what Poisson and the Negative Binomial predict.
  import { scaleLinear, line, format } from 'd3';
  import { pct, whole, date, WIDTH } from './format.js';
  import Method from './Method.svelte';

  let { city, stage } = $props();   // stage 0: observed, 1: + Poisson, 2: + Negative Binomial

  const W = WIDTH, H = 340, M = { top: 24, right: 16, bottom: 36, left: 44 }, MAX = 40;
  const x = scaleLinear([0, MAX + 1], [M.left, W - M.right]);
  let y = $derived(scaleLinear([0, city.pmf.observed[0] * 1.08], [H - M.bottom, M.top]));
  let path = $derived(line((d, k) => x(k + 0.5), (d) => Math.max(M.top, y(d))));
  const cut = (values) => values.slice(0, MAX + 1);
  let peak = $derived(cut(city.pmf.poisson).reduce((best, d, k, all) => (d > all[best] ? k : best), 0));
  const small = (share) => (share < 0.001 ? '<0.1%' : pct(share));
  let hover = $state(null);   // the number of reviews under the pointer

  let titles = $derived([
    `Most ${city.city} listings have few reviews. ${pct(city.share_zero_reviews)} have none.`,
    `Poisson expects ${small(city.fit.zeros_poisson)} of listings at zero. The data has ${pct(city.share_zero_reviews)}.`,
    `The Negative Binomial expects ${pct(city.fit.zeros_negative_binomial)} at zero, close to the ${pct(city.share_zero_reviews)} observed.`,
  ]);
</script>

<figure>
  <h3>{titles[stage]}</h3>
  <div class="plot">
    <svg viewBox="0 0 {W} {H}" role="img" aria-label="Share of listings by number of reviews, observed and predicted"
         onpointerleave={() => (hover = null)}>
      {#each y.ticks(4) as t}
        <line class="grid" x1={M.left} x2={W - M.right} y1={y(t)} y2={y(t)} />
        <text class="tick" x={M.left - 8} y={y(t)} dy="0.32em" text-anchor="end">{format('.0%')(t)}</text>
      {/each}
      {#each [0, 10, 20, 30, 40] as t}
        <text class="tick" x={x(t + 0.5)} y={H - M.bottom + 18} text-anchor="middle">{t}</text>
      {/each}
      <text class="tick" x={W - M.right} y={H - 4} text-anchor="end">reviews per listing</text>

      {#each cut(city.pmf.observed) as share, k}
        <rect class:zero={k === 0} class:hover={hover === k} x={x(k) + 1} width={x(1) - x(0) - 2} y={y(share)} height={y(0) - y(share)} />
      {/each}
      <path class="poisson" class:on={stage >= 1} d={path(cut(city.pmf.poisson))} pathLength="1" />
      <path class="nb" class:on={stage >= 2} d={path(cut(city.pmf.negative_binomial))} pathLength="1" />

      <text class="label zero" x={x(1.4)} y={y(city.pmf.observed[0]) + 12}>{pct(city.share_zero_reviews)} never reviewed</text>
      {#if stage >= 1}
        <text class="label poisson" x={x(peak + 0.5)} y={y(city.pmf.poisson[peak]) - 10}>Poisson</text>
      {/if}
      {#if stage >= 2}
        <text class="label nb" x={x(3)} y={y(city.pmf.negative_binomial[2]) - 8}>Negative Binomial</text>
      {/if}
      {#each cut(city.pmf.observed) as _, k}
        <rect class="hit" x={x(k)} width={x(1) - x(0)} y={M.top} height={H - M.top - M.bottom} onpointerenter={() => (hover = k)} role="presentation" />
      {/each}
    </svg>
    {#if hover !== null}
      <div class="tip" style="left: {(x(hover + 0.5) / W) * 100}%" class:flip={hover > MAX / 2}>
        <b>{hover} review{hover === 1 ? '' : 's'}</b>
        <span>Observed <i>{pct(city.pmf.observed[hover])} · {whole(city.pmf.observed[hover] * city.listings_analysed)} listings</i></span>
        {#if stage >= 1}<span class="poisson">Poisson <i>{small(city.pmf.poisson[hover])}</i></span>{/if}
        {#if stage >= 2}<span class="nb">Negative Binomial <i>{pct(city.pmf.negative_binomial[hover])}</i></span>{/if}
      </div>
    {/if}
  </div>
  <Method
    summary="Each bar is the share of listings with exactly that many reviews. Each line is what a model predicts for the same listings: the probability of 0, 1, 2… reviews, averaged over all of them."
    rows={[
      ['Listings', `${whole(city.listings_analysed)} in ${city.city}, snapshot of ${date(city.snapshot)}`],
      ['Variance ÷ mean', city.variance_to_mean.toFixed(0), { hint: 'Poisson assumes the variance of the count equals its mean, a ratio of 1. A ratio this far above 1 means review counts are much more spread out than Poisson allows. The Negative Binomial adds a parameter for that spread.' }],
      ['AIC, Poisson', whole(city.fit.aic_poisson), { hint: 'Akaike Information Criterion: how well a model fits the data, with a penalty for extra parameters. Lower is better.' }],
      ['AIC, Negative Binomial', whole(city.fit.aic_negative_binomial), { hint: 'The much lower score means the Negative Binomial fits these listings far better than Poisson.' }],
      ['Predictors', 'Superhost, host tenure, host’s listings, capacity, amenities, entire home, price'],
    ]}
    source={{ label: 'Code: build_atlas.py', href: 'https://github.com/anayaanj/predicting-airbnb-bookings' }}
  />
</figure>

<style>
  figure { margin: 0; }
  .plot { position: relative; }
  svg { width: 100%; height: auto; display: block; }
  rect { fill: #4b5261; }
  rect.zero { fill: var(--accent); }
  rect.hover { fill: #8a93a5; }
  rect.zero.hover { fill: #ff9388; }
  rect.hit { fill: transparent; }
  .grid { stroke: #ffffff12; }
  .tick { fill: var(--muted); font-size: 11px; }
  path { fill: none; stroke-width: 2.5; stroke-dasharray: 1; stroke-dashoffset: 1; transition: stroke-dashoffset 1.2s ease; pointer-events: none; }
  path.on { stroke-dashoffset: 0; }
  path.poisson { stroke: var(--muted-strong); }
  path.nb { stroke: var(--cool); }
  .label { font-size: 12px; font-weight: 600; pointer-events: none; }
  .label.zero { fill: var(--accent); }
  .label.poisson { fill: var(--muted-strong); }
  .label.nb { fill: var(--cool); }
  .tip { top: 8%; transform: translateX(12px); }
  .tip.flip { transform: translateX(calc(-100% - 12px)); }
  .tip .nb { color: var(--cool); }
</style>
