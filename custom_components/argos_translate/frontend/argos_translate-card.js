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

const CARD_VERSION = "0.5.2";
const DETECTION_CONFIDENCE_THRESHOLD = 50.0;

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
      _detectedLanguage: { type: Object },
      _detectionCandidates: { type: Array },
    };
  }

  constructor() {
    super();
    this._source = "auto";
    this._target = "";
    this._inputText = "";
    this._outputText = "";
    this._loading = false;
    this._error = null;
    this._detectedLanguage = null;
    this._detectionCandidates = [];
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
    return 4;
  }

  getGridOptions() {
    return {
      rows: 4,
      columns: 12,
      min_rows: 3,
      min_columns: 4,
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
    if (sourceCode === "auto" || (typeof sourceCode === "string" && sourceCode.startsWith("auto:"))) {
      const { codes } = this._getLanguages();
      return codes;
    }
    const { targets } = this._getLanguages();
    return targets[sourceCode] || [];
  }

  _getLanguageName(code) {
    const { names, codes } = this._getLanguages();
    const idx = codes.indexOf(code);
    return idx >= 0 ? names[idx] : code;
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
      }
      if (codes.length > 0 && !this._target) {
        const validTargets = this._getTargetsForSource(this._source);
        this._target =
          (this.config && this.config.default_target && validTargets.includes(this.config.default_target)
            ? this.config.default_target
            : validTargets[0] || "");
      }
    }
  }

  _sourceChanged(ev) {
    const val = ev.target.value;
    if (val.startsWith("auto:")) {
      // User picked a detection candidate — re-translate with that fixed source
      const fixedSource = val.slice(5);
      this._source = fixedSource;
      this._detectedLanguage = null;
      this._detectionCandidates = [];
      const validTargets = this._getTargetsForSource(this._source);
      if (!validTargets.includes(this._target)) {
        this._target = validTargets[0] || "";
      }
      // Trigger re-translate with the fixed source
      if (this._inputText && this._target) {
        this._translate();
      }
    } else {
      this._source = val;
      if (val !== "auto") {
        // Switching away from auto-detect — clear detection state
        this._detectedLanguage = null;
        this._detectionCandidates = [];
      }
      const validTargets = this._getTargetsForSource(this._source);
      if (!validTargets.includes(this._target)) {
        this._target = validTargets[0] || "";
      }
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
    if (this._source === "auto") return; // Can't swap auto-detect
    const oldSource = this._source;
    const oldTarget = this._target;

    // Pre-swap guard: check if the reversed pair exists
    const reversedTargets = this._getTargetsForSource(oldTarget);
    if (!reversedTargets.includes(oldSource)) {
      const targetName = this._getLanguageName(oldTarget);
      const sourceName = this._getLanguageName(oldSource);
      this._error = `Cannot swap \u2014 ${targetName} \u2192 ${sourceName} translation pair is not installed.`;
      this.requestUpdate();
      return;
    }

    this._source = oldTarget;
    this._target = oldSource;

    // Move output to input for convenient back-translation
    if (this._outputText) {
      this._inputText = this._outputText;
      this._outputText = "";
    }

    this._error = null;
    this.requestUpdate();
  }

  async _translate() {
    // Determine actual source to send — "auto" or a specific code
    const sourceToSend = this._source;

    if (!this._inputText || !sourceToSend || !this._target) return;

    this._loading = true;
    this._error = null;

    try {
      const result = await this.hass.callService(
        "argos_translate",
        "translate",
        {
          text: this._inputText,
          source: sourceToSend,
          target: this._target,
        },
        {},
        true,
        true
      );

      const resp = result.response;
      this._outputText = resp.translated_text;

      // Handle auto-detect feedback
      if (sourceToSend === "auto" && resp.detected_language) {
        this._detectedLanguage = {
          language: resp.detected_language,
          confidence: resp.detection_confidence,
        };

        // Handle uninstalled detected language warning (DTCT-06 — display side)
        if (resp.uninstalled_detected_language) {
          const langName = this._getLanguageName(resp.uninstalled_detected_language) || resp.uninstalled_detected_language;
          this._error = `Detected language "${langName}" (${resp.uninstalled_detected_language}) is not installed on the LibreTranslate server. Translation may be incomplete.`;
        } else if (resp.error) {
          this._error = resp.error;
        }

        // Fetch detection candidates via the detect HA service (registered in Plan 05-01).
        // This calls LibreTranslate's /detect endpoint and returns multiple candidates
        // with confidence scores, enabling the user to pick an alternative detection.
        try {
          const detectResult = await this.hass.callService(
            "argos_translate",
            "detect",
            { text: this._inputText },
            {},
            true,
            true
          );
          const detections = detectResult.response.detections || [];
          // Filter to candidates above the confidence threshold
          this._detectionCandidates = detections.filter(
            (d) => d.confidence >= DETECTION_CONFIDENCE_THRESHOLD
          );
        } catch (_detectErr) {
          // Detection candidates are best-effort — if /detect fails,
          // we still have the primary detected language from /translate.
          this._detectionCandidates = [];
        }
      } else {
        this._detectedLanguage = null;
        this._detectionCandidates = [];
      }
    } catch (err) {
      // Error discrimination from Plan 02 is already in place
      const code = err?.code;
      const msg = err?.message || "";
      if (!code || typeof code === "number") {
        this._error = "Cannot reach Home Assistant. Check your connection.";
      } else if (code === "home_assistant_error") {
        const lower = msg.toLowerCase();
        if (lower.includes("timeout") || lower.includes("timed out")) {
          this._error = "Translation timed out. The server may be busy — try again.";
        } else if (lower.includes("connection") || lower.includes("connect")) {
          this._error = "Cannot connect to LibreTranslate server. Check that it is running.";
        } else {
          this._error = `Translation error: ${msg}`;
        }
      } else if (code === "service_validation_error") {
        this._error = `Invalid request: ${msg}`;
      } else {
        this._error = msg || "Translation failed.";
      }
    } finally {
      this._loading = false;
    }
  }

  _getDisabledReason() {
    if (this._loading) return null; // button shows "Translating..." spinner instead
    const status = this._getStatus();
    if (!status.online) return "LibreTranslate server is offline";
    if (!this._inputText) return "Enter text to translate";
    if (!this._source) return "Select a source language";
    if (!this._target) return "Select a target language";
    return null;
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

    const layout = (this.config && this.config.layout) || "auto";
    this.setAttribute("data-layout", layout);

    return html`
      <ha-card header="${this.config.header || ""}">
        <div class="card-content">
          <div class="status-bar">
            <span class="${statusDotClass}"></span>
            <span>${statusText}</span>
          </div>

          <div class="lang-row">
            <select
              aria-label="Source language"
              .value="${this._source}"
              @change="${this._sourceChanged}"
            >
              <option value="auto" ?selected="${this._source === 'auto'}">
                ${this._detectedLanguage
                  ? `Auto (${this._getLanguageName(this._detectedLanguage.language)})`
                  : "Auto-detect"}
              </option>
              ${this._detectionCandidates
                .filter(c => c.language !== (this._detectedLanguage && this._detectedLanguage.language))
                .map(c => html`
                  <option value="auto:${c.language}">
                    Auto (${this._getLanguageName(c.language)})
                  </option>
                `)}
              <option disabled>──────────</option>
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
              aria-label="Swap languages"
              ?disabled="${this._source === 'auto'}"
            ></ha-icon-button>

            <select
              aria-label="Target language"
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

          <div class="container-wrap">
            <div class="content-area">
              <div class="input-panel">
                <textarea
                  rows="4"
                  placeholder="Enter text to translate..."
                  aria-label="Text to translate"
                  .value="${this._inputText}"
                  @input="${this._inputChanged}"
                ></textarea>
              </div>
              <div class="output-panel">
                <textarea
                  rows="4"
                  readonly
                  placeholder=""
                  aria-label="Translated text"
                  .value="${this._outputText}"
                ></textarea>
              </div>
            </div>
          </div>

          ${this._detectedLanguage ? html`
            <div class="detection-info">
              Detected: ${this._getLanguageName(this._detectedLanguage.language)}
              (${Math.round(this._detectedLanguage.confidence)}%)
            </div>
          ` : ""}

          <button
            class="translate-btn"
            @click="${this._translate}"
            ?disabled="${!canTranslate}"
          >
            ${this._loading
              ? html`<ha-spinner size="small"></ha-spinner> Translating...`
              : "Translate"}
          </button>

          ${(() => {
            const reason = this._getDisabledReason();
            return reason ? html`<div class="hint">${reason}</div>` : "";
          })()}

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
        height: 100%;
        box-sizing: border-box;
      }
      ha-card {
        overflow: hidden;
        height: 100%;
        display: flex;
        flex-direction: column;
      }
      .card-content {
        padding: 0 16px 16px;
        flex: 1;
        overflow: auto;
      }
      .container-wrap {
        container-type: inline-size;
        container-name: argos-card;
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
        flex-wrap: wrap;
      }
      .lang-row select {
        flex: 1 1 120px;
        padding: 8px;
        border: 1px solid var(--divider-color, #e0e0e0);
        border-radius: 4px;
        background: var(--card-background-color, #fff);
        color: var(--primary-text-color);
        font-size: 14px;
        min-width: 100px;
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
        resize: none;
      }
      textarea[readonly] {
        background: var(--secondary-background-color, #f5f5f5);
      }
      .content-area {
        display: flex;
        flex-direction: column;
        gap: 12px;
      }
      .input-panel textarea,
      .output-panel textarea {
        width: 100%;
        box-sizing: border-box;
      }
      @container argos-card (min-width: 580px) {
        .content-area {
          flex-direction: row;
        }
        .input-panel,
        .output-panel {
          flex: 1;
          min-width: 0;
        }
      }
      :host([data-layout="horizontal"]) .content-area {
        flex-direction: row;
      }
      :host([data-layout="horizontal"]) .input-panel,
      :host([data-layout="horizontal"]) .output-panel {
        flex: 1;
        min-width: 0;
      }
      :host([data-layout="vertical"]) .content-area {
        flex-direction: column;
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
      .hint {
        text-align: center;
        font-size: 0.8em;
        color: var(--secondary-text-color);
        margin-top: -8px;
        margin-bottom: 4px;
      }
      .detection-info {
        font-size: 0.85em;
        color: var(--secondary-text-color);
        padding: 4px 0;
        margin-top: 4px;
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
        <ha-select
          label="Layout"
          .value="${this.config.layout || "auto"}"
          @selected="${this._layoutChanged}"
          @closed="${(ev) => ev.stopPropagation()}"
        >
          <mwc-list-item value="auto">Auto (responsive)</mwc-list-item>
          <mwc-list-item value="horizontal">Horizontal</mwc-list-item>
          <mwc-list-item value="vertical">Vertical</mwc-list-item>
        </ha-select>
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

  _layoutChanged(ev) {
    this._updateConfig("layout", ev.target.value);
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
