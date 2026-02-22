/**
 * Argos Translate Card
 *
 * A Lovelace card for translating text via LibreTranslate.
 * Provides language dropdowns, text input/output, and a translate button.
 */

const LitElement = customElements.get("hui-masonry-view")
  ? Object.getPrototypeOf(customElements.get("hui-masonry-view"))
  : Object.getPrototypeOf(customElements.get("hui-view"));
const html = LitElement.prototype.html;
const css = LitElement.prototype.css;

const CARD_VERSION = "0.3.0";

console.info(
  `%c ARGOS-TRANSLATE-CARD %c v${CARD_VERSION} `,
  "color: orange; font-weight: bold; background: black",
  "color: white; font-weight: bold; background: dimgray"
);

class ArgosTranslateCard extends LitElement {
  static get properties() {
    return {
      hass: { type: Object },
      config: { type: Object },
      _source: { type: String },
      _target: { type: String },
      _inputText: { type: String },
      _outputText: { type: String },
      _loading: { type: Boolean },
      _error: { type: String },
    };
  }

  constructor() {
    super();
    this._source = "";
    this._target = "";
    this._inputText = "";
    this._outputText = "";
    this._loading = false;
    this._error = null;
  }

  static getConfigElement() {
    return document.createElement("argos-translate-card-editor");
  }

  static getStubConfig(hass) {
    if (!hass) {
      return {
        header: "Translate",
        entity: "",
        language_entity: "",
      };
    }
    const entities = Object.keys(hass.states);
    const statusEntity = entities.find((e) =>
      e.startsWith("binary_sensor.") && (e.includes("libretranslate") || e.includes("argos_translate"))
    );
    const langEntity = entities.find((e) =>
      e.startsWith("sensor.") && (e.includes("libretranslate") || e.includes("argos_translate"))
    );
    return {
      header: "Translate",
      entity: statusEntity || "",
      language_entity: langEntity || "",
    };
  }

  setConfig(config) {
    if (!config) {
      throw new Error("Invalid configuration");
    }
    this.config = {
      header: "Translate",
      ...config,
    };
  }

  getCardSize() {
    return 5;
  }

  getGridOptions() {
    return {
      rows: 5,
      columns: 6,
      min_rows: 4,
      min_columns: 3,
    };
  }

  _getLanguages() {
    const langEntity = this.config.language_entity;
    const langState = this.hass && this.hass.states && this.hass.states[langEntity];
    if (!langState || !langState.attributes) {
      return { names: [], codes: [], targets: {} };
    }
    return {
      names: langState.attributes.languages || [],
      codes: langState.attributes.language_codes || [],
      targets: langState.attributes.language_targets || {},
    };
  }

  _getTargetsForSource(sourceCode) {
    const { targets } = this._getLanguages();
    return targets[sourceCode] || [];
  }

  _getStatus() {
    const stateObj = this.hass && this.hass.states && this.hass.states[this.config.entity];
    if (!stateObj) {
      return { online: false, available: false };
    }
    return {
      online: stateObj.state === "on",
      available: true,
    };
  }

  updated(changedProperties) {
    super.updated(changedProperties);
    if (changedProperties.has("hass") || changedProperties.has("config")) {
      const { codes } = this._getLanguages();
      if (codes.length > 0 && !this._source) {
        this._source =
          (this.config && this.config.default_source && codes.includes(this.config.default_source)
            ? this.config.default_source
            : codes[0]);
        const validTargets = this._getTargetsForSource(this._source);
        this._target =
          (this.config && this.config.default_target && validTargets.includes(this.config.default_target)
            ? this.config.default_target
            : validTargets[0] || "");
      }
    }
  }

  _sourceChanged(ev) {
    this._source = ev.target.value;
    const validTargets = this._getTargetsForSource(this._source);
    if (!validTargets.includes(this._target)) {
      this._target = validTargets[0] || "";
    }
    this.requestUpdate();
  }

  _targetChanged(ev) {
    this._target = ev.target.value;
    this.requestUpdate();
  }

  _inputChanged(ev) {
    this._inputText = ev.target.value;
  }

  _swapLanguages() {
    const oldSource = this._source;
    const oldTarget = this._target;
    this._source = oldTarget;
    this._target = oldSource;

    // Check if new combination is valid
    const validTargets = this._getTargetsForSource(this._source);
    if (!validTargets.includes(this._target)) {
      this._target = validTargets[0] || "";
    }

    // Move output to input for convenient back-translation
    if (this._outputText) {
      this._inputText = this._outputText;
      this._outputText = "";
    }

    this.requestUpdate();
  }

