<script>
  import { onMount } from 'svelte';
  import { Map as MapLibre, Marker, setWorkerUrl } from 'maplibre-gl';
  import workerUrl from 'maplibre-gl/dist/maplibre-gl-worker.mjs?worker&url';
  import { MapLibreOverlay } from '@deck.gl/maplibre';
  import { ScatterplotLayer } from '@deck.gl/layers';
  import { scaleSequentialLog } from 'd3';
  import { interpolateYlOrRd } from 'd3';
  import { color } from 'd3';
  import { app } from './state.svelte.js';
  import { loadPoints } from './data.js';

  let { onpick } = $props();

  setWorkerUrl(workerUrl);
  const STYLE = 'https://basemaps.cartocdn.com/gl/dark-matter-nolabels-gl-style/style.json';
  const DIM = [120, 130, 145, 70], CORAL = [255, 107, 94, 230], BLUE = [111, 177, 255, 230], HIDDEN = [120, 130, 145, 12];
  const heat = scaleSequentialLog(interpolateYlOrRd).domain([300, 1]);

  let container, map, overlay;
  let points = $state(null);

  onMount(() => {
    map = new MapLibre({
      container, style: STYLE, center: [5, 30], zoom: 1.6, attributionControl: { compact: true },
      scrollZoom: false, dragRotate: false,
    });
    map.on('style.load', () => {
      map.setProjection({ type: 'globe' });
      map.setSky({ 'atmosphere-blend': ['interpolate', ['linear'], ['zoom'], 0, 1, 5, 1, 7, 0] });
    });
    overlay = new MapLibreOverlay({ layers: [], getTooltip });
    map.addControl(overlay);
    map.on('moveend', spin);
    return () => map.remove();
  });

  // One clickable marker per city, shown on the globe.
  $effect(() => {
    if (!map) return;
    const markers = app.cities.map((c) => {
      const element = document.createElement('button');
      element.className = c.slug === app.slug ? 'city-marker selected' : 'city-marker';
      element.innerHTML = `<i style="--size:${6 + 40 * c.share_zero_reviews}px"></i><span>${c.city}</span>`;
      element.onclick = () => onpick(c.slug);
      return new Marker({ element, anchor: 'left', offset: [-8, 0], opacityWhenCovered: '0' }).setLngLat([c.lon, c.lat]).addTo(map);
    });
    return () => markers.forEach((m) => m.remove());
  });

  $effect(() => {
    points = null;
    const slug = app.slug;
    loadPoints(slug).then((p) => { if (slug === app.slug) points = p; });
  });

  // Camera: the world for picking a city, otherwise the selected city beside the story text.
  $effect(() => {
    if (!map) return;
    container.classList.toggle('globe', app.globe);
    app.explore ? map.scrollZoom.enable() : map.scrollZoom.disable();
    if (app.globe) {
      const c = app.cities.find((x) => x.slug === app.slug);
      map.flyTo({ center: [c?.lon ?? 5, 30], zoom: 2.2, duration: 2500, padding: { left: app.explore || innerWidth < 800 ? 0 : innerWidth * 0.3 } });
    } else if (points) {
      const left = app.explore ? 360 : Math.min(innerWidth * 0.45, 620);
      map.fitBounds(points.bounds, { padding: { left: innerWidth > 800 ? left : 20, right: 40, top: 90, bottom: 60 }, duration: 3000 });
    }
  });

  $effect(() => {
    if (!overlay) return;
    overlay.setProps({ layers: points ? [layer(points, app.explore ? app.show : 'all')] : [] });
  });

  function spin() {
    if (!app.globe) return;
    const c = map.getCenter();
    map.easeTo({ center: [c.lng + 25, c.lat], duration: 14000, easing: (t) => t });
  }

  // all: never-reviewed listings stand out. never / reviewed / superhost: only that group is lit.
  function fill(p, show, i) {
    const never = p.reviews[i] === 0;
    if (show === 'all') return never ? CORAL : DIM;
    if (show === 'never') return never ? CORAL : HIDDEN;
    if (show === 'superhost') return p.superhost[i] ? BLUE : HIDDEN;
    if (never) return HIDDEN;
    const c = color(heat(p.reviews[i]));
    return [c.r, c.g, c.b, 210];
  }

  function layer(p, show) {
    const colours = new Uint8Array(p.length * 4);
    for (let i = 0; i < p.length; i++) colours.set(fill(p, show, i), 4 * i);
    return new ScatterplotLayer({
      id: 'listings',
      data: { length: p.length, attributes: {
        getPosition: { value: p.positions, size: 2 },
        getFillColor: { value: colours, size: 4, normalized: true },
      } },
      getRadius: 30, radiusMinPixels: 1.2, radiusMaxPixels: 6,
      pickable: app.explore,
      transitions: { getFillColor: 600 },
    });
  }

  function getTooltip({ index }) {
    if (index < 0 || !points) return null;
    const price = Number.isNaN(points.price[index]) ? 'no price' : Math.round(points.price[index]);
    return { text: `${points.reviews[index]} reviews · ${price}${points.superhost[index] ? ' · superhost' : ''}`, className: 'map-tip' };
  }
</script>

<div class="map" bind:this={container}></div>

<style>
  .map { position: fixed; inset: 0; }
  .map :global(.city-marker) {
    display: none; align-items: center; gap: 8px; padding: 4px 0; border: 0; background: none;
    color: var(--text); font: 500 12px/1 var(--font); cursor: pointer;
  }
  .map:global(.globe) :global(.city-marker) { display: flex; }
  .map :global(.city-marker i) {
    width: var(--size); height: var(--size); border-radius: 50%; background: var(--accent);
    box-shadow: 0 0 12px var(--accent); opacity: 0.85; transition: transform 0.2s;
  }
  .map :global(.city-marker span) { opacity: 0; text-shadow: 0 1px 4px #000; transition: opacity 0.2s; }
  .map :global(.city-marker:hover i) { transform: scale(1.4); }
  .map :global(.city-marker:hover span), .map :global(.city-marker.selected span) { opacity: 1; }
  .map :global(.city-marker.selected i) { outline: 1.5px solid var(--text); outline-offset: 3px; }
  .map :global(.maplibregl-marker:hover) { z-index: 2; }
  :global(.map-tip) { font: 12px var(--font) !important; background: #14171f !important; color: var(--text) !important; border-radius: 6px; }
</style>
