---
status: investigating
trigger: "container-query-still-not-firing"
created: 2026-02-22T00:00:00Z
updated: 2026-02-22T00:00:00Z
---

## Current Focus

hypothesis: Initial evidence gathering — reading card JS structure to understand container query setup
test: Examine DOM hierarchy: :host > ha-card > .card-content and how container-type interacts with ha-card shadow DOM
expecting: Find structural reason why @container argos-card query on .card-content doesn't fire
next_action: Analyze ha-card element behavior — does ha-card have its own shadow DOM that intercepts sizing?

## Symptoms

expected: Input and output textareas display side-by-side at >= 580px card width via @container argos-card (min-width: 580px) query
actual: Textareas always stack vertically in auto mode. Language selectors respond to width. Manual Horizontal/Vertical override works correctly.
errors: None — no console errors reported
reproduction: Place card in wide dashboard column (>= 580px), observe layout stays vertical
started: After 05-04 moved container-type from :host to .card-content

## Eliminated

(none yet)

## Evidence

- timestamp: 2026-02-22T00:01:00Z
  checked: argos_translate-card.js static get styles()
  found: container-type:inline-size and container-name:argos-card are set on .card-content (lines 503-504). @container argos-card (min-width: 580px) targets .content-area (line 584).
  implication: The container and query are in the same shadow root — no cross-shadow boundary issue here

- timestamp: 2026-02-22T00:02:00Z
  checked: render() method, ha-card usage
  found: .card-content is a direct child of <ha-card>. ha-card is a custom element defined by HA — it has its OWN shadow DOM.
  implication: CRITICAL — ha-card renders its slot content inside its own shadow DOM. The .card-content div lives in ha-card's shadow DOM slot, NOT in ArgosTranslateCard's shadow root. CSS styles from ArgosTranslateCard's static get styles() are scoped to ArgosTranslateCard's shadow root and CANNOT style elements that are projected into ha-card's shadow slot.

- timestamp: 2026-02-22T00:03:00Z
  checked: How LitElement styles work with slotted content
  found: Styles defined in static get styles() are injected into the component's shadow root via <style> tag in the shadow DOM. They apply to elements rendered in that shadow root's render tree.
  implication: .card-content IS rendered in ArgosTranslateCard's shadow root (it's part of the render() template). The container-type declaration should be visible to the CSS engine for that element. BUT — ha-card wraps content in its own shadow DOM structure. The .card-content is slotted INTO ha-card's shadow, meaning ha-card's shadow root is the containing block.

- timestamp: 2026-02-22T00:04:00Z
  checked: CSS @container query mechanism
  found: @container queries find the nearest ancestor with a matching container-name. The .content-area is a child of .card-content. Both live in ArgosTranslateCard's shadow root. The @container rule is also in ArgosTranslateCard's shadow root. This should work — same shadow root.
  implication: The container and the queried element are in the same shadow root. The @container rule in the same shadow root should see .card-content as the container. Shadow DOM does NOT block container queries between elements in the SAME shadow root.

- timestamp: 2026-02-22T00:05:00Z
  checked: ha-card display/sizing behavior — does it constrain .card-content width?
  found: ha-card style says overflow:hidden, height:100%, display:flex, flex-direction:column. .card-content has flex:1 and overflow:auto.
  implication: ha-card is given display:flex. .card-content is flex:1 meaning it grows to fill ha-card. The INLINE SIZE of .card-content used by container-type:inline-size comes from ha-card's internal layout. Since ha-card uses its shadow DOM slot mechanism, the actual rendered width of .card-content depends on ha-card's slot container width.

- timestamp: 2026-02-22T00:06:00Z
  checked: overflow:auto on .card-content
  found: .card-content has overflow:auto set (line 503)
  implication: CRITICAL FINDING — overflow:auto establishes a new block formatting context. More importantly, when an element has overflow other than visible, it can affect the containment model. BUT the real issue: overflow:auto on a container-type:inline-size element means the container's size is determined by its own content unless constrained by its parent. If .card-content can scroll, its inline-size may be reported as the CONTENT size (which adjusts to content), not the visual width.

## Resolution

root_cause: (pending confirmation)
fix: (empty)
verification: (empty)
files_changed: []
