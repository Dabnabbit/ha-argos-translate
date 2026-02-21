# Argos Translate

Local text translation via LibreTranslate for Home Assistant.

[![HACS Default](https://img.shields.io/badge/HACS-Default-blue.svg)](https://github.com/hacs/integration)
[![HA Version](https://img.shields.io/badge/Home%20Assistant-2025.7%2B-blue.svg)](https://www.home-assistant.io/)

## Installation via HACS

1. Open HACS in Home Assistant
2. Go to Integrations
3. Search for "Argos Translate"
4. Install and restart Home Assistant

## Manual Installation

1. Copy `custom_components/argos_translate/` into your HA `config/custom_components/`
2. Restart Home Assistant
3. Add the integration via Settings > Devices & Services > Add Integration

## Card Usage

Add the Lovelace card to your dashboard:

```yaml
type: custom:argos-translate-card
entity: sensor.example
header: "Argos Translate"
```

## Configuration

Configure the integration via Settings > Devices & Services > Add Integration > Argos Translate.

## Links

- [Documentation](https://github.com/Dabentz/ha-argos-translate)
- [Issues](https://github.com/Dabentz/ha-argos-translate/issues)

## License

MIT
