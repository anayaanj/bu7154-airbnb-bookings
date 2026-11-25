<script>
  // Do the published findings hold? Each published direction against the estimates for the two chosen cities.
  import Method from './Method.svelte';

  let { city, versus } = $props();

  // variable: [label, published direction, source]
  const FINDINGS = {
    superhost: ['Superhost', '+', 'Both'], host_years_z: ['Host tenure', '+', 'Both'],
    log_host_listings_z: ["Host's listings", '-', 'Sengupta'], accommodates_z: ['Capacity', '-', 'Sengupta'],
    n_amenities_z: ['Amenities', '+', 'Both'], log_price_z: ['Price', '-', 'Biswas'],
    has_profile_pic: ['Host profile photo', '+', 'Both'], identity_verified: ['Identity verified', '+', 'Biswas'],
    log_desc_words_z: ['Description length', '+', 'Both'], lix_z: ['Description readability', '+', 'Biswas'],
    promo_per_100_z: ['Promotional words', '+', 'Biswas'], desc_pos_z: ['Description positivity', '-', 'Sengupta'],
    desc_neg_z: ['Description negativity', '+', 'Sengupta'], review_scores_rating_z: ['Overall rating', '+', 'Both'],
    review_scores_communication_z: ['Communication score', '+', 'Sengupta'],
    review_scores_cleanliness_z: ['Cleanliness score', '+', 'Sengupta'],
    share_positive_z: ['Share of positive reviews', '+', 'Biswas'], review_neg_z: ['Review negativity', '-', 'Biswas'],
    host_response_time: ['Host response time', '+', 'Sengupta'], instant_bookable: ['Instant booking', '+', 'Both'],
  };
  const WORDS = { holds: 'Holds', reversed: 'Reversed', unclear: 'No clear effect', empty: 'Not in the data' };
  const EXPECTED = { '+': 'more reviews', '-': 'fewer reviews' };

  let hover = $state(null);
  let columns = $derived(city.deep ? [city, versus].filter((c) => c?.deep) : []);

  // The scorecard's rule: significant at 5% in the published direction holds; the other way is reversed.
  function cell(c, variable) {
    const e = c.deep.estimates[variable];
    if (!e) return { city: c.city, status: 'empty' };
    const status = e.p >= 0.05 ? 'unclear' : (e.irr > 1 ? '+' : '-') === FINDINGS[variable][1] ? 'holds' : 'reversed';
    return { city: c.city, status, irr: e.irr.toFixed(2) };
  }
  let rows = $derived(Object.entries(FINDINGS).map(([variable, [label, expected, source]]) => ({
    variable, label, expected, source, cells: columns.map((c) => cell(c, variable)) })));
  const count = (i, status) => rows.filter((r) => r.cells[i].status === status).length;
  let testable = $derived(rows.filter((r) => r.cells[0]?.status !== 'empty').length);
  let title = $derived(columns.length === 2
    ? `${count(0, 'holds')} of ${testable} published findings hold in ${columns[0].city}, ${count(1, 'holds')} in ${columns[1].city}.`
    : `${count(0, 'holds')} of ${testable} published findings hold in ${columns[0].city}.`);
</script>

{#if columns.length}
  <figure>
    <h3>{title}</h3>
    <p class="context">
      {#each Object.entries(WORDS) as [status, word]}<span class="cell {status}"></span>{word}{/each}
    </p>
    <div class="grid" style="--columns: {columns.length}" onpointerleave={() => (hover = null)} role="presentation">
      <span></span><span class="head expected">Published</span>{#each columns as c}<span class="head">{c.city}</span>{/each}
      {#each rows as r (r.variable)}
        <span class="name">{r.label}</span>
        <span class="expected">{EXPECTED[r.expected]}</span>
        {#each r.cells as cell}
          <span class="cell {cell.status}" onpointerenter={() => (hover = { r, cell })} role="presentation">{cell.irr ? cell.irr + '×' : ''}</span>
        {/each}
      {/each}
    </div>
    {#if hover}
      <p class="detail">
        <b>{hover.r.label}, {hover.cell.city}.</b>
        {hover.r.source === 'Both' ? 'Both papers' : hover.r.source + ' et al.'} report {EXPECTED[hover.r.expected]}.
        {hover.cell.irr ? `We estimate ${hover.cell.irr}×: ${WORDS[hover.cell.status].toLowerCase()}.` : 'The field is empty in the InsideAirbnb file, so it cannot be tested.'}
      </p>
    {:else}
      <p class="detail muted">Hover a tile for the detail.</p>
    {/if}
    <Method
      summary="Each row is a finding from Biswas et al. (2020) or Sengupta et al. (2021). A tile holds if our estimate is significant at 5% in the published direction, is reversed if significant the other way, and shows no clear effect otherwise."
      rows={[
        ['Host and listing features', 'Model A+, all listings', { hint: 'Model A plus text-mining variables from the listing description and host profile.' }],
        ['Review scores and sentiment', 'Model B, reviewed listings only', { hint: 'These exist only for listings with reviews. Sentiment is scored on English comments with VADER.' }],
        ['Number in the tile', 'Incidence rate ratio', { hint: 'The multiplier on expected reviews, per standard deviation for features measured on a scale.' }],
        ['Sample', 'Up to 50,000 listings per city, random, seed BU7154G11'],
      ]}
      source={{ label: 'Airbnb_Project_Guided.ipynb, run once per city', href: 'https://github.com/anayaanj/predicting-airbnb-bookings' }}
    />
  </figure>
{:else}
  <p class="muted">The full model has not been run for {city.city}.</p>
{/if}

<style>
  figure { margin: 0; }
  h3 { margin-bottom: 8px; }
  .context { display: flex; flex-wrap: wrap; align-items: center; gap: 6px; color: var(--muted-strong); font-size: 12px; margin-bottom: 16px; }
  .context .cell { width: 12px; height: 12px; min-height: 0; border-radius: 3px; margin-left: 10px; }
  .context .cell:first-child { margin-left: 0; }
  .grid { display: grid; grid-template-columns: 1fr 1.1fr repeat(var(--columns), 96px); gap: 4px 8px; align-items: center; font-size: 13px; }
  .head { color: var(--muted); font-size: 11px; text-transform: uppercase; letter-spacing: 0.04em; }
  .grid .head:nth-child(n + 3) { text-align: center; }
  .name { color: var(--text); }
  .expected { color: var(--muted); font-size: 12px; }
  .cell { min-height: 24px; border-radius: 5px; display: grid; place-items: center; font-size: 11px; font-weight: 600;
          font-variant-numeric: tabular-nums; border: 1.5px solid transparent; }
  .cell.holds { background: var(--cool); color: #08121f; }
  .cell.reversed { background: var(--accent); color: #1f0906; }
  .cell.unclear { border-color: #5d6573; color: var(--muted-strong); }
  .cell.empty { background: repeating-linear-gradient(135deg, #ffffff14 0 4px, transparent 4px 8px); }
  .grid .cell:hover { outline: 1.5px solid var(--text); outline-offset: 1px; }
  .detail { margin-top: 14px; font-size: 13px; color: var(--muted-strong); min-height: 2.6em; }
  .detail b { color: var(--text); }
  .muted { color: var(--muted); }
  @media (max-width: 640px) {
    .grid { grid-template-columns: 1fr repeat(var(--columns), 64px); }
    .expected { display: none; }
  }
</style>
