# TTS Broadcast

A Home Assistant custom integration for broadcasting a TTS message to multiple media players.

## Manual installation (private repository)
1. Copy `custom_components/tts_broadcast` into `config/custom_components/tts_broadcast`, or unzip `dist/tts_broadcast.zip` into `config/custom_components/`.
2. Restart Home Assistant.
3. Add the integration from Settings -> Devices & Services.

## Installation via HACS (only if the repository is public)
1. Open HACS -> Integrations -> Custom repositories.
2. Add this repository URL and select category "Integration".
3. Install "TTS Broadcast" and restart Home Assistant.
4. Add the integration from Settings -> Devices & Services.

## Configuration
Configure entirely from the UI:
- TTS entity (`tts.wyoming_vietnamese`)
- Speakers (media players)
- Speakers without volume control
- Default volume
- Optional language and options
- Voice phrases: `strip_phrases` (remove prefix before speaking, e.g. "thông báo"), `keep_phrases` (keep whole sentence, e.g. "xin chào"), `require_phrase`, fallback agent, accent-insensitive matching, reply text.

## Entities
One device "TTS Broadcast" with:
- One switch per speaker
- One shared volume number
- One message text
- Speak, Stop, Select all, Select none buttons
- One conversation agent (Assist)

## Services
### `tts_broadcast.speak`
```yaml
service: tts_broadcast.speak
data:
  message: "Hello everyone"
```
Optional: `speakers`, `volume`, `language`, `options`.

### `tts_broadcast.stop`
```yaml
service: tts_broadcast.stop
```

## Blueprint
Import `blueprints/automation/tts_broadcast/voice_announce.yaml` manually in Home Assistant. Configure trigger sentences such as `thông báo {message}`.

## Dashboard snippet
```yaml
type: entities
entities:
  - switch.tts_broadcast_media_player_speaker_one
  - number.tts_broadcast_volume
  - text.tts_broadcast_message
  - button.tts_broadcast_speak
  - button.tts_broadcast_stop
```
Assist button example:
```yaml
type: button
name: Assist
tap_action:
  action: assist
  pipeline_id: preferred
  start_listening: true
```
Speak button with message:
```yaml
type: button
name: Speak
tap_action:
  action: perform-action
  perform_action: tts_broadcast.speak
  data:
    message: "Hello"
```

## Dashboard card
The integration serves a custom card `tts-broadcast-card`. After installation, hard-refresh the browser. In the dashboard editor, Add card -> TTS Broadcast. The card discovers entities automatically.

Card options (all optional): `title`, `show_volume`, `show_message`, `show_assist`, `assist_pipeline_id` (defaults to `preferred`), `show_select_buttons`.

YAML fallback:
```yaml
service: tts_broadcast.get_dashboard_card
data:
  notify: true
```

## Version
v1.1.1: fixed the Voice phrases options step cannot be saved, fallback clear/self-recursion, wrong spoken replies, static path registration, translations, and dashboard card pipeline picker.

## Known limitations
- ESPHome announcement interruption via `media_stop` is unverified.
- Tapo speaker compatibility depends on the device.
- With an LLM conversation agent, sentence triggers may require "Prefer handling commands locally"; unverified.