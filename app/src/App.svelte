<script>
  import { onMount, tick } from 'svelte';
  import scrollama from 'scrollama';
  import { app, city, versus, select } from './lib/state.svelte.js';
  import { loadCities, summary } from './lib/data.js';
  import { pct, whole, money, date } from './lib/format.js';
  import Map from './lib/Map.svelte';
  import CountFit from './lib/CountFit.svelte';
  import Atlas from './lib/Atlas.svelte';
  import Simulator from './lib/Simulator.svelte';
  import Drivers from './lib/Drivers.svelte';
  import Hurdle from './lib/Hurdle.svelte';
  import Tenure from './lib/Tenure.svelte';
  import Rating from './lib/Rating.svelte';
  import Scorecard from './lib/Scorecard.svelte';
  import Actions from './lib/Actions.svelte';
  import Sentiment from './lib/Sentiment.svelte';
  import Method from './lib/Method.svelte';
  import Select from './lib/Select.svelte';
  import About from './lib/About.svelte';

  const MAP_STEPS = ['hero', 'zero', 'value', 'proxy'];
  const SHOW = [
    { value: 'all', label: 'All listings' },
    { value: 'never', label: 'Never reviewed' },
    { value: 'reviewed', label: 'With reviews' },
    { value: 'superhost', label: 'Superhosts' },
  ];
  let c = $derived(city());
  let v = $derived(versus());
  let total = $derived(app.cities.reduce((n, x) => n + x.listings_analysed, 0));
  let options = $derived(app.cities.map((x) => ({ value: x.slug, label: x.city })));
  let sampled = $derived(c && c.listings_raw > c.listings_analysed + 1);
  let stats = $state(null);

  onMount(async () => {
    app.cities = await loadCities();
    await tick();
    scrollama().setup({ step: '[data-step]', offset: 0.6 }).onStepEnter(({ element }) => {
      app.step = element.dataset.step;
      app.globe = app.step === 'hero';
    });
  });

  $effect(() => {
    const slug = app.slug, show = app.show;
    if (!app.explore || app.globe) return;
    summary(slug, show).then((s) => (stats = s), () => {});
  });

  function pick(slug) {
    select(slug);
    if (app.explore) app.globe = false;
    else if (app.step === 'hero') document.getElementById('problem').scrollIntoView({ behavior: 'smooth' });
  }

  function explore(on) {
    app.explore = on;
    app.show = 'all';
    app.globe = on ? false : app.step === 'hero';
  }
</script>

<Map onpick={pick} />
<div class="scrim" class:on={!app.explore && !MAP_STEPS.includes(app.step)}></div>

