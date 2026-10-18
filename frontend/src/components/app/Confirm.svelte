<script lang="ts">
  let {
    open = $bindable(false),
    title,
    body,
    confirmLabel = 'Delete',
    onconfirm,
  }: { open?: boolean; title: string; body: string; confirmLabel?: string; onconfirm: () => void } = $props()

  let dialog: HTMLDialogElement

  $effect(() => {
    if (open && !dialog.open) dialog.showModal()
    else if (!open && dialog.open) dialog.close()
  })
</script>

<dialog bind:this={dialog} onclose={() => (open = false)} onclick={(e) => e.target === dialog && dialog.close()} aria-labelledby="confirm-title">
  <div class="inner">
    <p class="label eyebrow">Confirm</p>
    <h2 id="confirm-title" class="h3">{title}</h2>
    <p class="muted">{body}</p>
    <div class="row">
      <button class="btn btn-ghost btn-sm" onclick={() => dialog.close()}>Cancel</button>
      <button
        class="btn btn-primary btn-sm"
        onclick={() => {
          dialog.close()
          onconfirm()
        }}>{confirmLabel}</button
      >
    </div>
  </div>
</dialog>

<style>
  dialog {
    margin: auto;
    padding: 0;
    border: 1px solid var(--ink);
    background: var(--surface);
    color: var(--ink);
    box-shadow: var(--shadow-hard);
    width: min(440px, calc(100vw - 32px));
  }
  dialog[open] {
    animation: pop var(--t-med) var(--ease);
  }
  @keyframes pop {
    from {
      opacity: 0;
      transform: translateY(8px);
    }
  }
  dialog::backdrop {
    background: rgb(18 17 15 / 0.45);
  }
  .inner {
    padding: 22px;
    display: grid;
    gap: 12px;
  }
  .muted {
    font-size: var(--fs-sm);
  }
  .row {
    display: flex;
    justify-content: flex-end;
    gap: 8px;
    margin-top: 8px;
  }
</style>
