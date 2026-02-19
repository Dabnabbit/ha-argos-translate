/**
 * Argos Translate Card
 *
 * A Lovelace card for translating text via a local
 * LibreTranslate / Argos Translate server.
 */

const LitElement = customElements.get("hui-masonry-view")
  ? Object.getPrototypeOf(customElements.get("hui-masonry-view"))
  : Object.getPrototypeOf(customElements.get("hui-view"));
const html = LitElement.prototype.html;
const css = LitElement.prototype.css;

const CARD_VERSION = "0.1.0";

console.info(
  `%c ARGOS-TRANSLATE-CARD %c v${CARD_VERSION} `,
  "color: cyan; font-weight: bold; background: black",
  "color: white; font-weight: bold; background: dimgray"
);

class ArgosTranslateCard extends LitElement {
  static get properties() {
    return {
      hass: { type: Object },
      config: { type: Object },
      _sourceLang: { type: String },
      _targetLang: { type: String },
      _inputText: { type: String },
      _outputText: { type: String },
      _translating: { type: Boolean },
      _languages: { type: Array },
    };
  }

  constructor() {
    super();
    this._sourceLang = "en";
    this._targetLang = "es";
    this._inputText = "";
    this._outputText = "";
    this._translating = false;
    this._languages = [];
  }

  static getConfigElement() {
    return document.createElement("argos-translate-card-editor");
  }

  static getStubConfig() {
    return {
      header: "Translate",
    };
  }

  setConfig(config) {
    if (!config) throw new Error("Invalid configuration");
    this.config = { header: "Translate", ...config };
  }

  getCardSize() {
    return 5;
  }

  updated(changedProperties) {
    if (changedProperties.has("hass") && this.hass) {
      this._loadLanguages();
    }
  }

  _loadLanguages() {
    // Try to get languages from the status sensor's attributes
    // or use a default set
    if (this._languages.length > 0) return;

    this._languages = [
      { code: "en", name: "English" },
      { code: "es", name: "Spanish" },
      { code: "fr", name: "French" },
      { code: "de", name: "German" },
      { code: "it", name: "Italian" },
      { code: "pt", name: "Portuguese" },
      { code: "ru", name: "Russian" },
      { code: "zh", name: "Chinese" },
      { code: "ja", name: "Japanese" },
      { code: "ko", name: "Korean" },
      { code: "ar", name: "Arabic" },
      { code: "hi", name: "Hindi" },
      { code: "nl", name: "Dutch" },
      { code: "pl", name: "Polish" },
      { code: "tr", name: "Turkish" },
      { code: "uk", name: "Ukrainian" },
    ];
  }

  render() {
    if (!this.hass || !this.config) return html``;

    return html`
      <ha-card header="${this.config.header}">
        <div class="card-content">
          <div class="lang-row">
            <select
              class="lang-select"
              .value="${this._sourceLang}"
              @change="${this._sourceChanged}"
            >
              ${this._languages.map(
                (l) =>
                  html`<option
                    value="${l.code}"
                    ?selected="${l.code === this._sourceLang}"
                  >
                    ${l.name}
                  </option>`
              )}
            </select>

            <button class="swap-btn" @click="${this._swapLanguages}">
              &#8646;
            </button>

            <select
              class="lang-select"
              .value="${this._targetLang}"
              @change="${this._targetChanged}"
            >
              ${this._languages.map(
                (l) =>
                  html`<option
                    value="${l.code}"
                    ?selected="${l.code === this._targetLang}"
                  >
                    ${l.name}
                  </option>`
              )}
            </select>
          </div>

          <textarea
            class="input-area"
            placeholder="Enter text to translate..."
            .value="${this._inputText}"
            @input="${this._inputChanged}"
            rows="4"
          ></textarea>

          <button
            class="translate-btn"
            @click="${this._doTranslate}"
            ?disabled="${this._translating || !this._inputText.trim()}"
          >
            ${this._translating ? "Translating..." : "Translate"}
          </button>

          <textarea
            class="output-area"
            placeholder="Translation will appear here..."
            .value="${this._outputText}"
            readonly
            rows="4"
          ></textarea>

          ${this._renderStatus()}
        </div>
      </ha-card>
    `;
  }

