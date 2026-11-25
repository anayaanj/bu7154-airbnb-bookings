<script>
  // Dropdown in the app's own style. options: [{ value, label }].
  let { value = $bindable(), options, label } = $props();
  let open = $state(false);
  let root;
  let current = $derived(options.find((o) => o.value === value));

  function choose(v) { value = v; open = false; }
</script>

<svelte:window onclick={(e) => { if (!root.contains(e.target)) open = false; }}
               onkeydown={(e) => { if (e.key === 'Escape') open = false; }} />

<div class="select" bind:this={root}>
  <button class="trigger" aria-haspopup="listbox" aria-expanded={open} aria-label={label} onclick={() => (open = !open)}>
    {current?.label}
    <svg viewBox="0 0 12 12" aria-hidden="true"><path d="M2.5 4.5 6 8l3.5-3.5" /></svg>
  </button>
  {#if open}
    <ul role="listbox" aria-label={label}>
      {#each options as o}
        <li role="option" aria-selected={o.value === value}>
          <button onclick={() => choose(o.value)}>{o.label}</button>
        </li>
      {/each}
    </ul>
  {/if}
</div>

<style>
  .select { position: relative; }
  .trigger {
    display: flex; align-items: center; justify-content: space-between; gap: 10px; width: 100%;
    background: #12151ccc; border: 1px solid #ffffff1f; border-radius: 999px; padding: 7px 14px 7px 16px;
    font-size: 13px; cursor: pointer; backdrop-filter: blur(8px); white-space: nowrap;
  }
  .trigger:hover, .trigger[aria-expanded='true'] { border-color: #ffffff55; }
  svg { width: 12px; height: 12px; fill: none; stroke: var(--muted-strong); stroke-width: 1.5; transition: transform 0.2s; }
  [aria-expanded='true'] svg { transform: rotate(180deg); }
  ul {
    position: absolute; top: calc(100% + 6px); left: 0; min-width: 100%; max-height: 60vh; overflow-y: auto; margin: 0; padding: 6px;
    list-style: none; background: #161a22; border: 1px solid #ffffff1f; border-radius: 12px; z-index: 20; box-shadow: 0 12px 32px #0009;
  }
  li button {
    width: 100%; text-align: left; background: none; border: 0; border-radius: 8px; padding: 7px 10px;
    font-size: 13px; color: var(--muted-strong); cursor: pointer; white-space: nowrap;
  }
  li button:hover { background: #ffffff10; color: var(--text); }
  li[aria-selected='true'] button { color: var(--accent); }
</style>