  async _translate() {
    if (!this._inputText || !this._source || !this._target) return;

    this._loading = true;
    this._error = null;

    try {
      const result = await this.hass.callService(
        "argos_translate",
        "translate",
        {
          text: this._inputText,
          source: this._source,
          target: this._target,
        },
        {},
        true,
        true
      );
      this._outputText = result.response.translated_text;
    } catch (err) {
      this._error = (err && err.message) || "Translation failed";
    } finally {
      this._loading = false;
    }
  }

  render() {
    if (!this.hass || !this.config) {
      return html`
        <ha-card>
          <div class="card-content loading">
            <ha-spinner size="small"></ha-spinner>
          </div>
        </ha-card>
      `;
    }

    if (!this.config.entity && !this.config.language_entity) {
      return html`
        <ha-card header="${this.config.header || ""}">
          <div class="card-content">
            <div class="empty">No entities configured. Open the card editor to set up.</div>
          </div>
        </ha-card>
      `;
    }

    const status = this._getStatus();
    const { names, codes } = this._getLanguages();
    const validTargets = this._getTargetsForSource(this._source);

    // Build status text
    let statusDotClass = "status-dot";
    let statusText = "";
    if (!status.available) {
      statusDotClass += " unavailable";
      statusText = "Unavailable";
    } else if (status.online) {
      statusDotClass += " online";
      statusText = `Online - ${codes.length} languages`;
    } else {
      statusDotClass += " offline";
      statusText = "Offline";
    }

    const canTranslate =
      !this._loading &&
      this._inputText &&
      this._source &&
      this._target &&
      status.online;

    return html`
      <ha-card header="${this.config.header || ""}">
        <div class="card-content">
          <div class="status-bar">
            <span class="${statusDotClass}"></span>
            <span>${statusText}</span>
          </div>

          <div class="lang-row">
            <select
              .value="${this._source}"
              @change="${this._sourceChanged}"
            >
              ${codes.map(
                (code, i) => html`
                  <option value="${code}" ?selected="${code === this._source}">
                    ${names[i]} (${code})
                  </option>
                `
              )}
            </select>

            <ha-icon-button
              .path="${"M21,9L17,5V8H10V10H17V13M7,11L3,15L7,19V16H14V14H7V11Z"}"
              @click="${this._swapLanguages}"
              title="Swap languages"
            ></ha-icon-button>

            <select
              .value="${this._target}"
              @change="${this._targetChanged}"
            >
              ${validTargets.map((targetCode) => {
                const idx = codes.indexOf(targetCode);
                const targetName = idx >= 0 ? names[idx] : targetCode;
                return html`
                  <option value="${targetCode}" ?selected="${targetCode === this._target}">
                    ${targetName} (${targetCode})
                  </option>
                `;
              })}
            </select>
          </div>

          <textarea
            rows="4"
            placeholder="Enter text to translate..."
            .value="${this._inputText}"
            @input="${this._inputChanged}"
          ></textarea>

          <button
            class="translate-btn"
            @click="${this._translate}"
            ?disabled="${!canTranslate}"
          >
            ${this._loading
              ? html`<ha-spinner size="small"></ha-spinner> Translating...`
              : "Translate"}
          </button>

          <textarea
            rows="4"
            readonly
            placeholder=""
            .value="${this._outputText}"
          ></textarea>

          ${this._error
            ? html`<ha-alert alert-type="error">${this._error}</ha-alert>`
            : ""}
        </div>
      </ha-card>
    `;
  }

