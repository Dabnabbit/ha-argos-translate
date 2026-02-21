# Argos Translate for Home Assistant

Local, privacy-respecting text translation via self-hosted [LibreTranslate](https://github.com/LibreTranslate/LibreTranslate) — no cloud services, no API limits.

[![HACS Default](https://img.shields.io/badge/HACS-Default-blue.svg)](https://github.com/hacs/integration)
[![HA Version](https://img.shields.io/badge/Home%20Assistant-2025.7%2B-blue.svg)](https://www.home-assistant.io/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

## Prerequisites

- **Home Assistant** 2025.7 or newer
- **A running LibreTranslate server** (self-hosted on your network)

The Argos Translate integration connects to your LibreTranslate server — it does not bundle or run the translation engine itself.

### Setting up LibreTranslate

The quickest way to run LibreTranslate:

```bash
docker run -d -p 5000:5000 libretranslate/libretranslate
```

Or with docker-compose:

```yaml
services:
  libretranslate:
    image: libretranslate/libretranslate
    ports:
      - "5000:5000"
    restart: unless-stopped
    environment:
      - LT_LOAD_ONLY=en,es,fr,de
```

Set `LT_LOAD_ONLY` to the language codes you need — loading fewer languages reduces memory usage.

For full configuration options, see the [LibreTranslate documentation](https://github.com/LibreTranslate/LibreTranslate).

## Installation

### Via HACS (Recommended)

1. Open HACS in Home Assistant
2. Go to **Integrations**
3. Click the three-dot menu and select **Custom repositories**
4. Add `https://github.com/Dabentz/ha-argos-translate` with category **Integration**
5. Search for "Argos Translate" and install
6. Restart Home Assistant

### Manual Installation

1. Copy the `custom_components/argos_translate/` directory to your Home Assistant `config/custom_components/` directory
2. Restart Home Assistant

## Configuration

### Adding the Integration

1. Go to **Settings** > **Devices & Services** > **Add Integration**
2. Search for **Argos Translate**
3. Fill in the connection details:
   - **Instance Name**: A friendly name for this server (e.g., "My LibreTranslate")
   - **Host**: IP address or hostname of your LibreTranslate server
   - **Port**: Server port (default: 5000)
   - **Use HTTPS**: Toggle on if your server uses SSL/TLS
   - **API Key**: Leave blank if your server has no authentication; enter the key if it does
4. The integration validates the connection by querying the server's language list

### Error States

- **Cannot connect**: Server unreachable — check host, port, and network connectivity
- **Invalid API key**: Server requires authentication — verify your API key
- **No languages**: Server is reachable but has no language models installed — install models via LibreTranslate admin UI or restart the server with `--load-only` flags

### Reconfiguring

Go to **Settings** > **Devices & Services** > **Argos Translate** > **Configure** to update host, port, SSL, or API key. The integration re-validates the connection when you save changes.

## The Translation Card

### Adding the Card

The card auto-registers as a Lovelace resource when using storage mode. To add it to your dashboard:

1. Open a dashboard in edit mode
2. Click **Add Card**
3. Search for **Argos Translate**
4. Select the card

Or add manually via YAML:

```yaml
type: custom:argos-translate-card
entity: sensor.my_libretranslate_language_count
header: Translate
```

### What You See

- **Top**: Header bar with a status indicator (green dot when online, red dot when offline) and the installed language count
- **Middle**: Source language dropdown on the left, a swap button in the center, and target language dropdown on the right. The target dropdown auto-filters to show only valid targets for the selected source language.
- **Below**: Text input area (multi-line, left side) and translated output area (read-only, right side)
- **Bottom**: Translate button. Disabled when the server is offline, a translation is in progress, or no text has been entered. Shows a loading spinner during translation.

### Card Editor

Access the visual editor from the card's pencil icon:

| Option | Description |
|--------|-------------|
| Entity | Pick the language count sensor entity |
| Header | Custom title text |
| Default Source Language | Pre-select a source language code (e.g., "en") |
| Default Target Language | Pre-select a target language code (e.g., "es") |

## Service: `argos_translate.translate`

Translates text between languages via LibreTranslate. Returns the result as response data (`SupportsResponse.ONLY` — you must use `response_variable` in automations or `return_response: true` in Developer Tools).

### Developer Tools Example

```yaml
service: argos_translate.translate
data:
  text: "Hello, how are you?"
  source: en
  target: es
```

Response:

```json
{"translated_text": "Hola, ¿cómo estás?"}
```

### Service Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `text` | string | Yes | Text to translate |
| `source` | string | Yes | Source language code (e.g., `en`) |
| `target` | string | Yes | Target language code (e.g., `es`) |

### Error Responses

- **Invalid source language code**: `ServiceValidationError` — the source language is not installed on the server
- **Invalid target language**: `ServiceValidationError` — the target language is not available for the selected source
- **Server unreachable**: `HomeAssistantError` — the LibreTranslate server could not be reached during translation

## Automation Examples

### Example 1: Translate a doorbell notification

```yaml
automation:
  - alias: "Translate doorbell notification"
    trigger:
      - platform: state
        entity_id: binary_sensor.front_door
        to: "on"
    action:
      - service: argos_translate.translate
        data:
          text: "Someone is at the front door"
          source: en
          target: es
        response_variable: translation
      - service: notify.mobile_app
        data:
          message: "{{ translation.translated_text }}"
```

### Example 2: Translate weather description and store it

```yaml
automation:
  - alias: "Translate weather description"
    trigger:
      - platform: state
        entity_id: sensor.weather_description
    action:
      - service: argos_translate.translate
        data:
          text: "{{ trigger.to_state.state }}"
          source: en
          target: es
        response_variable: result
      - service: input_text.set_value
        target:
          entity_id: input_text.weather_spanish
        data:
          value: "{{ result.translated_text }}"
```

### Example 3: Translate on button press

```yaml
automation:
  - alias: "Translate input text on demand"
    trigger:
      - platform: state
        entity_id: input_button.translate_now
    action:
      - service: argos_translate.translate
        data:
          text: "{{ states('input_text.source_text') }}"
          source: en
          target: fr
        response_variable: result
      - service: input_text.set_value
        target:
          entity_id: input_text.translated_text
        data:
          value: "{{ result.translated_text }}"
```

## Sensors

### Status (Binary Sensor)

- **Entity**: `binary_sensor.<name>_status`
- **Device class**: connectivity
- **State**: `on` when the server is reachable, `off` when unreachable
- **Updated**: Via coordinator polling every 5 minutes

### Language Count (Sensor)

- **Entity**: `sensor.<name>_language_count` (disabled by default — enable in entity settings)
- **State**: Number of installed source languages
- **Attributes**:
  - `languages` — list of language names
  - `language_codes` — list of language codes
  - `language_targets` — dict mapping each source code to its available target codes
- **Used by**: The translation card, for populating language dropdowns

## Troubleshooting

- **Card not appearing**: Ensure the integration is installed and configured. Try clearing your browser cache. Check that the Lovelace resource `/argos_translate/argos_translate-card.js` is registered under **Settings** > **Dashboards** > **Resources**.
- **"Cannot connect" during setup**: Verify LibreTranslate is running and accessible from your Home Assistant host. Test with `curl http://<host>:5000/languages`.
- **"No languages" error**: Your LibreTranslate server has no language models installed. Restart with language loading enabled or visit the LibreTranslate admin panel.
- **Translation card shows "Offline"**: Check the binary sensor state. The server may be down or the network unreachable.
- **Service call returns error**: Ensure the source and target language codes are valid. Check available languages in the language count sensor attributes.

## License

MIT
