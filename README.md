# TTS Broadcast

**English** | [Tiếng Việt](./README.vi.md)

A Home Assistant custom integration to broadcast a spoken or typed TTS announcement
to multiple speakers at once. Pick speakers with switches, share a volume slider,
trigger by voice through Assist, and control everything from a dashboard card — all
local, with no cloud dependency of its own.

> **Note:** This repository is currently PRIVATE. Until it is public, install
> manually by copying the folder (see Installation). Do not change the repository
> visibility yourself; see `PUBLISH_CHECKLIST.md` for the release process.

## What it is and why

TTS Broadcast lets you announce a message on several speakers in one go. A common
use case is a Vietnamese smart-home announcement such as "thông báo, cơm chín rồi"
(dinner is ready). You configure one or more media-player speakers, choose which are
switched on, set a shared volume, and speak or type the message through Assist.

## Features and what it deliberately does not do

**Features**

- Announce one message to many speakers at once.
- Per-speaker on/off switches (only switched-on speakers play).
- Shared volume slider ("Initial volume" is only the starting value).
- Voice trigger through Assist: a sentence such as "thông báo {message}" is spoken
  only to the switched-on speakers.
- Custom dashboard card (`tts-broadcast-card`) with per-speaker switches, volume,
  message, Speak/Stop/Select buttons and a localized TALK (Assist) row.
- Services: `tts_broadcast.speak`, `tts_broadcast.stop`,
  `tts_broadcast.get_dashboard_card`, `tts_broadcast.debug_selection`.
- Fully local when you use a local TTS engine (e.g. Wyoming); no cloud dependency of
  its own.

**Deliberately does not do**

- It does not stream your real voice. Speech is converted to text and re-spoken by
  TTS.
- No per-speaker volume (one shared volume).
- No custom frontend beyond the card.
- No streaming audio between devices.

## Requirements

- Home Assistant **2025.1 or newer** (runtime verification was performed on
  HA 2026.10.4, the 2026.11 line).
- A TTS entity (e.g. `tts.wyoming_vietnamese`).
- `media_player` speakers that can play TTS.
- Optional: an STT engine for voice trigger through Assist.

## Installation

### Manual (works now; repository is private)

1. Copy `custom_components/tts_broadcast` into
   `config/custom_components/tts_broadcast`, or unzip
   `dist/tts_broadcast.zip` into `config/custom_components/`.
2. Restart Home Assistant.
3. Add the integration from Settings -> Devices & Services.

### HACS (only after the repository goes public)

1. HACS -> Integrations -> Custom repositories.
2. Add this repository URL, category "Integration".
3. Install "TTS Broadcast" and restart Home Assistant.
4. Add the integration from Settings -> Devices & Services.

## Configuration

Everything is configured from the UI (Settings -> Devices & Services -> TTS Broadcast
-> Configure).

| Field | Meaning | Example |
|-------|---------|---------|
| TTS entity | The TTS engine used to speak | `tts.wyoming_vietnamese` |
| Speakers | Media players that may announce | `media_player.living_room`, … |
| Speakers without volume control | Speakers excluded from `volume_set` | `media_player.porch` |
| Initial volume | Starting volume before the slider has a stored state | `50` |
| Language / options | Optional language/options passed to TTS | `vi` / `{}` |
| Strip phrases | Phrases removed from the start before speaking | `thông báo` |
| Keep phrases | Phrases that keep the whole sentence unchanged | `xin chào` |
| Require phrase | If disabled, every sentence is broadcast | enabled |
| Fallback agent | Assist agent used when no phrase matches | another conversation agent |
| Accent insensitive | Ignore Vietnamese diacritics when matching | enabled |
| Reply text | Short confirmation returned to Assist | `Đã gửi` |
| Playback mode | `per_speaker` (default) or `single_call` | `per_speaker` |
| Audit all media players | Observe every media player during the audit window | disabled |

Phrase examples: strip `thông báo` so "thông báo, cơm chín rồi" speaks only
"cơm chín rồi"; keep `xin chào` so "xin chào mọi người xuống ăn cơm" is spoken
whole.

## Entities and services

One device "TTS Broadcast" with one switch per speaker, one shared volume number,
one message text, Speak/Stop/Select all/Select none buttons, and one conversation
agent.

### `tts_broadcast.speak`

```yaml
service: tts_broadcast.speak
data:
  message: "Cơm chín rồi, mọi người xuống ăn!"
  speakers: ["media_player.living_room"]   # optional
  volume: 70                                # optional, 0-100
  language: vi                              # optional
  cache: false                              # optional
  audit: true                               # optional, wait for audit details
```

Response shape: `{played, skipped, failed, errors, targeted, unexpected_started,
context_id}`.

- `played`: speakers HA accepted the request for — **"accepted" does not mean
  audible**.
- `skipped`: unavailable/unknown speakers.
- `failed`: speakers that errored.
- `errors`: `{entity_id: short error text}`.
- `targeted`: the exact list sent to `tts.speak`.
- `unexpected_started`: media players that started playing but were not targeted
  (only filled when `audit: true`; otherwise see `debug_selection`/diagnostics).

### `tts_broadcast.stop`

```yaml
service: tts_broadcast.stop
data:
  speakers: ["media_player.living_room"]  # optional
```

### `tts_broadcast.get_dashboard_card`

```yaml
service: tts_broadcast.get_dashboard_card
data:
  notify: true
```

Returns a YAML snippet for a stock entities card (also creates a persistent
notification when `notify: true`).

### `tts_broadcast.debug_selection`