{#if c}
  <header>
    <Select label="City" {options} bind:value={() => app.slug, pick} />
    {#if !app.explore}
      <span class="vs">vs</span>
      <Select label="Compare with" options={options.filter((o) => o.value !== app.slug)} bind:value={app.versus} />
    {/if}
    <button class="pill" onclick={() => explore(!app.explore)}>{app.explore ? 'Back to story' : 'Explore'}</button>
    <About />
  </header>

  {#if app.explore}
    <aside class="panel explore">
      <button class="link" onclick={() => (app.globe = !app.globe)}>{app.globe ? `Back to ${c.city}` : '← Pick another city'}</button>
      {#if !app.globe}
        <h2>{c.city}</h2>
        <Select label="Show" options={SHOW} bind:value={app.show} />
        {#if stats}
          <dl class="stats">
            <div><dd>{whole(stats.listings)}</dd><dt>listings</dt></div>
            <div><dd>{pct(stats.never_reviewed)}</dd><dt>never reviewed</dt></div>
            <div><dd>{stats.mean_reviews.toFixed(1)}</dd><dt>mean reviews</dt></div>
            <div><dd>{money(stats.median_price, c.currency)}</dd><dt>median price</dt></div>
          </dl>
          <Method
            summary="These four numbers are calculated in your browser, live, from the listings now lit on the map."
            rows={[
              ['Query', stats.sql, { code: true }],
              ['Engine', 'DuckDB', { hint: 'A database that runs inside the web page, so the numbers come straight from the listing-level file, not from a pre-made summary.' }],
              ['Data', `InsideAirbnb, ${c.city}, snapshot of ${date(c.snapshot)}`],
            ]}
            source={{ label: 'Source file', href: c.source }} />
        {/if}
      {:else}
        <p class="muted">Pick a city on the globe.</p>
      {/if}
    </aside>
  {:else}
    <main>
      <section class="hero" data-step="hero">
        <div>
          <p class="eyebrow">Predicting Airbnb Bookings · {app.cities.length} places · {whole(total)} listings</p>
          <h1>What gets an Airbnb listing booked?</h1>
          <p class="muted">Pick a city, or scroll.</p>
        </div>
      </section>

      <section id="problem" data-step="zero">
        <div class="panel">
          <p class="big"><b>{pct(c.share_zero_reviews)}</b></p>
          <h2>of {c.city} listings have never had a review.</h2>
          <Method
            summary="We counted the listings with zero guest reviews and divided by all the listings analysed."
            formula={`${whole(c.share_zero_reviews * c.listings_analysed)} ÷ ${whole(c.listings_analysed)} = ${pct(c.share_zero_reviews)}`}
            rows={[
              ['Listings', sampled ? `Random sample of ${whole(c.listings_analysed)} from ${whole(c.listings_raw)}` : `All ${whole(c.listings_analysed)} in the file`,
                sampled ? { hint: 'The brief caps the analysis at 50,000 listings per city. The sample is random with seed BU7154G11, so it can be redrawn exactly.' } : undefined],
              ['Data', `InsideAirbnb, ${c.city}`],
              ['Snapshot', date(c.snapshot), { hint: 'The day InsideAirbnb collected these listings from the Airbnb site.' }],
              ['Downloaded', date(c.download_date)],
              ['File fingerprint', c.sha256.slice(0, 12) + '…', { hint: 'The start of the file’s SHA-256 checksum. Anyone who downloads the same file gets the same value, which proves the data is unchanged.' }],
            ]}
            source={{ label: 'Source file · InsideAirbnb, CC BY 4.0', href: c.source }} />
        </div>
      </section>

      <section data-step="value">
        <div class="panel">
          <h2>No stay, no fee.</h2>
          <p>Airbnb and its hosts earn only when a stay is booked. A listing that never gets one earns nothing for either.</p>
          <p>Knowing which features go with bookings tells a host-support team where to spend its effort.</p>
        </div>
      </section>

      <section data-step="proxy">
        <div class="panel">
          <h2>Reviews are the trace bookings leave.</h2>
          <p>Airbnb publishes no bookings. Guests can only review after a stay, so we count reviews, as Biswas et al. (2020) and Sengupta et al. (2021) do.</p>
        </div>
      </section>

      <section class="chart">
        <div class="sticky panel wide"><CountFit city={c} stage={['fit-1', 'fit-2'].indexOf(app.step) + 1} /></div>
        <div class="steps">
          <div data-step="fit-0"></div>
          <div data-step="fit-1"></div>
          <div data-step="fit-2"></div>
        </div>
      </section>

      <section data-step="drivers">
        <div class="panel wide"><Drivers city={c} /></div>
      </section>

      <section data-step="atlas">
        <div class="panel wide"><Atlas onpick={pick} /></div>
      </section>

      <section data-step="hurdle">
        <div class="panel wide"><Hurdle city={c} /></div>
      </section>

      <section data-step="tenure">
        <div class="panel wide"><Tenure city={c} onpick={pick} /></div>
      </section>

      <section data-step="rating">
        <div class="panel wide"><Rating city={c} /></div>
      </section>

      <section data-step="sentiment">
        <div class="panel wide"><Sentiment city={c} versus={v} /></div>
      </section>

      <section data-step="scorecard">
        <div class="panel wide"><Scorecard city={c} versus={v} /></div>
      </section>

      <section data-step="simulator">
        <div class="panel wide">
          <h3>Build a {c.city} listing.</h3>
          {#key c.slug}<Simulator city={c} />{/key}
        </div>
      </section>

      <section data-step="actions">
        <div class="panel wide"><Actions city={c} /></div>
      </section>

      <section class="end" data-step="end">
        <button class="cta" onclick={() => explore(true)}>Explore {c.city} →</button>
      </section>
    </main>
  {/if}
{/if}
