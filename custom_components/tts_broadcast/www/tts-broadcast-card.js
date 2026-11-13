const VERSION = "1.2.1";

const AUTO_PIPELINE = "auto";

const STRINGS = {
  en: {
    empty: "TTS Broadcast not configured",
    assist: "TALK",
    assist_name: "TALK",
    assist_icon: "mdi:microphone",
    assist_auto: "Auto (TTS Broadcast pipeline)",
    assist_no_pipeline:
      "No Assist pipeline uses the TTS Broadcast agent. Create one: Settings > Voice assistants > Add assistant > Conversation agent: TTS Broadcast.",
    assist_tooltip_multiple:
      "Multiple Assist pipelines use the TTS Broadcast agent; using the first one by name.",
  },
  vi: {
    empty: "Chưa cấu hình TTS Broadcast",
    assist: "NÓI",
    assist_name: "NÓI",
    assist_icon: "mdi:microphone",
    assist_auto: "Tự động (pipeline TTS Broadcast)",
    assist_no_pipeline:
      "Không có pipeline Assist nào sử dụng agent TTS Broadcast. Tạo một pipeline: Settings > Voice assistants > Thêm trợ lý > Đạo lý trò chuyện: TTS Broadcast.",
    assist_tooltip_multiple:
      "Nhiều pipeline Assist sử dụng agent TTS Broadcast; đang dùng pipeline đầu tiên theo tên.",
  },
};

function strings(hass) {
  const lang = (hass && hass.language) || "en";
  return STRINGS[lang] || STRINGS.en;
}

const ALLOWED_PIPELINE_IDS = [AUTO_PIPELINE, "preferred", "last_used"];

