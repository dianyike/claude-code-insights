// Browser-side overlap detector for the frontend-design Editing Pass.
//
// This file is a single arrow function. Pass its entire contents as the
// `function` argument to Playwright MCP's browser_evaluate tool. The function
// runs in the page context and returns a JSON-serializable audit report.
//
// Contract:
//   Input:  none — reads the current document.
//   Output: {
//     viewport: { width, height, scrollY },
//     summary: { contentElementsScanned, flagged },
//     candidates: Candidate[]   // sorted by coverageRatio desc
//   }
//
// A Candidate is a content-bearing element whose bounding rect has sample
// points painted over by another element. Candidates are suspects, not
// verdicts — the Editing Pass still judges "intentional mask vs. bug"
// using the rubric in references/overlap-audit.md. Rule 1 of that rubric
// is a hard floor: any portion of visible content-bearing text occluded
// is a bug, regardless of intent signals.
//
// Key design decisions (why, not what):
//   - 3x3 grid sampling inside each rect. Single-point checks miss partial
//     overlap; full-pixel diffing is too expensive for an in-session audit.
//   - Only the target itself is exempt from being counted as occluder. A
//     descendant can cover the target's own text with an absolute overlay;
//     an ancestor can clip the target via overflow. DOM containment is not
//     a safe proxy for paint order. Related elements count as occluders
//     only when their computed style actually paints (paintsOver).
//   - Content-bearing is a mix of visible text-bearing and interactive
//     controls. Icon-only buttons (aria-label but no visible text) are
//     captured via the button/a selectors, not via a broad [aria-label]
//     catch-all. Use [data-audit="content"] to opt in non-semantic
//     wrappers (span/div carrying price, metadata, etc.).

() => {
  const CONTENT_SELECTORS = [
    // Headings
    'h1', 'h2', 'h3', 'h4', 'h5', 'h6', '[role="heading"]',
    // Block text
    'p', 'li', 'dt', 'dd', 'blockquote', 'figcaption',
    // Metadata / small text
    'label', 'legend', 'time', 'address', 'small',
    // Live regions / status
    '[role="status"]',
    '[aria-live]:not([aria-live="off"])',
    // Interactive (visible label must stay legible)
    'a', 'button',
    'input', 'textarea', 'select',
    '[role="button"]', '[role="link"]',
    // Opt-in for non-semantic wrappers (price, metadata spans)
    '[data-audit="content"]',
  ];

  const MEDIA_TAGS = new Set(['IMG', 'SVG', 'VIDEO', 'CANVAS', 'PICTURE', 'IFRAME']);
  const MIN_AREA = 40;

  const hasText = (el) => {
    if (el.tagName === 'INPUT' || el.tagName === 'TEXTAREA' || el.tagName === 'SELECT') return true;
    if ((el.textContent || '').trim().length > 0) return true;
    const aria = el.getAttribute('aria-label');
    return !!(aria && aria.trim().length > 0);
  };

  const selectorHint = (el) => {
    if (!el) return null;
    const parts = [el.tagName.toLowerCase()];
    if (el.id) parts.push('#' + el.id);
    if (el.className && typeof el.className === 'string') {
      const cls = el.className.trim().split(/\s+/).slice(0, 2).join('.');
      if (cls) parts.push('.' + cls);
    }
    return parts.join('');
  };

  const shortText = (el) => {
    const txt = (el.textContent || el.getAttribute('aria-label') || '').trim();
    return txt.length > 80 ? txt.slice(0, 77) + '…' : txt;
  };

  const samplePoints = (rect) => {
    const pts = [];
    for (let i = 1; i <= 3; i++) {
      for (let j = 1; j <= 3; j++) {
        pts.push({
          x: rect.left + (rect.width * i) / 4,
          y: rect.top + (rect.height * j) / 4,
        });
      }
    }
    return pts;
  };

  const isInert = (el) => {
    if (!el || el === document.documentElement || el === document.body) return true;
    const style = getComputedStyle(el);
    return style.visibility === 'hidden' || style.display === 'none' || style.opacity === '0';
  };

  const paintsOver = (el) => {
    if (MEDIA_TAGS.has(el.tagName)) return true;
    const style = getComputedStyle(el);
    const bg = style.backgroundColor;
    const hasBg = bg && bg !== 'rgba(0, 0, 0, 0)' && bg !== 'transparent';
    const hasImage = style.backgroundImage && style.backgroundImage !== 'none';
    const hasFilter = style.filter && style.filter !== 'none';
    const hasBackdrop = style.backdropFilter && style.backdropFilter !== 'none';
    return !!(hasBg || hasImage || hasFilter || hasBackdrop);
  };

  const auditElement = (target) => {
    const rect = target.getBoundingClientRect();
    if (rect.width * rect.height < MIN_AREA) return null;
    if (rect.bottom < 0 || rect.top > innerHeight) return null;

    const pts = samplePoints(rect);
    const occluders = new Map();
    let covered = 0;

    for (const pt of pts) {
      if (pt.x < 0 || pt.y < 0 || pt.x > innerWidth || pt.y > innerHeight) continue;
      const stack = document.elementsFromPoint(pt.x, pt.y);
      if (!stack || stack.length === 0) continue;

      let occluder = null;
      for (const el of stack) {
        if (!el) continue;
        if (el === target) { occluder = null; break; }
        if (isInert(el)) continue;

        const related = target.contains(el) || el.contains(target);
        if (related) {
          // Ancestors/descendants count only when they actually paint pixels.
          // A plain wrapper or the target's own text span will paintsOver →
          // false, so we continue. An absolute overlay inside the target,
          // or an overflow-clipping ancestor with a real background, will
          // paintsOver → true, so we flag.
          if (!paintsOver(el)) continue;
          occluder = el;
          break;
        }

        if (!paintsOver(el)) continue;
        occluder = el;
        break;
      }

      if (occluder) {
        covered++;
        occluders.set(occluder, (occluders.get(occluder) || 0) + 1);
      }
    }

    if (covered === 0) return null;

    const occluderList = Array.from(occluders.entries())
      .sort((a, b) => b[1] - a[1])
      .slice(0, 3)
      .map(([el, count]) => ({
        selector: selectorHint(el),
        tag: el.tagName.toLowerCase(),
        role: el.getAttribute('role') || null,
        coveredSamples: count,
      }));

    return {
      target: {
        selector: selectorHint(target),
        tag: target.tagName.toLowerCase(),
        text: shortText(target),
        rect: {
          x: Math.round(rect.x),
          y: Math.round(rect.y),
          w: Math.round(rect.width),
          h: Math.round(rect.height),
        },
      },
      coveredSamples: covered,
      totalSamples: pts.length,
      coverageRatio: Number((covered / pts.length).toFixed(2)),
      occluders: occluderList,
    };
  };

  const seen = new Set();
  const candidates = [];

  for (const sel of CONTENT_SELECTORS) {
    for (const el of document.querySelectorAll(sel)) {
      if (seen.has(el)) continue;
      seen.add(el);
      if (!hasText(el)) continue;
      const result = auditElement(el);
      if (result) candidates.push(result);
    }
  }

  candidates.sort((a, b) => b.coverageRatio - a.coverageRatio);

  return {
    viewport: { width: innerWidth, height: innerHeight, scrollY: window.scrollY },
    summary: {
      contentElementsScanned: seen.size,
      flagged: candidates.length,
    },
    candidates,
  };
}