No side effects, no speech. Returns per-speaker state, the resolved list that a
`speak` without arguments would use, any media player listing a configured speaker
as a group member, and the last announcement audit. Use this to prove why extra
speakers play.

## Voice setup, step by step (read the pitfall first)

**Pitfall:** do not use the default Assist pipeline for the TALK button. The
default pipeline usually uses an LLM/Home Assistant conversation agent, and HA
will route the announcement to `assist_satellite.announce` on ALL Assist
satellites — so every speaker plays, not just the ones you switched on.

1. Settings -> Voice assistants -> Add assistant.
2. Choose conversation agent: **TTS Broadcast**.
3. Choose your STT engine and your TTS engine.
4. Save the pipeline. Do **not** make it the default pipeline.
5. Note its pipeline id.

In the dashboard card, set `assist_pipeline_id` to that id. Or leave it as
`auto` (the default): the card finds the pipeline whose conversation agent is the
TTS Broadcast agent automatically.

If no pipeline uses the TTS Broadcast agent, the TALK row is hidden and an info
line tells you to create one.

## Dashboard card

Add card -> TTS Broadcast. The card discovers the integration's entities
automatically.

Card options (all optional):

| Option | Meaning | Default |
|--------|---------|---------|
| title | Card title | `TTS Broadcast` |
| show_volume | Show the volume slider | true |
| show_message | Show the message text | true |
| show_assist | Show the TALK (Assist) row | true |
| assist_pipeline_id | `auto`, `preferred`, `last_used`, or a concrete pipeline id | `auto` |
| assist_name | Override the TALK button label | `TALK` / `NÓI` |
| assist_icon | Override the TALK button icon | `mdi:microphone` |
| show_select_buttons | Show Select all / Select none | true |

YAML fallback (stock entities card):

```yaml
service: tts_broadcast.get_dashboard_card
data:
  notify: true
```

After install or update, hard-refresh the browser so the card JS is re-cached.

If no Assist pipeline uses the TTS Broadcast agent, no TALK row is rendered and a
localized info line is shown instead.

## Troubleshooting

| Problem | What to check |
|---------|---------------|
| All speakers play when I talk | You are using the default Assist pipeline (an LLM/Home Assistant agent routes to all satellites). Create a dedicated pipeline with conversation agent = TTS Broadcast and set `assist_pipeline_id` to its id. Use Developer Tools > Events > `call_service` to see who called `assist_satellite.announce` or `tts.speak`. |
| No microphone button | The pipeline needs an STT engine. The browser page must be HTTPS, or use the Home Assistant Companion app. The conversation entity's own chat dialog is text-only by design. |
| Some speakers quiet or silent | Check the volume slider and the speaker's own volume. Speakers in "Speakers without volume control" get no `volume_set`. Test the speaker directly with `tts_broadcast.speak`. |
| Extra speakers play | Call `tts_broadcast.debug_selection` and compare `targeted` vs `unexpected_started`. See the runbook below. |
| Card missing from picker | Hard-refresh the browser after install/update. |
| Configure error | Check the options error translation (e.g. "Select at least one speaker"). |
| Stop does not interrupt some ESPHome speakers | `media_player.media_stop` interruption on ESPHome announcement pipelines is unverified (see Known limitations). |

### Extra speakers play — runbook

1. Call `tts_broadcast.debug_selection` and read the output.
2. Turn exactly one switch ON, call `tts_broadcast.speak` with `return_response`,
   and compare `targeted` (exact list sent to `tts.speak`) with
   `unexpected_started`.
3. If `unexpected_started` is empty and `targeted` has one entity but other
   speakers still play, the cause is outside this integration: check the Logbook
   for who started those players, list automations/scripts that call
   `tts.speak` or `media_player.play_media`, and check for the old YAML package
   (script `loa_phat_tts`, the "Assist - thông báo ra loa" automation,
   `input_boolean.loa_*`).
4. If `targeted` has more than one entity, send the full `debug_selection`
   output, the switch states, and the integration log lines.

## Known limitations and verification status

| Item | Status |
|------|--------|
| Per-speaker playback (one failing speaker never blocks others) | Verified by automated tests |
| `tts.speak` once per speaker, concurrently | Verified by automated tests |
| Volume slider as single source of truth | Verified by automated tests |
| `debug_selection` / audit / `unexpected_started` | Verified by automated tests |
| Card auto pipeline selection | Verified by automated tests (JS logic via node --check) |
| HA 2026.11 line, ESPHome speaker media players | Verified on the author's HA 2026.10.4 |
| Assist pipeline with a local Wyoming TTS/STT | Verified on the author's HA 2026.10.4 |
| Tapo speaker behavior | Not tested |
| Other TTS engines | Not tested |
| Other HA versions | Not tested (minimum declared 2025.1, assumed compatible) |
| ESPHome announcement interruption via `media_stop` | Not tested |
| Frontend visual editor `assist_pipeline` selector | Not tested locally (backend verified) |

## Privacy and security

- Message text is never logged at info level.
- No telemetry, no external calls from the integration.
- Anyone who can reach an Assist pipeline using the TTS Broadcast agent can speak
  on your speakers — protect your pipeline access.
- Not affiliated with or endorsed by Home Assistant, Nabu Casa, Tapo/TP-Link,
  Zalo, or Google.

## Development

```bash
ruff check .
ruff format --check .
pytest tests
```

See `CONTRIBUTING.md`, `SECURITY.md`, `CODE_OF_CONDUCT.md`, and
`PUBLISH_CHECKLIST.md`. Screenshots to add are listed in `docs/images/README.md`.

License: MIT. See `LICENSE`.
