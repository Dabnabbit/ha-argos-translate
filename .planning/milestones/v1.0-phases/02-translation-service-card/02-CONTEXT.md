# Phase 2: Translation Service + Card - Context

**Gathered:** 2026-02-20
**Status:** Ready for planning

<domain>
## Phase Boundary

Implement the `argos_translate.translate` service call and build a Lovelace translation card. The service accepts text, source, and target language codes, validates against coordinator data, and returns translated text via SupportsResponse.ONLY. The card provides language dropdowns populated from the server, input/output text areas, translate button, swap button, loading indicator, and status display. Visual card editor for configuration.

</domain>

<decisions>
## Implementation Decisions

### Translate service behavior
- Service name: `argos_translate.translate` with schema fields `text` (required string), `source` (required string), `target` (required string)
- Response pattern: `SupportsResponse.ONLY` — always returns `{translated_text: "..."}`, never fire-and-forget
- Language validation: Before calling the API, validate that source language exists in coordinator data AND target is in that source language's `targets` list
- Error messages: Distinct errors for invalid source language, invalid target language, invalid language pair (source exists but target not in its targets list), server unreachable, and timeout
- Service handler must look up coordinator from `hass.config_entries.async_entries(DOMAIN)` and use the first entry's coordinator — single-instance primary use case
- Multi-entry handling: If multiple config entries exist, use the first one (ordered by entry creation). Log a debug message noting which entry is being used.

### Card layout and structure
- Single-column card layout: header area, language selectors row, input textarea, translate button, output textarea
- Language selector row: source dropdown, swap button (centered), target dropdown — all on one horizontal line
- Input textarea: multi-line, placeholder "Enter text to translate...", user-editable
- Output textarea: multi-line, read-only, placeholder shows after translation completes
- Translate button: full-width below input, primary color, shows "Translate" label
- Card uses `ha-card` wrapper with configurable header title
- Minimum card height accommodates both text areas without excessive scrolling

### Language dropdown behavior
- Source dropdown: All languages from coordinator data (language_count sensor attributes)
- Target dropdown: Filtered to valid targets for the currently selected source language
- When source language changes, if current target is invalid for new source, reset target to first available target
- Swap button: exchanges source and target selections; if the reverse pair is not valid, swap anyway and let the target dropdown show closest valid option
- Dropdowns display language name with code in parentheses, e.g., "English (en)", "Japanese (ja)"
- Default selections: Use config editor defaults if set, otherwise first available language pair

### Loading and status indicators
- Loading: Disable translate button and show `ha-spinner` inside the button during translation
- Status indicator: Small dot (green/red) + text in the header area showing server status from binary sensor state
- Language count shown next to status: "Online - 12 languages" or "Offline"
- Status reads from the binary_sensor entity state, language count from sensor entity attributes
- Error display: `ha-alert` component below the output area for translation errors (auto-dismisses on next successful translation)

### Card editor
- Visual editor with fields: entity (binary sensor picker for status), header text, default source language, default target language
- Entity picker filters to `binary_sensor` domain entities from argos_translate
- Header defaults to "Translate"
- Default language fields are optional text inputs (language codes like "en", "ja")

### Claude's Discretion
- Exact CSS styling and spacing values
- Card size hints for grid layout (getCardSize, getGridOptions)
- Whether to add copy-to-clipboard button on output area
- Textarea row counts and resize behavior
- Debounce timing if any auto-translate feature is considered
- How to handle very long text (truncation warning vs. unlimited)

</decisions>

<specifics>
## Specific Ideas

- Card should work well at standard HA dashboard column width (roughly 500px card width)
- Use HA's native CSS custom properties throughout (--primary-color, --primary-text-color, --secondary-text-color, etc.) for theme compatibility
- The swap button is a visual centerpiece between the two dropdowns — an icon button with mdi:swap-horizontal
- Service call from card uses `hass.callService` with `returnResponse: true` (requires HA 2024.1+)
- Keep the card self-contained in one JS file — no build toolchain, no external dependencies
- The existing template card in frontend/argos_translate-card.js will be completely rewritten but keeps the same file name, custom element name, and registration pattern

</specifics>

<deferred>
## Deferred Ideas

- Auto-detect source language via /detect endpoint — v2 feature (ENHC-01)
- Translation history persistence — v2 feature (ENHC-02)
- Copy-to-clipboard button — Claude's discretion (may include if straightforward)
- Character count / rate limiting display — future enhancement

</deferred>

---

*Phase: 02-translation-service-card*
*Context gathered: 2026-02-20*
