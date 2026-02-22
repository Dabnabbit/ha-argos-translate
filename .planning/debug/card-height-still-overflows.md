---
status: investigating
trigger: "card-height-still-overflows"
created: 2026-02-22T00:00:00Z
updated: 2026-02-22T00:10:00Z
---

## Current Focus

hypothesis: CONFIRMED — two separate problems: (1) only one textarea is rendering (no output panel visible), which means resize:none on textarea is not enough — the textarea with rows="4" has a visible drag handle in screenshot, meaning an older card version is still deployed; (2) the card outer container does NOT constrain to its grid slot height because :host has no height:100% and ha-card height:100% only fills the :host, not the grid slot.
test: Root cause is confirmed via screenshot analysis
expecting: N/A — confirmed
next_action: Return diagnosis

## Symptoms

expected: Card fits its content area without extending into the "new section" territory below the card
actual: Card definitely does not fit, might be worse than before
errors: None
reproduction: View card on dashboard, observe it extends below its content area
started: After 05-04 reduced grid rows from 7 to 5

## Eliminated

- hypothesis: "rows:5 in getGridOptions is causing the card to render at exactly 5 rows of height, and content overflows that"
  evidence: Screenshot shows the card visual boundary (card outline/border) actually extends PAST the grid slot into New section territory — it's the card container itself that is too tall, not content overflowing inside the card. The card outer box is taller than its allocated slot.
  timestamp: 2026-02-22T00:08:00Z

## Evidence

- timestamp: 2026-02-22T00:01:00Z
  checked: argos_translate-card.js getCardSize() and getGridOptions()
  found: getCardSize returns 5; getGridOptions returns rows:5, columns:12, min_rows:4, min_columns:4
  implication: These tell HA how many grid slots to allocate. In the sections view, each row is approximately 56px. 5 rows = ~280px slot height.

- timestamp: 2026-02-22T00:02:00Z
  checked: ha-card CSS in static get styles()
  found: ha-card { height: 100%; overflow: hidden; display: flex; flex-direction: column; }
  implication: ha-card fills 100% of its parent (:host). If :host is not constrained, ha-card is not constrained.

- timestamp: 2026-02-22T00:03:00Z
  checked: :host CSS rule
  found: :host { display: block; } — no height constraint set on :host
  implication: :host is block with no height — it expands to its natural content height. This is the core problem. The HA sections grid gives the slot a fixed height, but :host is not told to respect that height.

- timestamp: 2026-02-22T00:04:00Z
  checked: card content elements natural height (textarea rows="4")
  found: Two textareas each with rows="4". Natural height per textarea ~78-85px. Status bar ~30px, lang-row ~42px, translate-btn ~42px, hint ~20px, gaps/padding ~60px. Total content ~350-400px. Plus ha-card header ~48px. Total natural height ~400-450px.
  implication: Natural height far exceeds 5-row slot (~280px). The card overflows by ~120-170px.

- timestamp: 2026-02-22T00:05:00Z
  checked: Screenshot 2026-02-21 201154.png (dashboard view)
  found: Card visual boundary (dashed outline) visibly extends into the "New section" row below the card. The card shows: "Translate" header, status dot "Online - 22 languages", language dropdowns, ONE textarea (input only — output not visible), Translate button, and then BELOW the Translate button the card boundary overlaps with "New section" + its dashed add-box. The output textarea panel appears BELOW the translate button and below the "New section" label.
  implication: The card visual container extends past its grid slot. The output textarea is rendering OUTSIDE the card's grid allocation. This confirms :host height is not constrained to the grid slot.

- timestamp: 2026-02-22T00:06:00Z
  checked: Screenshot also shows textarea drag handle (resize indicator) visible in bottom-right of input textarea
  found: The input textarea shows a resize drag handle despite resize:none in CSS
  implication: This suggests the deployed card may be v0.5.0 or earlier (before resize:none was added), OR the resize:none is not being applied (CSS specificity issue). However, the card JS console.info shows v0.5.1 — so likely the browser has a cached older version OR there is a CSS specificity issue with resize:none being overridden by HA global styles. HOWEVER — this is a secondary finding; the primary overflow issue is the :host height constraint problem.

- timestamp: 2026-02-22T00:07:00Z
  checked: How HA sections grid constrains card height
  found: In HA sections view, the grid gives each card a fixed grid area. The custom element (:host) must use height:100% to fill and be constrained to that area. Without height:100% on :host, the element grows to its natural content height and visually overflows its grid cell.
  implication: The fix is to add height:100% to :host CSS. This constrains :host to the grid slot. ha-card already has height:100% (fills :host), and .card-content already has flex:1 and overflow:auto (scrolls internally). So the chain height:100% on :host → ha-card height:100% → .card-content flex:1 overflow:auto will properly contain the card.

- timestamp: 2026-02-22T00:08:00Z
  checked: Why reducing rows:7 to rows:5 made it worse
  found: Reducing rows shrank the GRID SLOT from ~392px to ~280px. But :host has no height constraint, so the card renders at its natural ~400-450px regardless. The gap between grid slot and natural content height INCREASED from ~8-58px to ~120-170px. The card was already overflowing with 7 rows; it's more visible now with 5.
  implication: The rows number is irrelevant to the overflow as long as :host has no height:100% constraint. The rows number only matters for how much space the dashboard allocates — the card will render beyond it either way.

## Resolution

root_cause: |
  The :host element has only `display: block` with no height constraint. In HA sections grid view,
  each card is given a fixed grid slot (rows * row_height pixels). The card must have `height: 100%`
  on :host to be constrained to that slot. Without it, :host expands to its natural content height
  (~400-450px for two 4-row textareas + all UI elements), which exceeds any grid slot allocation.

  The CSS chain that SHOULD work:
    :host { display: block; height: 100%; }  <- MISSING height:100%
    ha-card { height: 100%; ... }            <- already present
    .card-content { flex: 1; overflow: auto; } <- already present

  Because :host lacks height:100%, the entire card renders at natural height and overflows the
  grid slot boundary into the "New section" area below.

  Reducing rows from 7 to 5 in getGridOptions made the overflow WORSE: it shrank the allocated
  slot without shrinking the card's rendered height.

  Secondary finding: The screenshot also shows a textarea resize handle, suggesting resize:none
  may not be applying (CSS specificity — browser UA stylesheet for textarea has higher specificity
  than :host-scoped rules in some cases). This is a separate, minor issue.

fix: (empty until applied)
verification: (empty until verified)
files_changed: []