class TTSBroadcastCard extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: "open" });
    this._config = {};
    this._hass = null;
    this._card = null;
    this._signature = "";
    this._resolvedAssistPipeline = null;
    this._assistPipelineError = null;
  }

  setConfig(config) {
    this._config = {
      title: "TTS Broadcast",
      show_volume: true,
      show_message: true,
      show_assist: true,
      assist_pipeline_id: AUTO_PIPELINE,
      assist_name: undefined,
      assist_icon: undefined,
      show_select_buttons: true,
      ...config,
    };
    // Normalize: only explicit values are honored; anything else falls back to auto.
    if (
      this._config.assist_pipeline_id !== AUTO_PIPELINE &&
      this._config.assist_pipeline_id !== "preferred" &&
      this._config.assist_pipeline_id !== "last_used" &&
      !this._looksLikePipelineId(this._config.assist_pipeline_id)
    ) {
      this._config.assist_pipeline_id = AUTO_PIPELINE;
    }
    this._resolvedAssistPipeline = null;
    this._assistPipelineError = null;
    this._rebuild();
  }

  // Heuristic: a concrete pipeline id stored by HA is a non-empty string that is
  // not one of the reserved keywords.
  _looksLikePipelineId(value) {
    return typeof value === "string" && value.length > 0;
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
    const helpers = await (window.loadCardHelpers
      ? window.loadCardHelpers()
      : Promise.resolve(null));
    const entities = this._discover();
    const s = strings(this._hass);
    this.shadowRoot.innerHTML = "";

    if (entities.length === 0) {
      const div = document.createElement("div");
      div.style.padding = "16px";
      div.textContent = s.empty;
      this.shadowRoot.appendChild(div);
      this._card = null;
      this._resolvedAssistPipeline = null;
      this._assistPipelineError = null;
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

    // Strip the device-name prefix ("TTS Broadcast ") that recent HA versions
    // prepend to friendly names of entities with has_entity_name = True.
    const deviceNames = new Set(["TTS Broadcast"]);
    entities.forEach((e) => {
      const dn =
        this._hass.devices &&
        this._hass.devices[e.device_id] &&
        this._hass.devices[e.device_id].name;
      if (dn) deviceNames.add(dn);
    });
    const row = (e) => {
      const st = this._hass.states[e.entity_id];
      const fn = st && st.attributes && st.attributes.friendly_name;
      if (!fn) return e.entity_id;
      for (const d of deviceNames) {
        if (fn.startsWith(d + " ")) {
          return { entity: e.entity_id, name: fn.slice(d.length + 1) };
        }
      }
      return e.entity_id;
    };

    const rows = [];
    switches.forEach((e) => rows.push(row(e)));

    const showVolume = this._config.show_volume !== false && volume;
    const showMessage = this._config.show_message !== false && message;
    if (showVolume || showMessage) {
      rows.push({ type: "divider" });
      if (showVolume) rows.push(row(volume));
      if (showMessage) rows.push(row(message));
    }

    rows.push({ type: "divider" });
    if (speak) rows.push(row(speak));

    if (this._config.show_assist !== false) {
      const assistPipeline = await this._resolveAssistPipeline(s);
      if (assistPipeline) {
        const assistName =
          this._config.assist_name ||
          assistPipeline.name ||
          s.assist;
        const assistIcon =
          this._config.assist_icon || s.assist_icon;
        rows.push({
          type: "button",
          name: assistName,
          icon: assistIcon,
          tap_action: {
            action: "assist",
            pipeline_id: assistPipeline.id,
            start_listening: true,
          },
        });
      } else if (this._config.assist_pipeline_id === AUTO_PIPELINE) {
        // Auto mode but no pipeline uses our agent: hide TALK row, show info line.
        const div = document.createElement("div");
        div.style.padding = "8px 16px";
        div.style.color = "var(--primary-text-color, var(--text-primary-color))";
        div.textContent = s.assist_no_pipeline;
        this.shadowRoot.appendChild(div);
      }
    }

    if (stop) rows.push(row(stop));
    if (this._config.show_select_buttons !== false) {
      if (selectAll) rows.push(row(selectAll));
      if (selectNone) rows.push(row(selectNone));
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

  /**
   * Resolve the Assist pipeline to use for the TALK row.
   *
   * - "auto": find a pipeline whose conversation engine is this integration's
   *   conversation entity. Discovered via the assist_pipeline/pipeline/list
   *   websocket API; result is cached until the card rebuilds.
   * - "preferred" / "last_used": honored as explicit user choices.
   * - concrete id: used as-is.
   *
   * Returns {id, name} or null when no pipeline should be used.
   */
  async _resolveAssistPipeline(s) {
    const configured = this._config.assist_pipeline_id;

    // Explicit choice (concrete id, "preferred", or "last_used"): honor as-is.
    if (configured !== AUTO_PIPELINE) {
      return { id: configured, name: configured };
    }

    // Auto mode: use cached result if we already looked it up this build.
    if (configured === AUTO_PIPELINE && this._resolvedAssistPipeline) {
      return this._resolvedAssistPipeline;
    }

    // Discover our conversation entity id from the entity registry data.
    const ourConversationEntity = this._findOurConversationEntity();
    if (!ourConversationEntity) {
      this._assistPipelineError =
        "No TTS Broadcast conversation entity found.";
      return null;
    }

    let pipelines;
    try {
      pipelines = await this._listAssistPipelines();
    } catch (err) {
      this._assistPipelineError = String(err);
      return null;
    }

    const ours = pipelines.filter(
      (p) => p.conversation_engine === ourConversationEntity
    );
    if (ours.length === 0) {
      this._resolvedAssistPipeline = null;
      this._assistPipelineError = null;
      return null;
    }

    // If several pipelines use our agent, pick the first by name and note it.
    ours.sort((a, b) => (a.name || "").localeCompare(b.name || ""));
    if (ours.length > 1) {
      this._assistPipelineError = s.assist_tooltip_multiple;
    } else {
      this._assistPipelineError = null;
    }
    this._resolvedAssistPipeline = ours[0];
    return ours[0];
  }

  _findOurConversationEntity() {
    if (!this._hass || !this._hass.entities) return null;
    for (const entity of Object.values(this._hass.entities)) {
      if (
        entity.platform === "tts_broadcast" &&
        entity.entity_id.startsWith("conversation.")
      ) {
        return entity.entity_id;
      }
    }
    return null;
  }

  async _listAssistPipelines() {
    const response = await this._hass.connection.sendMessagePromise({
      type: "assist_pipeline/pipeline/list",
    });
    return response.pipelines || [];
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
      {
        name: "assist_pipeline_id",
        selector: { text: {} },
        description:
          'Allowed values: "auto" (default, finds the pipeline using the TTS Broadcast agent), "preferred", "last_used", or a concrete pipeline id.',
      },
      { name: "assist_name", selector: { text: {} } },
      { name: "assist_icon", selector: { text: {} } },
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

console.info(
  `%c TTS-BROADCAST-CARD %c ${VERSION}`,
  "color: white; background: #1f6feb; font-weight: bold;",
  "color: #1f6feb; background: white; font-weight: bold;"
);
