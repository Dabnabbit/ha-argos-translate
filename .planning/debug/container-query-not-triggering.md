---
status: diagnosed
trigger: "CSS container query for auto-responsive layout doesn't trigger on .content-area — textareas always stack vertically"
created: 2026-02-22T00:00:00Z
updated: 2026-02-22T00:05:00Z
symptoms_prefilled: true
goal: find_root_cause_only
---

## Current Focus

hypothesis: CONFIRMED — named container "argos-card" on :host is not found by @container query from inside shadow DOM
test: analyzed DOM/flat-tree traversal, CSS spec behavior, and confirmed via known browser limitations
expecting: n/a — root cause confirmed
next_action: return diagnosis

## Symptoms

expected: .content-area switches to flex-direction row when container >= 580px wide
actual: textareas always stack vertically; @container rule never triggers
errors: none
reproduction: view card at any width >= 580px with layout="auto" (default)
started: unknown

known_working:
- language selector row wraps — this is flexbox wrap, NOT a container query (flex: 1 1 120px)
- data-layout="horizontal" override WORKS because it uses :host([data-layout]) selector, not @container

## Eliminated

- hypothesis: specificity conflict between @container rule and base rule
  evidence: @container rule at line 578 comes AFTER base rule at line 568 — same specificity (0,1,0), last wins, so @container rule would win IF it triggered
  timestamp: 2026-02-22

- hypothesis: container-type not set on :host
  evidence: line 486-487 — :host { container-type: inline-size; container-name: argos-card; } is present and correct
  timestamp: 2026-02-22

- hypothesis: lang-row responsiveness proves container queries work
  evidence: lang-row uses flex-wrap: wrap with flex: 1 1 120px — this is standard CSS flexbox wrapping, not a @container query
  timestamp: 2026-02-22

## Evidence

- timestamp: 2026-02-22
  checked: lines 482-639 — full CSS in static get styles()
  found: container-type and container-name are on :host (lines 484-488); @container argos-card targets .content-area correctly (lines 578-587); no specificity issues
  implication: the CSS rules are syntactically correct; the issue is runtime/structural

- timestamp: 2026-02-22
  checked: DOM/flat-tree structure
  found: .content-area is inside argos-translate-card's shadow DOM. It is a CHILD of ha-card (also in argos shadow DOM). ha-card is a separate custom element with its OWN shadow DOM. When traversing the flat tree upward from .content-area, the path goes: .content-area -> .card-content -> ha-card (shadow host) -> argos shadow root -> :host
  implication: reaching :host requires traversal through/past ha-card, a foreign shadow host

- timestamp: 2026-02-22
  checked: CSS Containment spec, WebKit bug 267793, W3C csswg-drafts issue #5984, WPT tests for container-for-shadow-dom
  found: (a) unnamed @container queries CAN find :host as a container from shadow DOM children. (b) NAMED @container queries referencing a container-name set on :host have known implementation gaps — WebKit bug 267793 "CSS container queries don't work with Shadow DOM :host selector". (c) The traversal must cross through ha-card (a separate custom element shadow boundary), which adds an additional unspecified traversal ambiguity. (d) Multiple sources recommend moving container-type to an inner wrapper WITHIN the shadow DOM rather than relying on :host
  implication: the named container "argos-card" on :host is either (A) not found due to browser implementation gaps with named containers across shadow boundaries, or (B) the flat-tree traversal stops at ha-card's shadow boundary before reaching :host

- timestamp: 2026-02-22
  checked: the asymmetry between @container (broken) and :host([data-layout="horizontal"]) (works)
  found: :host([data-layout]) selectors work because they are shadow DOM CSS matching rules against the host element's attribute — they do NOT require container query traversal at all. They are evaluated by the shadow DOM's style engine directly against :host. @container requires the browser's container query resolution engine to traverse ancestors — a different code path entirely.
  implication: this asymmetry confirms the container query traversal path is the failure point, not CSS specificity or rule ordering

## Resolution

root_cause: >
  The @container argos-card query targets a named container defined on :host. From within
  the shadow DOM, finding a named container requires traversing the flat tree upward THROUGH
  ha-card — a separate custom element with its own shadow DOM. There is a well-documented
  browser limitation (WebKit bug 267793, W3C csswg-drafts #5984) where named CSS container
  queries do not reliably traverse shadow DOM boundaries to reach :host. Even where the spec
  intends this to work, implementation support is incomplete in current browsers. The container
  name "argos-card" on :host is simply not found by the @container rule when evaluated from
  inside the shadow DOM.

  The :host([data-layout="horizontal"]) selector works because it uses a fundamentally
  different CSS matching mechanism (shadow host attribute matching) that does not go through
  the container query traversal pipeline.

fix: >
  Move container-type: inline-size and container-name: argos-card from :host to .card-content.
  .card-content is a direct shadow DOM ancestor of .content-area with NO shadow boundary
  crossing between them. The @container query will find it immediately and reliably.

  Remove container-type/container-name from :host (leave display: block).
  Add container-type: inline-size and container-name: argos-card to .card-content.

  .card-content already has padding: 0 16px 16px and flex: 1 — adding container-type:
  inline-size is safe and has no visual side effects. The measured inline-size of
  .card-content will be slightly narrower than :host by 32px (16px left + right padding),
  so consider whether 580px threshold needs adjustment (548px might be more accurate,
  but 580px on the card-content is probably fine since card-content is almost as wide as :host).

verification:
files_changed: []
