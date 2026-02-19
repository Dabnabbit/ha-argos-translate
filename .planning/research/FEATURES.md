# Features Research

**Domain:** Local translation integration for Home Assistant
**Researched:** 2026-02-19
**Confidence:** HIGH (feature scoping), MEDIUM (competitive landscape — based on training data)

## Competitive Landscape

### Existing HA Translation Options

| Solution | Type | Local? | HA Integration? | Notes |
|----------|------|--------|-----------------|-------|
| Google Translate | Cloud service | NO | Yes (official) | Requires API key, costs money, sends data to Google |
| DeepL | Cloud service | NO | Community integration | Better quality but cloud-dependent, paid API |
| Lingva Translate | Self-hosted frontend | YES | No | Frontend-only, proxies to Google Translate |
| LibreTranslate | Self-hosted API | YES | **No existing integration** | Full local translation, Argos Translate engine |
| Whisper (STT) | Self-hosted | YES | Yes (official) | Speech-to-text only, not translation |
| Piper (TTS) | Self-hosted | YES | Yes (official) | Text-to-speech only, not translation |

**Key finding:** There is NO existing HA integration for local text translation. Whisper and Piper handle speech but not translation. This is a genuine ecosystem gap.

**Confidence:** MEDIUM — searched training data for HA integrations. There may be obscure community integrations not in my training data.

### LibreTranslate Ecosystem

LibreTranslate is the dominant self-hosted translation solution:
- Docker image: `libretranslate/libretranslate`
- Engine: Argos Translate (CTranslate2 backend)
- Languages: ~30+ language pairs depending on installed packages
- API: Simple REST (GET /languages, POST /translate, POST /detect)
- License: AGPL-3.0
- Active development: Yes, regular releases

## Feature Analysis

### Must-Have (v1) Features

#### 1. Config Flow with Connection Validation
**Priority:** P0 — Without this, nothing works
**Complexity:** Low
**Details:**
- Fields: Host, Port, API Key (optional — LibreTranslate can run with or without API keys)
- Validation: GET /languages — if it returns 200 with a non-empty array, connection is valid
- The API key field should be optional since many self-hosted instances don't require one
- Store as config entry with `runtime_data` pattern

#### 2. DataUpdateCoordinator Polling Languages
**Priority:** P0 — Feeds sensors and card
**Complexity:** Low
**Details:**
- Poll GET /languages every 300 seconds (5 minutes)
- Parse response into language list: `[{code: "en", name: "English", targets: ["es", "ja", ...]}, ...]`
- Derive server status: if poll succeeds → online, if fails → error
- Language count = len(languages)
- Language pair availability for validation

#### 3. Status Sensor
**Priority:** P1 — Server health visibility
**Complexity:** Low
**Details:**
- Binary: "online" / "error" based on coordinator last update success
- Attributes: last_check timestamp, error message if applicable

#### 4. Language Count Sensor
**Priority:** P1 — Library visibility
**Complexity:** Low
**Details:**
- Integer: count of available source languages
- Attributes: language list (codes + names)

#### 5. `argos_translate.translate` Service Call
**Priority:** P0 — Core functionality
**Complexity:** Medium
**Details:**
- Schema: `{text: str, source: str, target: str}`
- Source/target are ISO 639-1 codes (e.g., "en", "es", "ja")
- Validate source/target against coordinator's language list before calling API
- POST /translate with body `{q: text, source: source, target: target}`
- Return `{translated_text: response.translatedText}`
- Use SupportsResponse.ONLY pattern
- Timeout: 30 seconds (translation can be slow on CPU)

#### 6. Lovelace Card with Language Dropdowns
**Priority:** P0 — Primary UI
**Complexity:** Medium-High
**Details:**
- Source language dropdown (populated from coordinator data)
- Target language dropdown (filtered to valid targets for selected source)
- Text input area (textarea, multi-line)
- Output area (read-only, shows translated text)
- Translate button
- Swap button (swap source/target languages)
- Status indicator (online/offline dot + language count)

#### 7. Visual Card Editor
**Priority:** P1 — HACS expectation
**Complexity:** Medium
**Details:**
- Entity selection (for the sensors)
- Default source/target language override
- Card title customization

### Nice-to-Have (v1.x) Features

#### 8. Language Pair Validation
**Priority:** P2
**Details:**
- Not all source→target pairs are available
- LibreTranslate's /languages response includes `targets[]` per language
- Card should disable "Translate" if selected pair isn't available
- Consider pivot translation: en→es when only en→fr and fr→es exist (but complex, defer)

#### 9. Loading State During Translation
**Priority:** P2
**Details:**
- Translation can take 1-5 seconds on CPU hardware
- Show spinner/loading indicator on translate button
- Disable button during translation to prevent double-submit

### Deferred (v2+) Features

| Feature | Why Deferred |
|---------|-------------|
| Auto-detect source language | Adds complexity; LibreTranslate supports it but explicit selection is simpler for v1 |
| Translation history | Needs persistent storage; out of scope for v1 |
| Batch translation | Niche use case; single text translation covers 90% of needs |
| Pivot translation (A→B→C) | Complex routing logic; LibreTranslate handles some internally |
| Speech-to-translate pipeline | Requires Whisper integration; future v3 |
| Language package management | LibreTranslate admin UI handles this |

## Differentiators

### What Makes This Unique

1. **Only local translation for HA** — Fills a genuine gap. Whisper (STT) and Piper (TTS) exist but translation is missing from the local AI triad.

2. **Privacy-first** — No data leaves the network. Important for household translation (personal messages, documents).

3. **No API limits** — Cloud translation services have rate limits and costs. Self-hosted has no limits beyond hardware capacity.

4. **Automation-ready** — `SupportsResponse.ONLY` service call means automations can translate notification text, sensor values, etc.

5. **Simple server dependency** — LibreTranslate is a single Docker container. No complex setup.

### Automation Use Cases

The service call pattern enables powerful automations:
- Translate incoming notification text to household language
- Translate weather descriptions for non-English-speaking household members
- Translate smart home device status messages
- Multi-language TTS announcements (translate → Piper)
- Translate text from OCR/camera integrations

## Scope Assessment

**Current scope is right-sized for v1.** The core translation service + card covers the primary use case. Deferred features are genuine v2 candidates, not hidden v1 requirements.

**One concern:** The card UI complexity is moderate — language dropdowns with dynamic filtering, swap button, translate button, loading states, error display. This is more complex than a simple sensor card but manageable in a single JS file.

## Recommendations

1. **Start with the service call** — it's the core value. Card is secondary (automations work without it).
2. **Validate language pairs** — use the `targets[]` array from /languages to prevent invalid translations.
3. **Set generous timeouts** — QNAP Celeron is slow for ML inference. 30-second timeout minimum.
4. **Optional API key** — many LibreTranslate instances run without auth. Make it optional in config flow.
5. **Consider card size** — the card with dropdowns, textarea, and status is ~500-800 lines of JS. Plan for this in phasing.
