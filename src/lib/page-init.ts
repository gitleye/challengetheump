/**
 * Run `init` once per page view: on first load and after every ClientRouter
 * navigation. Return a cleanup function to undo timers/observers/listeners;
 * it runs before the next swap.
 *
 * Why this exists: with <ClientRouter /> the document is never reloaded.
 *  - Bundled `<script>` modules execute once per session, so element lookups
 *    and listeners bound at module scope point at DOM that the swap discards.
 *  - Astro skips an `is:inline` script whose text is identical to one it
 *    already ran, so those do not re-run on return visits either.
 * Scripts that touch page DOM should therefore be bundled and wrapped in this.
 *
 * Each <body> is initialised at most once (a swap replaces the body, so a new
 * page view always gets a fresh init). Tracked in a WeakSet rather than as a
 * DOM attribute so the guard can never collide with page selectors such as
 * `[data-count-up]`.
 */
export function initPerPage(init: () => void | (() => void)): void {
  let cleanup: void | (() => void);
  const initialised = new WeakSet<HTMLElement>();

  const run = () => {
    const body = document.body;
    if (!body || initialised.has(body)) return;
    initialised.add(body);
    cleanup = init();
  };

  document.addEventListener('astro:before-swap', () => {
    if (typeof cleanup === 'function') cleanup();
    cleanup = undefined;
  });
  document.addEventListener('astro:page-load', run);
  // The module may execute after `astro:page-load` has already fired.
  run();
}