  _renderStatus() {
    const statusEntity = Object.keys(this.hass.states).find(
      (e) => e.startsWith("sensor.argos_translate") && e.endsWith("_status")
    );
    const langEntity = Object.keys(this.hass.states).find(
      (e) =>
        e.startsWith("sensor.argos_translate") &&
        e.endsWith("_available_languages")
    );

    const status = statusEntity
      ? this.hass.states[statusEntity].state
      : "unknown";
    const langCount = langEntity
      ? this.hass.states[langEntity].state
      : "?";

    return html`
      <div class="status-bar">
        <span class="status-dot ${status === "online" ? "online" : "offline"}">
        </span>
        <span class="status-text">${status}</span>
        <span class="lang-count">${langCount} languages</span>
      </div>
    `;
  }

  _sourceChanged(ev) {
    this._sourceLang = ev.target.value;
  }

  _targetChanged(ev) {
    this._targetLang = ev.target.value;
  }

  _inputChanged(ev) {
    this._inputText = ev.target.value;
  }

  _swapLanguages() {
    const tmp = this._sourceLang;
    this._sourceLang = this._targetLang;
    this._targetLang = tmp;

    // Also swap text
    if (this._outputText) {
      const tmpText = this._inputText;
      this._inputText = this._outputText;
      this._outputText = tmpText;
    }
  }

  async _doTranslate() {
    if (!this._inputText.trim()) return;
    this._translating = true;
    this._outputText = "";

    try {
      const result = await this.hass.callService(
        "argos_translate",
        "translate",
        {
          text: this._inputText,
          source: this._sourceLang,
          target: this._targetLang,
        },
        undefined,
        true // return_response
      );

      if (result?.response?.translated_text) {
        this._outputText = result.response.translated_text;
      } else {
        this._outputText = "[No translation returned]";
      }
    } catch (err) {
      this._outputText = `[Error: ${err.message || err}]`;
    } finally {
      this._translating = false;
    }
  }

  static get styles() {
    return css`
      ha-card {
        padding: 16px;
      }
      .card-content {
        padding: 0 16px 16px;
        display: flex;
        flex-direction: column;
        gap: 12px;
      }
      .lang-row {
        display: flex;
        gap: 8px;
        align-items: center;
      }
      .lang-select {
        flex: 1;
        padding: 8px;
        border: 1px solid var(--divider-color, #e0e0e0);
        border-radius: 4px;
        background: var(--card-background-color);
        color: var(--primary-text-color);
        font-size: 14px;
      }
      .swap-btn {
        padding: 8px 12px;
        border: 1px solid var(--divider-color, #e0e0e0);
        border-radius: 4px;
        background: transparent;
        color: var(--primary-color);
        cursor: pointer;
        font-size: 18px;
        line-height: 1;
      }
      .swap-btn:hover {
        background: var(--secondary-background-color);
      }
      textarea {
        width: 100%;
        padding: 10px;
        border: 1px solid var(--divider-color, #e0e0e0);
        border-radius: 4px;
        background: var(--card-background-color);
        color: var(--primary-text-color);
        font-family: inherit;
        font-size: 14px;
        resize: vertical;
        box-sizing: border-box;
      }
      textarea:focus {
        outline: none;
        border-color: var(--primary-color);
      }
      .output-area {
        background: var(--secondary-background-color);
      }
      .translate-btn {
        padding: 10px 20px;
        border: none;
        border-radius: 4px;
        background: var(--primary-color);
        color: var(--text-primary-color, white);
        cursor: pointer;
        font-size: 14px;
        font-weight: 500;
        align-self: center;
      }
      .translate-btn:disabled {
        opacity: 0.5;
        cursor: not-allowed;
      }
      .status-bar {
        display: flex;
        align-items: center;
        gap: 8px;
        font-size: 12px;
        color: var(--secondary-text-color);
        padding-top: 8px;
        border-top: 1px solid var(--divider-color, #e0e0e0);
      }
      .status-dot {
        width: 8px;
        height: 8px;
        border-radius: 50%;
        background: var(--error-color, red);
      }
      .status-dot.online {
        background: var(--success-color, green);
      }
      .lang-count {
        margin-left: auto;
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
    if (!this.hass || !this.config) return html``;

    return html`
      <div class="editor">
        <ha-textfield
          label="Header"
          .value="${this.config.header || ""}"
          @input="${this._headerChanged}"
        ></ha-textfield>
      </div>
    `;
  }

  _headerChanged(ev) {
    this._updateConfig("header", ev.target.value);
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

customElements.define("argos-translate-card", ArgosTranslateCard);
customElements.define("argos-translate-card-editor", ArgosTranslateCardEditor);

window.customCards = window.customCards || [];
window.customCards.push({
  type: "argos-translate-card",
  name: "Argos Translate Card",
  description: "Translate text using a local translation server",
  preview: true,
});