  static get styles() {
    return css`
      :host {
        display: block;
      }
      .card-content {
        padding: 0 16px 16px;
      }
      .loading {
        display: flex;
        justify-content: center;
        align-items: center;
        padding: 32px 16px;
      }
      .empty {
        color: var(--secondary-text-color);
        font-style: italic;
        text-align: center;
        padding: 16px;
      }
      .status-bar {
        display: flex;
        align-items: center;
        gap: 8px;
        padding: 4px 0 12px;
        font-size: 0.85em;
        color: var(--secondary-text-color);
      }
      .status-dot {
        width: 8px;
        height: 8px;
        border-radius: 50%;
        display: inline-block;
        flex-shrink: 0;
      }
      .status-dot.online {
        background-color: var(--success-color, #4caf50);
      }
      .status-dot.offline {
        background-color: var(--error-color, #f44336);
      }
      .status-dot.unavailable {
        background-color: var(--disabled-color, #bdbdbd);
      }
      .lang-row {
        display: flex;
        align-items: center;
        gap: 8px;
        margin-bottom: 12px;
      }
      .lang-row select {
        flex: 1;
        padding: 8px;
        border: 1px solid var(--divider-color, #e0e0e0);
        border-radius: 4px;
        background: var(--card-background-color, #fff);
        color: var(--primary-text-color);
        font-size: 14px;
        min-width: 0;
      }
      textarea {
        width: 100%;
        box-sizing: border-box;
        padding: 8px;
        border: 1px solid var(--divider-color, #e0e0e0);
        border-radius: 4px;
        background: var(--card-background-color, #fff);
        color: var(--primary-text-color);
        font-family: inherit;
        font-size: 14px;
        resize: vertical;
      }
      textarea[readonly] {
        background: var(--secondary-background-color, #f5f5f5);
      }
      .translate-btn {
        width: 100%;
        padding: 10px;
        margin: 12px 0;
        border: none;
        border-radius: 4px;
        background: var(--primary-color);
        color: var(--text-primary-color, #fff);
        font-size: 14px;
        font-weight: 500;
        cursor: pointer;
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 8px;
      }
      .translate-btn:disabled {
        opacity: 0.6;
        cursor: not-allowed;
      }
      .translate-btn:hover:not(:disabled) {
        opacity: 0.9;
      }
      ha-alert {
        display: block;
        margin-top: 8px;
      }
    `;
  }
}

/**
 * Card Editor
 */
class ArgosTranslateCardEditor extends LitElement {
  static get properties() {
    return {
      hass: { type: Object },
      config: { type: Object },
    };
  }

  setConfig(config) {
    this.config = config;
  }

  render() {
    if (!this.hass || !this.config) {
      return html``;
    }

    return html`
      <div class="editor">
        <ha-entity-picker
          label="Status Entity"
          .hass="${this.hass}"
          .value="${this.config.entity || ""}"
          @value-changed="${this._entityChanged}"
          .includeDomains="${["binary_sensor"]}"
          allow-custom-entity
        ></ha-entity-picker>
        <ha-entity-picker
          label="Language Entity"
          .hass="${this.hass}"
          .value="${this.config.language_entity || ""}"
          @value-changed="${this._langEntityChanged}"
          .includeDomains="${["sensor"]}"
          allow-custom-entity
        ></ha-entity-picker>
        <ha-textfield
          label="Header"
          .value="${this.config.header || ""}"
          @input="${this._headerChanged}"
        ></ha-textfield>
        <ha-textfield
          label="Default Source Language (code)"
          .value="${this.config.default_source || ""}"
          @input="${this._defaultSourceChanged}"
          placeholder="e.g., en"
        ></ha-textfield>
        <ha-textfield
          label="Default Target Language (code)"
          .value="${this.config.default_target || ""}"
          @input="${this._defaultTargetChanged}"
          placeholder="e.g., es"
        ></ha-textfield>
      </div>
    `;
  }

  _entityChanged(ev) {
    this._updateConfig("entity", ev.detail.value);
  }

  _langEntityChanged(ev) {
    this._updateConfig("language_entity", ev.detail.value);
  }

  _headerChanged(ev) {
    this._updateConfig("header", ev.target.value);
  }

  _defaultSourceChanged(ev) {
    this._updateConfig("default_source", ev.target.value);
  }

  _defaultTargetChanged(ev) {
    this._updateConfig("default_target", ev.target.value);
  }

  _updateConfig(key, value) {
    if (!this.config) return;
    const newConfig = { ...this.config, [key]: value };
    const event = new CustomEvent("config-changed", {
      detail: { config: newConfig },
      bubbles: true,
      composed: true,
    });
    this.dispatchEvent(event);
  }

  static get styles() {
    return css`
      .editor {
        display: flex;
        flex-direction: column;
        gap: 16px;
        padding: 16px;
      }
    `;
  }
}

if (!customElements.get("argos-translate-card")) {
  customElements.define(
    "argos-translate-card",
    ArgosTranslateCard
  );
}
if (!customElements.get("argos-translate-card-editor")) {
  customElements.define(
    "argos-translate-card-editor",
    ArgosTranslateCardEditor
  );
}

window.customCards = window.customCards || [];
window.customCards.push({
  type: "argos-translate-card",
  name: "Argos Translate Card",
  description: "Local text translation via LibreTranslate for Home Assistant.",
  preview: true,
});
