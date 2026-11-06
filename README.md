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

## Entities
One device "TTS Broadcast" with:
- One switch per speaker
- One shared volume number
- One message text
- Speak, Stop, Select all, Select none buttons

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

## Known limitations
- ESPHome announcement interruption via `media_stop` is unverified.
- Tapo speaker compatibility depends on the device.
- With an LLM conversation agent, sentence triggers may require "Prefer handling commands locally"; unverified.