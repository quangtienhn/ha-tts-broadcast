# Changelog

All notable changes to the TTS Broadcast integration are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/,
and this project adheres to Semantic Versioning.

## [Unreleased]

## [1.2.1]
### Fixed
- Minimum HA version declared as `2026.11.0` (verified against HA 2026.10.4 source and the 2026.11.0 tag; removed the unverified 2025.1 assumption).
- Repairs issue "No Assist pipeline uses the TTS Broadcast agent" made non-intrusive: warning severity, not fixable, created only when voice phrases are configured, cleared automatically when a pipeline exists.
- Audit `audit: true` no longer holds the announce lock while waiting for the audit window; added a regression test proving a second announcement completes while the first waits for its audit.
- Card editor documents the `assist_pipeline_id` control (text field) and README/TESTING.md kept consistent.
- Language quality pass on README.md and README.vi.md.
- Secrets/PII scan: gitleaks 8.30.1 attempted (binary unavailable via PATH); manual grep of working tree and full git history found no secrets, tokens, emails, personal names, real IPs, or tracked prompt/work-log files in tts_broadcast.

## [1.2.0]

### Fixed
- Card: the TALK (Assist) row now defaults to `assist_pipeline_id: "auto"` and
  selects the Assist pipeline whose conversation engine is the TTS Broadcast
  agent, instead of falling back to the user's default pipeline (which could
  broadcast to all Assist satellites). `preferred` and `last_used` still work
  only when set explicitly. `assist_name` / `assist_icon` editor options added.
- Card: when no Assist pipeline uses the TTS Broadcast agent, the TALK row is
  hidden and a localized info line is shown instead of silently falling back.
- `_build_dashboard_card_yaml` emits the discovered `pipeline_id` (never
  `preferred`) when exactly one pipeline uses the TTS Broadcast agent; a
  commented placeholder is shown otherwise.
- Repairs issue "No Assist pipeline uses the TTS Broadcast agent" created on
  setup and cleared when a pipeline exists.

### Changed
- `services.yaml` now declares `debug_selection`, plus the `cache` and `audit`
  fields of `speak`; English and Vietnamese translations added.
- `tts_broadcast.speak` gains an optional `audit: true` field: wait up to 20 s
  and return `unexpected_started` details in the response.
- Audit now counts only real state transitions, dedupes entities, records
  `from_state`/`to_state`/context ids per unexpected player, and keeps the last
  5 announcements keyed by context id. Defaults to observing configured
  speakers; new option `audit_all_media_players` observes everything.
- Card editor `assist_pipeline_id` is a plain text field documenting the
  allowed values (`auto`, `preferred`, `last_used`, concrete id).
- Minimum HA version declared as 2025.1 in `hacs.json` and the README.

### Added
- `tts_broadcast.debug_selection` diagnostic service (already in 1.1.3, now
  also returns `audit_store`).
- `CHANGELOG.md`, `CONTRIBUTING.md`, `SECURITY.md`, `CODE_OF_CONDUCT.md`,
  issue/PR templates, Dependabot config, and a `PUBLISH_CHECKLIST.md` to
  prepare the repository for going public.

## [1.1.3] - Investigation: extra speakers play

### Added
- Dedicated `Context` per announcement, passed to every `volume_set` /
  `tts.speak` / `media_stop` call; `context.id` stored in the last result.
- 20 s state-change audit listener that classifies unexpected media players
  (started but not targeted by this integration) and logs them at WARNING.
- `targeted` and `unexpected_started` in the `speak` response and in
  `diagnostics.py` / `tts_broadcast.debug_selection`.
- Registry hygiene warnings for stale or duplicate switch mappings.
- `tts_broadcast.debug_selection` diagnostic service (no side effects, no
  speech).

## [1.1.2] - Follow-up 4

### Fixed
- `tts.speak` is called once per speaker (`media_player_entity_id: [speaker]`)
  concurrently with `asyncio.gather(return_exceptions=True)`; a failing speaker
  never marks the others as failed.
- `volume_set` runs concurrently per speaker; a volume failure does not block
  TTS.
- Response keeps `played` / `skipped` / `failed` and adds `errors`
  `{entity_id: short error text}`. "played" means HA accepted the request.
- One info log per announcement with entity ids only (never message text);
  warning per failed speaker with exception type + message; debug timing.
- Last announcement result stored in `runtime_data` and returned by
  `diagnostics.py`.
- New optional `cache` field (bool, default false) for `tts.speak`.
- Volume slider is now the single source of truth
  (`runtime_data.volume`, synced from `async_set_native_value` and restored
  state). Precedence: service `volume` argument > slider value > options
  "Initial volume".
- Options field "Default volume" relabeled to "Initial volume" (en/vi).
- Empty `blueprints/` folder removed from the integration.

### Added
- Tests: one speaker failing does not stop the others; response shape;
  `volume_set` skip for no-volume speakers; unavailable speaker skipped;
  diagnostics contains the last result; slider value used / overridden /
  restored after reload.

## [1.1.1] - Follow-up 3

### Fixed
- Voice phrases options step could never be saved: validation split into
  per-step sections (`_validate_speakers_section` / `_validate_voice_section`);
  cleared optional fields are removed (not preserved); fallback agent cannot be
  the integration's own conversation entity (validation + runtime guard).
- Wrong spoken replies: reply keys mapped to a localized en/vi table;
  `reply_text` overrides only the success reply.
- Fallback agent cannot be cleared fixed; fallback errors logged and answered
  with a localized reply instead of being swallowed.
- Static path / card JS registered once in `async_setup` (guarded by
  `hass.data[DOMAIN]["static_registered"]`), not removed on unload.
- Public `homeassistant.components.conversation` exports used
  (`ConversationEntity`, `async_converse`, `ConversationResult`).
- `options.error` added to en/vi translations; config step labels and
  descriptions added; `entity.switch.speaker.name` added to vi; conversation
  entity name translated; translation parity test added.
- Card: `assist_pipeline_id` uses the `assist_pipeline` selector; dashboard YAML
  emits `pipeline_id: preferred` and localized Assist name.
- Duplicate aliased imports removed; typed runtime data used throughout.
- Version bumped to 1.1.1.

## [1.1.0] - Built-in voice phrases and conversation agent

### Added
- Built-in conversation agent with phrase matching (strip / keep / require /
  accent-insensitive).
- Options flow with Speakers & TTS and Voice phrases steps.
- `tts_broadcast.speak` / `stop` / `get_dashboard_card` services.
- Dashboard card (`tts-broadcast-card`), brand icon, switch/number/text/button
  entities.
- Translations en/vi.
