# Requirements: Argos Translate

**Defined:** 2026-02-21
**Core Value:** Users can translate text between languages entirely on their local network — no cloud services, no API limits, no privacy concerns — directly from a HA dashboard card or automation.

## v1.1 Requirements

Requirements for v1.1 Enhancement milestone. Each maps to roadmap phases.

### Stabilize & Deploy

- [ ] **STAB-01**: Integration installs via manual copy to custom_components/ and loads without errors on real HA instance
- [ ] **STAB-02**: Config flow completes successfully against real LibreTranslate server
- [ ] **STAB-03**: All sensors, service calls, and card work correctly on real hardware
- [ ] **STAB-04**: Bugs discovered during manual testing are fixed and tests updated

### Options Flow

- [ ] **OPTS-01**: User can reconfigure host, port, API key, and SSL toggle from the integration's options without removing and re-adding
- [ ] **OPTS-02**: Options flow triggers coordinator reload so changes take effect immediately (no HA restart required)

### Auto-Detect Language

- [ ] **DTCT-01**: User can select "Auto" as source language in the card dropdown
- [ ] **DTCT-02**: Service call accepts `source: "auto"` and returns translated text with detected language info
- [ ] **DTCT-03**: Service response includes `detected_language` code and `detection_confidence` when source was "auto"
- [ ] **DTCT-04**: Card target dropdown shows all available targets when source is "Auto"
- [ ] **DTCT-05**: Card displays detected language label (e.g. "Detected: French (90%)") after auto-translate
- [ ] **DTCT-06**: Card handles case where detected language is not installed (shows user-visible message)

### Card Polish

- [ ] **CPOL-01**: Card shows specific error messages (connection error vs. bad request vs. timeout) instead of generic "Translation failed"
- [ ] **CPOL-02**: Card explains why translate button is disabled (server offline, no text entered, no languages selected)
- [ ] **CPOL-03**: All form controls have ARIA labels for screen reader accessibility
- [ ] **CPOL-04**: Card layout stacks properly on mobile/narrow screens (flex-wrap on language row)

## v2 Requirements

Deferred to future release. Tracked but not in current roadmap.

### Enhanced Features

- **ENHC-01**: Translation history with persistent storage
- **ENHC-02**: Batch translation (multiple texts in one call)
- **ENHC-03**: Copy-to-clipboard button on translated text
- **ENHC-04**: Ctrl+Enter keyboard shortcut to translate

### Integration

- **INTG-01**: Whisper STT → Translate → Piper TTS pipeline documentation
- **INTG-02**: Template sensor examples for translated values

## Out of Scope

| Feature | Reason |
|---------|--------|
| Auto-translate on typing (debounced) | API call per keystroke; no WebSocket streaming; bad UX mid-word |
| HA native form elements (ha-select, ha-textfield) | Underdocumented for card context; API changes between HA releases; CSS vars already provide theming |
| Translation history in card | Lost on reload; requires persistent_storage; deferred to v2 |
| Language package management from HA | Requires LibreTranslate admin API; out of integration scope |
| HACS install validation | Deferred — manual install sufficient for v1.1; formal HACS validation in future |

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| STAB-01 | — | Pending |
| STAB-02 | — | Pending |
| STAB-03 | — | Pending |
| STAB-04 | — | Pending |
| OPTS-01 | — | Pending |
| OPTS-02 | — | Pending |
| DTCT-01 | — | Pending |
| DTCT-02 | — | Pending |
| DTCT-03 | — | Pending |
| DTCT-04 | — | Pending |
| DTCT-05 | — | Pending |
| DTCT-06 | — | Pending |
| CPOL-01 | — | Pending |
| CPOL-02 | — | Pending |
| CPOL-03 | — | Pending |
| CPOL-04 | — | Pending |

**Coverage:**
- v1.1 requirements: 16 total
- Mapped to phases: 0 (pending roadmap)
- Unmapped: 16

---
*Requirements defined: 2026-02-21*
*Last updated: 2026-02-21 after initial definition*
