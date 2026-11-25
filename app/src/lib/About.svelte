<script>
  import { app } from './state.svelte.js';
  import { whole } from './format.js';

  const REPO = 'https://github.com/anayaanj/predicting-airbnb-bookings';
  const TEAM = ['Euan Lynch', 'Jose Anaya', 'Julie Blevin', 'Krish Gupta', 'Anna Kriel'];
  const LINKS = [
    ['Code and full results', REPO],
    ['Data: Inside Airbnb (CC BY 4.0)', 'https://insideairbnb.com/get-the-data/'],
    ['Biswas, Sengupta & Chatterjee (2020)', 'https://www.sciencedirect.com/science/article/pii/S0167923620300798'],
    ['Sengupta et al. (2021)', 'https://www.sciencedirect.com/science/article/pii/S0148296321005968'],
  ];
  let dialog;
  let total = $derived(app.cities.reduce((n, c) => n + c.listings_analysed, 0));
</script>

<button class="pill" onclick={() => dialog.showModal()}>About</button>

<dialog bind:this={dialog} onclick={(e) => { if (e.target === dialog) dialog.close(); }}>
  <button class="close" aria-label="Close" onclick={() => dialog.close()}>×</button>
  <p class="eyebrow">BU7154 Foundations of Business Analytics · Trinity Business School</p>
  <h2>Predicting Airbnb Bookings</h2>
  <p>A host-support team at Airbnb wants to know which listing and host features predict bookings, and whether the predictors
    published by Biswas et al. (2020) and Sengupta et al. (2021) still hold.</p>
  <p>Airbnb publishes no bookings, so guest reviews stand in for them. We model the number of reviews with Negative Binomial
    regression: in depth for London and Paris, and with the same core model across {app.cities.length} places
    and {whole(total)} listings.</p>
  <p class="small">An independent student project, not affiliated with Airbnb.</p>
  <h3>Team</h3>
  <p>Group 11{TEAM.length ? ' · ' + TEAM.join(' · ') : ''}</p>
  <h3>Links</h3>
  <ul>
    {#each LINKS as [label, href]}<li><a {href} target="_blank" rel="noreferrer">{label} ↗</a></li>{/each}
  </ul>
</dialog>

<style>
  dialog {
    width: min(560px, calc(100vw - 32px)); padding: 32px; background: #12151c; color: var(--text);
    border: 1px solid #ffffff1f; border-radius: 16px;
  }
  dialog::backdrop { background: #000a; backdrop-filter: blur(4px); }
  h2 { margin-bottom: 16px; }
  h3 { font-size: 12px; font-weight: 500; letter-spacing: 0.04em; text-transform: uppercase; color: var(--muted); margin: 24px 0 8px; }
  p { color: var(--muted-strong); font-size: 15px; }
  .small { color: var(--muted); font-size: 13px; }
  ul { margin: 0; padding: 0; list-style: none; display: grid; gap: 6px; font-size: 14px; }
  a { color: var(--accent); text-decoration: none; }
  a:hover { text-decoration: underline; }
  .close { position: absolute; top: 14px; right: 16px; background: none; border: 0; font-size: 24px; color: var(--muted); cursor: pointer; }
  .close:hover { color: var(--text); }
</style>
