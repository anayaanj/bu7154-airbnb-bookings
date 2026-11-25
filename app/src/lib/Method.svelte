<script>
  // "How this was computed": a plain explanation, the calculation, then the facts behind it.
  // rows: [label, value, { hint, code }]. A hint explains the term on hover.
  let { summary, formula, rows = [], source } = $props();
</script>

<details>
  <summary>How this was computed</summary>
  <div class="body">
    {#if summary}<p>{summary}</p>{/if}
    {#if formula}<pre>{formula}</pre>{/if}
    <dl>
      {#each rows as [label, value, options]}
        <dt>
          {#if options?.hint}<button type="button" class="hint" data-hint={options.hint}>{label}</button>{:else}{label}{/if}
        </dt>
        <dd class:code={options?.code}>{#if options?.code}<pre>{value}</pre>{:else}{value}{/if}</dd>
      {/each}
    </dl>
    {#if source}<a href={source.href} target="_blank" rel="noreferrer">{source.label} ↗</a>{/if}
  </div>
</details>

<style>
  details { margin-top: 16px; font-size: 13px; }
  summary { cursor: pointer; width: fit-content; list-style: none; color: var(--muted); font-size: 12px; border-bottom: 1px dotted var(--muted); }
  summary::-webkit-details-marker { display: none; }
  summary:hover, details[open] summary { color: var(--text); }
  .body { margin-top: 14px; padding-top: 14px; border-top: 1px solid #ffffff14; display: grid; gap: 12px; }
  p { color: var(--muted-strong); line-height: 1.5; }
  pre { margin: 0; padding: 8px 10px; background: #ffffff0d; border-radius: 6px; color: var(--text);
        font: 12px/1.5 ui-monospace, 'SF Mono', Menlo, monospace; white-space: pre-wrap; overflow-wrap: anywhere; }
  dl { display: grid; grid-template-columns: max-content 1fr; gap: 8px 20px; margin: 0; }
  dt { color: var(--muted); }
  dd { margin: 0; color: var(--text); font-variant-numeric: tabular-nums; }
  dd.code { grid-column: 1 / -1; }
  dd.code pre { white-space: pre; overflow-x: auto; }
  a { color: var(--accent); text-decoration: none; font-size: 12px; }
  a:hover { text-decoration: underline; }
  .hint { position: relative; cursor: help; background: none; border: 0; border-bottom: 1px dotted var(--muted); padding: 0; color: inherit; text-align: left; }
  .hint::after {
    content: attr(data-hint); position: absolute; left: 0; bottom: calc(100% + 8px); width: 260px; padding: 10px 12px;
    background: #1d212b; border: 1px solid #ffffff24; border-radius: 8px; color: var(--text); font-size: 12px; line-height: 1.45; white-space: normal;
    opacity: 0; pointer-events: none; transition: opacity 0.15s; z-index: 10;
  }
  .hint:hover::after, .hint:focus::after { opacity: 1; }
</style>
