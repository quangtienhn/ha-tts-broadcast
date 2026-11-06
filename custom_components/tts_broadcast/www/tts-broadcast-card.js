const VERSION = "1.1.1";

const STRINGS = {
  en: {
    empty: "TTS Broadcast not configured",
    assist: "Assist",
  },
  vi: {
    empty: "Chưa cấu hình TTS Broadcast",
    assist: "Trợ lý",
  },
};

function strings(hass) {
  const lang = (hass && hass.language) || "en";
  return STRINGS[lang] || STRINGS.en;
}

class TTSBroadcastCard extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: "open" });
    this._config = {};
    this._hass = null;
    this._card = null;
    this._signature = "";
  }

  setConfig(config) {
    this._config = {
      title: "TTS Broadcast",
      show_volume: true,
      show_message: true,
      show_assist: true,
      assist_pipeline_id: "preferred",
      show_select_buttons: true,
      ...config,
    };
    this._rebuild();
  }

  set hass(hass) {
    this._hass = hass;
    if (this._card) {
      this._card.hass = hass;
    }
    this._maybeRebuild();
  }

  static getStubConfig() {
    return { title: "TTS Broadcast" };
  }

  getCardSize() {
    return 4;
  }

  _discover() {
    if (!this._hass || !this._hass.entities) return [];
    return Object.values(this._hass.entities).filter(
      (e) => e.platform === "tts_broadcast"
    );
  }

  _signatureOf(entities) {
    return entities.map((e) => e.entity_id).sort().join("|");
  }

  _maybeRebuild() {
    const entities = this._discover();
    const sig = this._signatureOf(entities);
    if (sig !== this._signature) {
      this._signature = sig;
      this._rebuild();
    } else if (this._card) {
      this._card.hass = this._hass;
    }
  }

  async _rebuild() {
    if (!this._hass) return;
    const helpers = await (window.loadCardHelpers ? window.loadCardHelpers() : Promise.resolve(null));
    const entities = this._discover();
    const s = strings(this._hass);
    this.shadowRoot.innerHTML = "";

    if (entities.length === 0) {
      const div = document.createElement("div");
      div.style.padding = "16px";
      div.textContent = s.empty;
      this.shadowRoot.appendChild(div);
      this._card = null;
      return;
    }

    const switches = entities
      .filter((e) => e.entity_id.startsWith("switch."))
      .sort((a, b) =>
        (a.name || a.entity_id).localeCompare(b.name || b.entity_id)
      );
    const volume = entities.find((e) => e.translation_key === "volume");
    const message = entities.find((e) => e.translation_key === "message");
    const speak = entities.find((e) => e.translation_key === "speak");
    const stop = entities.find((e) => e.translation_key === "stop");
    const selectAll = entities.find((e) => e.translation_key === "select_all");
    const selectNone = entities.find((e) => e.translation_key === "select_none");

    const rows = [];
    switches.forEach((e) => rows.push(e.entity_id));

    const showVolume = this._config.show_volume !== false && volume;
    const showMessage = this._config.show_message !== false && message;
    if (showVolume || showMessage) {
      rows.push({ type: "divider" });
      if (showVolume) rows.push(volume.entity_id);
      if (showMessage) rows.push(message.entity_id);
    }

    rows.push({ type: "divider" });
    if (speak) rows.push(speak.entity_id);
    if (this._config.show_assist !== false) {
      rows.push({
        type: "button",
        name: s.assist,
        tap_action: {
          action: "assist",
          pipeline_id: this._config.assist_pipeline_id || "preferred",
          start_listening: true,
        },
      });
    }
    if (stop) rows.push(stop.entity_id);
    if (this._config.show_select_buttons !== false) {
      if (selectAll) rows.push(selectAll.entity_id);
      if (selectNone) rows.push(selectNone.entity_id);
    }

    const cardConfig = {
      type: "entities",
      title: this._config.title || "TTS Broadcast",
      entities: rows,
    };

    if (!helpers || !helpers.createCardElement) {
      const div = document.createElement("div");
      div.style.padding = "16px";
      div.textContent = "Card helpers unavailable";
      this.shadowRoot.appendChild(div);
      return;
    }

    const card = await helpers.createCardElement(cardConfig);
    card.hass = this._hass;
    this.shadowRoot.appendChild(card);
    this._card = card;
  }
}

class TTSBroadcastCardEditor extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: "open" });
    this._config = {};
    this._hass = null;
  }

  setConfig(config) {
    this._config = config || {};
    this._render();
  }

  set hass(hass) {
    this._hass = hass;
    this._render();
  }

  _render() {
    if (!this._hass) return;
    const schema = [
      { name: "title", selector: { text: {} } },
      { name: "show_volume", selector: { boolean: {} } },
      { name: "show_message", selector: { boolean: {} } },
      { name: "show_assist", selector: { boolean: {} } },
      { name: "assist_pipeline_id", selector: { assist_pipeline: {} } },
      { name: "show_select_buttons", selector: { boolean: {} } },
    ];
    const root = this.shadowRoot;
    root.innerHTML = "";
    const form = document.createElement("ha-form");
    form.schema = schema;
    form.data = this._config;
    form.addEventListener("value-changed", (ev) => {
      const newConfig = ev.detail.value;
      this._config = newConfig;
      this.dispatchEvent(
        new CustomEvent("config-changed", {
          detail: { config: newConfig },
          bubbles: true,
          composed: true,
        })
      );
    });
    root.appendChild(form);
  }
}

customElements.define("tts-broadcast-card", TTSBroadcastCard);
customElements.define("tts-broadcast-card-editor", TTSBroadcastCardEditor);

window.customCards = window.customCards || [];
window.customCards.push({
  type: "tts-broadcast-card",
  name: "TTS Broadcast",
  description: "Broadcast TTS to multiple speakers",
  preview: true,
  documentationURL: "https://github.com/quangtienhn/ha-tts-broadcast",
});

console.info(`%c TTS-BROADCAST-CARD %c ${VERSION}`, "color: white; background: #1f6feb; font-weight: bold;", "color: #1f6feb; background: white; font-weight: bold;");