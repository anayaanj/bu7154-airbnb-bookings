<script>
  // What a host-support team should do, with the selected city's own numbers, and what the data cannot say.
  import { ratio } from './predictors.js';
  import { effect, pct } from './format.js';

  let { city } = $props();
  const of = (name, model = city.negative_binomial) => ratio(model, name);
  const say = (r) => (r.clear ? effect(r.value) : 'no clear difference');
  const tone = (r) => (!r.clear ? 'none' : r.value > 1 ? 'up' : 'down');

  let price = $derived(of('log_price_z', city.share_long_stay > 0.1 ? city.with_long_stay : city.negative_binomial));
  let actions = $derived([
    [pct(city.share_zero_reviews), 'down', 'Target the first review', `of ${city.city} listings have never had one. That first booking is the hurdle to help with.`],
    ...[
      [of('superhost'), 'Make superhost the first goal', 'for superhosts, the strongest signal in most places.'],
      [of('n_amenities_z'), 'Get the amenities list completed', `per ${Math.round(city.scale.n_amenities.sd)} more amenities listed. It is the cheapest fix a host has.`],
      [price, 'Give price advice by city', `per ${Math.exp(city.scale.log_price.sd).toFixed(1)}× higher price. How much price matters differs from place to place.`],
      [of('price_missing'), 'Set closed listings aside', 'for listings showing no price. They have no bookable dates: closed, not unpopular.'],
    ].map(([r, action, why]) => [say(r), tone(r), action, why]),
  ]);
  const LIMITS = [
    'Reviews stand in for bookings. Not every stay leaves one.',
    'These are associations in one snapshot. Superhost status and scores are partly earned through bookings.',
    'Host response time and instant booking are empty in every file, so two published predictors cannot be tested.',
  ];
</script>

<div class="actions">
  <h3>What a host-support team should do in {city.city}.</h3>
  <ol>
    {#each actions as [number, tone, action, why]}
      <li><b class={tone}>{number}</b><div><strong>{action}</strong><p>{why}</p></div></li>
    {/each}
  </ol>
  <h4>What this cannot tell us</h4>
  <ul>{#each LIMITS as limit}<li>{limit}</li>{/each}</ul>
</div>

<style>
  ol { list-style: none; margin: 0; padding: 0; display: grid; gap: 4px; }
  ol li { display: grid; grid-template-columns: 190px 1fr; gap: 20px; align-items: baseline; padding: 14px 0; border-top: 1px solid #ffffff14; }
  b { font-size: 22px; font-weight: 600; letter-spacing: -0.01em; color: var(--muted-strong); font-variant-numeric: tabular-nums; }
  b.up { color: var(--cool); }
  b.down { color: var(--accent); }
  strong { font-weight: 600; }
  p { color: var(--muted); font-size: 14px; margin-top: 2px; }
  h4 { font-size: 12px; font-weight: 500; letter-spacing: 0.04em; text-transform: uppercase; color: var(--muted); margin: 24px 0 8px; }
  ul { margin: 0; padding-left: 18px; color: var(--muted-strong); font-size: 14px; display: grid; gap: 4px; }
  @media (max-width: 640px) { ol li { grid-template-columns: 1fr; gap: 4px; } }
</style>
