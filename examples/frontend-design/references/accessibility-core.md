# Accessibility Core Patterns

Default-loaded reference for universal accessibility patterns that apply to almost every frontend-design brief. Load this alongside `design-tokens.md`.

Scope is intentionally narrow. Component-specific patterns (tabs, autocomplete, data tables, date pickers, carousels) and interruption/notification timing are **out of scope** for this file — add a dedicated reference when a brief actually needs them, rather than preemptively stubbing files that drift out of date.

---

## `prefers-reduced-motion`

> **Status: skeleton — fill in before relying on this section for motion-heavy briefs.**
>
> TODO — cover:
> - Which effects should be cut when `@media (prefers-reduced-motion: reduce)` is active (auto-playing carousels, decorative parallax, long transform/scroll-linked animation chains, camera-like zoom).
> - Which effects are safe to keep (opacity cross-fades ≤ 150ms, focus-state transitions, progress indicators).
> - How to structure the CSS so the reduced variant is the easy-to-reach branch (default-reduced, layer motion on top).
> - How to verify during development (system preference toggles on macOS / iOS / Windows / Android, Chrome DevTools "Emulate CSS media feature").

---

## Icon buttons

Any button whose visible content is *only* an icon needs an accessible name. Without one, screen-reader users hear "button" with no context.

### Rules

- Put an accessible name on the `<button>` itself — via `aria-label`, visually-hidden text, or `aria-labelledby` pointing to a sibling.
- Mark the decorative SVG as `aria-hidden="true"` and `focusable="false"` so it isn't announced or tab-stopped separately.
- A tooltip is **not** a substitute for the accessible name. Tooltips vanish on mobile; accessible names don't.

### Canonical pattern

```html
<!-- Option A: aria-label -->
<button type="button" aria-label="Close dialog">
  <svg aria-hidden="true" focusable="false" viewBox="0 0 24 24">…</svg>
</button>

<!-- Option B: visually-hidden text (more resilient across translation layers) -->
<button type="button">
  <svg aria-hidden="true" focusable="false" viewBox="0 0 24 24">…</svg>
  <span class="visually-hidden">Close dialog</span>
</button>

<style>
  .visually-hidden {
    position: absolute;
    width: 1px; height: 1px;
    padding: 0; margin: -1px;
    overflow: hidden; clip: rect(0,0,0,0);
    white-space: nowrap; border: 0;
  }
</style>
```

### Anti-patterns

- `<div>` or `<span>` with a click handler — not focusable, not announced as a control. Always use `<button>`.
- Icon-only with `title` and nothing else — `title` is unreliable on mobile and hidden from most assistive tech.
- Two accessible names that disagree (e.g. `aria-label="Close"` on a button whose visible text says "Cancel") — screen readers pick one and the user experience diverges from visual.

---

## Skip links

The first focusable element on any page should be a skip link that jumps over repetitive navigation to the main content. Keyboard users land on the skip link; mouse users never see it.

### Rules

- Hide the link visually until focused — but **never** with `display: none` or `visibility: hidden` (both remove it from the focus order).
- On focus, it becomes visible, positioned above everything, and tappable.
- Target must be a real element with a matching `id` that can receive focus. Wrap the main with `tabindex="-1"` if needed so focus actually moves when the link is activated.

### Canonical pattern

```html
<a href="#main" class="skip-link">Skip to main content</a>
…
<main id="main" tabindex="-1">…</main>

<style>
  .skip-link {
    position: absolute;
    left: 8px; top: -40px;
    background: #000; color: #fff;
    padding: 8px 12px;
    z-index: 9999;
    transition: top 120ms ease;
  }
  .skip-link:focus { top: 8px; }
</style>
```

### Anti-patterns

- `display: none` with a `:focus` override — the element was never focusable to begin with, so `:focus` never fires.
- Skip link pointing to a `<section>` with no `tabindex` — most browsers won't actually move focus there when the link is activated.
- One skip link on a page with five independent landmark regions — offer multiple skip links (main, primary nav, footer) when the page structure justifies it.

---

## Modal focus management

When a modal opens, focus must move *into* it, stay trapped while open, and return to the trigger when closed. Background content must be inert — not focusable, not clickable, not announced.

### Rules

1. **On open** — move focus to the first meaningful focusable element inside the modal (the first input, or the close button if the modal is read-only).
2. **Trap focus** — `Tab` from the last focusable element wraps to the first; `Shift+Tab` from the first wraps to the last.
3. **Isolate background** — set `inert` on all siblings of the modal wrapper (blocks clicks, keyboard events, and AT announcements). `aria-hidden="true"` alone is not enough because it doesn't block interaction.
4. **Close triggers** — `Esc` key, close button, and (usually) click on the backdrop all close the modal.
5. **On close** — return focus to the element that opened the modal. Store a reference when you open.

### Canonical shape

```js
let previouslyFocused;
// Track only the siblings we made inert, so we don't clobber nodes
// that were already inert before the modal opened.
let siblingsWeInerted = [];

function openModal(modal) {
  previouslyFocused = document.activeElement;
  siblingsWeInerted = Array
    .from(document.querySelectorAll('body > *:not(.modal-wrapper)'))
    .filter(el => !el.inert);
  siblingsWeInerted.forEach(el => el.inert = true);

  modal.hidden = false;
  const firstFocusable = modal.querySelector(
    '[data-autofocus], button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
  );
  firstFocusable?.focus();
}

function closeModal(modal) {
  modal.hidden = true;
  siblingsWeInerted.forEach(el => el.inert = false);
  siblingsWeInerted = [];
  previouslyFocused?.focus();
}
```

### Anti-patterns

- Modal opens but focus stays on the trigger in the background — keyboard users can't reach the modal without tabbing blindly through the whole page.
- `display: none` with no focus management — content still exists in the tab order briefly, or screen readers announce it as the DOM repaints.
- `Esc` closes the modal but focus goes to `<body>` — users lose their place and have to re-find where they were.
- Scroll-locking via `overflow: hidden` on `<html>` while the background is still focusable. Use `inert` on siblings instead; it handles both problems.
