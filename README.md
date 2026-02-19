# Argos Translate

A Home Assistant HACS integration for local text translation using [LibreTranslate](https://libretranslate.com/) / [Argos Translate](https://github.com/argosopentech/argos-translate). All translations happen on your local network - no cloud services needed.

## Features

- Translate text between 15+ languages via a local LibreTranslate server
- `argos_translate.translate` service call for automations and scripts
- Status and language count sensors
- Lovelace card with language dropdowns, swap button, and translate functionality
- Visual card editor

## Installation

### HACS (Recommended)

1. Add this repository as a custom repository in HACS
2. Search for "Argos Translate" and install
3. Restart Home Assistant
4. Add the integration via Settings > Devices & Services

### Manual

1. Copy `custom_components/argos_translate/` to your HA `config/custom_components/`
2. Restart Home Assistant
3. Add the integration via Settings > Devices & Services

## Prerequisites

You need a running LibreTranslate server. The easiest way:

```bash
docker run -d -p 5000:5000 libretranslate/libretranslate
```

## Configuration

The config flow asks for:

- **Host**: LibreTranslate server hostname/IP (default: `localhost`)
- **Port**: Server port (default: `5000`)
- **API Key**: Optional, if your server requires authentication

## Service

### `argos_translate.translate`

Translate text between languages. Returns response data.

| Parameter | Description | Example |
|-----------|-------------|---------|
| `text` | Text to translate | `"Hello world"` |
| `source` | Source language code | `"en"` |
| `target` | Target language code | `"es"` |

**Response:**
```yaml
translated_text: "Hola mundo"
```

## Sensors

| Sensor | Description |
|--------|-------------|
| `sensor.argos_translate_*_status` | Server status (online/error) |
| `sensor.argos_translate_*_available_languages` | Number of available languages |

## Card

The Argos Translate card provides:

- **Language dropdowns**: Select source and target languages
- **Swap button**: Quickly reverse the translation direction
- **Input area**: Enter text to translate
- **Translate button**: Trigger translation via the service call
- **Output area**: Read-only translated result
- **Status bar**: Server status and language count

## License

MIT
