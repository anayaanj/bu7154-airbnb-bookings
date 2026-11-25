<script>
  // The share of positive reviews, month by month, for the two chosen cities.
  import { onMount } from 'svelte';
  import { scaleLinear, scaleTime, line, format, bisector } from 'd3';
  import { pct, whole, WIDTH } from './format.js';
  import Method from './Method.svelte';

  let { city, versus } = $props();
  let all = $state([]);
  let hover = $state(null);   // index into the month axis
  onMount(async () => {
    const data = await fetch('data/sentiment.json').then((r) => r.json());
    all = data.map((d) => ({ ...d, months: d.months.map((m) => ({ ...m, date: new Date(m.month + '-01') })) }));
  });

  const W = WIDTH, H = 300, M = { top: 16, right: 16, bottom: 28, left: 44 };
  const month = (d) => d.toLocaleDateString('en-GB', { month: 'short', year: 'numeric', timeZone: 'UTC' });
  let cities = $derived([city, versus].map((c) => all.find((s) => s.slug === c?.slug)).filter(Boolean));
  let months = $derived(cities.flatMap((c) => c.months));
  let dates = $derived([...new Set(months.map((m) => m.month))].sort().map((m) => new Date(m + '-01')));
  let x = $derived(scaleTime([dates[0], dates.at(-1)], [M.left, W - M.right]));
  let y = $derived(scaleLinear([Math.floor(Math.min(...months.map((m) => m.positive)) * 100) / 100, 1], [H - M.bottom, M.top]));
  let share = $derived(line((m) => x(m.date), (m) => y(m.positive)));
  const at = (c, d) => c.months.find((m) => +m.date === +d);

  // A year's share of positive comments, weighted by the number of comments each month.
  function year(c, y) {
    const rows = c.months.filter((m) => m.month.startsWith(y));
    return rows.reduce((s, m) => s + m.positive * m.english, 0) / rows.reduce((s, m) => s + m.english, 0);
  }
  let title = $derived.by(() => {
    const c = cities[0];
    if (!c || c.slug !== city.slug) return '';
    const [first, last] = [c.months[0].month.slice(0, 4), c.months.at(-1).month.slice(0, 4)];
    return `Nearly every ${c.city} review is positive: ${format('.0%')(year(c, first))} in ${first}, ${format('.0%')(year(c, last))} in ${last}.`;
  });

  function move(event) {
    const box = event.currentTarget.getBoundingClientRect();
    const i = bisector((d) => d).center(dates, x.invert(((event.clientX - box.left) / box.width) * W));
    hover = Math.max(0, Math.min(dates.length - 1, i));
  }
</script>

{#if title}
  <figure>
    <h3>{title}</h3>
    <p class="context">
      {#each cities as c, i}<span class="key k{i}"></span>{c.city}{/each}
    </p>
    <div class="plot">
      <svg viewBox="0 0 {W} {H}" role="img" aria-label={title} onpointermove={move} onpointerleave={() => (hover = null)}>
        {#each y.ticks(5) as t}
          <line class="grid" x1={M.left} x2={W - M.right} y1={y(t)} y2={y(t)} />
          <text class="tick" x={M.left - 8} y={y(t)} dy="0.32em" text-anchor="end">{format('.0%')(t)}</text>
        {/each}
        {#each x.ticks(W / 90) as t}
          <text class="tick" x={x(t)} y={H - M.bottom + 18} text-anchor="middle">{t.getUTCFullYear()}</text>
        {/each}
        {#each cities as c, i}<path class="k{i}" d={share(c.months)} />{/each}
        {#if hover !== null}
          <line class="cursor" x1={x(dates[hover])} x2={x(dates[hover])} y1={M.top} y2={H - M.bottom} />
          {#each cities as c, i}
            {@const m = at(c, dates[hover])}
            {#if m}<circle class="k{i}" cx={x(m.date)} cy={y(m.positive)} r="4" />{/if}
          {/each}
        {/if}
      </svg>
      {#if hover !== null}
        <div class="tip" style="left: {(x(dates[hover]) / W) * 100}%; top: 6%" class:flip={hover > dates.length / 2}>
          <b>{month(dates[hover])}</b>
          {#each cities as c, i}
            {@const m = at(c, dates[hover])}
            {#if m}
              <span class="k{i}">{c.city} <i>{pct(m.positive)} positive · {pct(m.negative)} negative</i></span>
              <span>Reviews <i>{whole(m.reviews)} · {whole(m.english)} in English</i></span>
            {/if}
          {/each}
        </div>
      {/if}
    </div>
    <Method
      summary="Every English review comment gets a sentiment score from −1 to +1. A comment counts as positive at +0.05 or above and negative at −0.05 or below. Each point is one month's share of positive comments."
      rows={[
        ['Scoring', 'VADER (Hutto & Gilbert, 2014)', { hint: 'A rule-based sentiment scorer built for short, informal text. It reads English only.' }],
        ['Comments scored', cities.map((c) => `${c.city} ${whole(c.english_total)} of ${whole(c.reviews_total)}`).join(' · '), { hint: 'Only English comments are scored. In a sample of 1,911 Paris comments translated from other languages, 95.2% were positive against 97.7% of English ones, so English-only scoring slightly overstates positivity.' }],
        ['Months shown', 'Those with at least 300 English comments', { hint: 'With fewer comments a monthly share jumps around too much to read.' }],
        ['Vertical axis', 'Starts well above 0%', { hint: 'The share only moves within a few points, so the chart zooms in. The change is small in absolute terms.' }],
      ]}
      source={{ label: 'Code: build_atlas.py, Airbnb_Project_Guided.ipynb (Cell 10)', href: 'https://github.com/anayaanj/predicting-airbnb-bookings' }}
    />
  </figure>
{:else if all.length}
  <p class="muted">Review comments have not been scored for {city.city}.</p>
{/if}

<style>
  figure { margin: 0; }
  .plot { position: relative; }
  svg { width: 100%; height: auto; display: block; }
  h3 { margin-bottom: 8px; }
  .context { display: flex; align-items: center; gap: 8px; color: var(--muted-strong); font-size: 13px; margin-bottom: 12px; }
  .key { width: 10px; height: 10px; border-radius: 50%; }
  .key.k1 { margin-left: 16px; }
  .key.k0 { background: var(--accent); }
  .key.k1 { background: var(--warm); }
  .grid { stroke: #ffffff12; }
  .tick { fill: var(--muted); font-size: 11px; }
  path { fill: none; stroke-width: 1.8; }
  .k0 { stroke: var(--accent); }
  .k1 { stroke: var(--warm); }
  circle { fill: var(--panel); stroke-width: 2; }
  .cursor { stroke: #ffffff40; }
  .tip { transform: translateX(14px); }
  .tip.flip { transform: translateX(calc(-100% - 14px)); }
  .tip span.k0 { color: var(--accent); }
  .tip span.k1 { color: var(--warm); }
  .muted { color: var(--muted); }
</style>
