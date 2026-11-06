# Decisions and verified findings

## Manifest
- `integration_type`: `service` (domain-level services plus entities; changed during v1.1.1 follow-ups from `helper`).
- `iot_class`: `calculated` (no device communication; logic only).
- `single_config_entry`: `true`.

## Conversation agent
- Verified in installed HA 2026.10.4 source (2026.11 line): `homeassistant.components.conversation` publicly exports `ConversationEntity`, `async_converse`, `ConversationResult` and `ConversationInput`; internal paths (`...conversation.agent_manager`, `...conversation.models`) also resolve. Integration uses the public export.
- Conversation entity `supported_languages` returns `"*"` (accepted by HA: `list[str] | Literal["*"]`).
- Fallback to another agent goes through `async_converse(..., agent_id=...)`; delegation to this integration's own conversation entity is rejected in the options flow and guarded at runtime.

## Replies
- `phrase_matching` returns a reply key (`speak`/`reply`/`delegate` + key) instead of raw text keys like `missing_content`.
- Localized reply table in `conversation.py` (`en`/`vi`, selected by user language, default `en`). `reply_text` overrides only the success (`sent`) reply.

## Static card asset
- Static path + `add_extra_js_url` registered once in `async_setup` (guard flag in `hass.data[DOMAIN]`); no removal on entry unload.

## TTS speak list support (v1.1.2 changed)
- Verified in installed HA 2026.11.0 source: `homeassistant/components/tts/services.py` registers `speak` with `ATTR_MEDIA_PLAYER_ENTITY_ID: cv.comp_entity_ids`, so a list is accepted. Entity `async_speak` converts the whole list into a single `media_player.play_media` call; a failure on one target in a multi-target call is not documented to isolate other targets.
- Integration now calls `tts.speak` once per speaker (`media_player_entity_id: [speaker]`) with `asyncio.gather(..., return_exceptions=True)`; a failing speaker never marks others failed.

## Config and options flow
- Normal `ConfigFlow` + `OptionsFlowWithReload`. Options flow reloads the entry automatically. Validation performed in code.

## Volume slider (v1.1.2)
- The shared number slider is now the single source of truth: `runtime_data.volume`, updated on `async_set_native_value` and restored from last number state in `async_added_to_hass`, synced into runtime data.
- `async_announce` precedence: explicit `volume` service argument > `runtime_data.volume` > options default ("Initial volume"). Speakers in `no_volume_speakers` get no `volume_set`.

## Restore entities
- `RestoreEntity`, `RestoreNumber`, `RestoreText` used. `RestoreNumber`/`RestoreText` already include their base entity, so subclass only the restore class.

## Entity registry tracking
- `async_track_entity_registry_updated_event` used for rename handling and updates stored speaker IDs, then reloads the entry.

## Blueprints
- Integrations cannot auto-install blueprints. Blueprint is provided at repository root `blueprints/automation/tts_broadcast/voice_announce.yaml`.
- Sentence triggers use `platform: conversation` with `command: !input sentences`, verified in `homeassistant/components/conversation/trigger.py`.
- `set_conversation_response` is a supported script action, verified in `homeassistant/helpers/config_validation.py`.

## Services
- Registered once in `async_setup` (domain level) with `SupportsResponse.OPTIONAL`.
- Concurrent calls serialized with one `asyncio.Lock` stored in `hass.data[DOMAIN]`.

## Per-speaker playback (v1.1.2)
- HA 2026.11 `tts.speak`: schema has `media_player_entity_id` (Required, comp_entity_ids=list), `message`, `cache` (Optional, default), `language`, `options. Entity `async_speak` turns it into a single `media_player.play_media` with a generated media source URI (`announce: True`), blocking, with context. Failure semantics for multiple targets are not documented to be isolated per target.
- Integration now calls `tts.speak` once per speaker (`media_player_entity_id: [speaker]`) with `asyncio.gather(..., return_exceptions=True)`; a failing speaker never marks others failed.

## Honest results (v1.1.2)
- Response keeps `played` / `skipped` / `failed` plus new `errors` map `{entity_id: short error}`. "played" means HA accepted the request, not that it was audible.

## Observability (v1.1.2)
- One info log per announcement with resolved/skipped/failed entity ids only (never message text); warning per failed speaker with exception type+message; debug timing. Last result stored in runtime data and returned by diagnostics.

## Card Assist row (v1.1.2)
- The Assist row in the dashboard card uses icon `mdi:microphone` and a localized label: `TALK` (en) / `NÓI` (vi).
- Card editor exposes optional `assist_name` and `assist_icon` text fields to override the label/icon.
- `_build_dashboard_card_yaml` renders `name:` and `icon:` for the Assist button, reading `assist_name`/`assist_icon` from entry options when present, otherwise falling back to localized defaults.
- Idea: options step "Speaker levels" with one NumberSelector per configured speaker (-50..+50 percentage points, default 0, skip no_volume speakers); effective volume = clamp(shared + offset, 0, 100).
- Trade-offs: dynamic options schema complicates validation and translation parity; offsets add state that must survive reload and be stored per speaker; marginal benefit for most setups.
- Decision: not implemented in v1.1.2. Recorded here so a future PR can implement it cleanly with tests for clamping and speaker removal.
## Sources
- Manifest: https://contributors.home-assistant.io/core/integrations/manifest/
- Config flow: https://contributors.home-assistant.io/core/integrations/config-flow/
- TTS services source: installed HA 2026.11.0 `homeassistant/components/tts/services.py`
- TTS entity source: installed HA 2026.11.0 `homeassistant/components/tts/entity.py` (`async_speak`)
- Conversation trigger source: installed HA 2026.11.0 `homeassistant/components/conversation/trigger.py`

## Uncertainties
- `media_player.media_stop` interruption on ESPHome announcement pipelines is unverified.
- Tapo speaker compatibility is unknown; configured as no-volume speaker.
- Wyoming TTS language handling: language is optional and empty by default.
- Sentence triggers with an LLM conversation agent may require "Prefer handling commands locally"; unverified.
- Frontend visual editor support for the `assist_pipeline` selector used by the TTS Broadcast card is unverified locally; backend selector registration was verified in HA source.