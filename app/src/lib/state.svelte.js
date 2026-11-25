// Shared app state: the city list, the selected city and where the reader is in the story.
export const app = $state({
  cities: [],
  slug: 'london',
  versus: 'paris',  // the city the selected one is compared with
  step: 'hero',
  explore: false,
  globe: true,      // true: world view for picking a city; false: zoomed into the selected city
  show: 'all',      // explore mode: 'all' | 'never' | 'reviewed' | 'superhost'
});

export const city = () => app.cities.find((c) => c.slug === app.slug);
export const versus = () => app.cities.find((c) => c.slug === app.versus);

// Selecting the comparison city itself swaps the two.
export function select(slug) {
  if (slug === app.versus) app.versus = app.slug;
  app.slug = slug;
}
