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

## TTS speak list support
- Verified in installed HA 2026.11.0 source: `homeassistant/components/tts/services.py` registers `speak` with `ATTR_MEDIA_PLAYER_ENTITY_ID: cv.comp_entity_ids`, so a list is accepted. The integration calls `tts.speak` once with `media_player_entity_id` as a list.

## Config and options flow
- Normal `ConfigFlow` + `OptionsFlowWithReload`. Options flow reloads the entry automatically. Validation performed in code.

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

## Sources
- Manifest: https://contributors.home-assistant.io/core/integrations/manifest/
- Config flow: https://contributors.home-assistant.io/core/integrations/config-flow/
- TTS services source: installed HA 2026.11.0 `homeassistant/components/tts/services.py`
- Conversation trigger source: installed HA 2026.11.0 `homeassistant/components/conversation/trigger.py`

## Uncertainties
- `media_player.media_stop` interruption on ESPHome announcement pipelines is unverified.
- Tapo speaker compatibility is unknown; configured as no-volume speaker.
- Wyoming TTS language handling: language is optional and empty by default.
- Sentence triggers with an LLM conversation agent may require "Prefer handling commands locally"; unverified.
- Frontend visual editor support for the `assist_pipeline` selector used by the TTS Broadcast card is unverified locally; backend selector registration was verified in HA source.