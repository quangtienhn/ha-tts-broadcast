# Testing

## Automated

- `ruff check .`
- `ruff format --check .`
- `pytest tests`

## Manual checklist (real Home Assistant, v1.1.3)

- (a) Configure -> Voice phrases -> change a phrase -> Submit works and the entry reloads.
- (b) Set a fallback agent, then clear it, and confirm it is really cleared.
- (c) Selecting the TTS Broadcast agent as its own fallback is rejected.
- (d) "thông báo" alone gets a spoken request for content, never "missing_content".
- (e) With `reply_text` set and no speaker selected, the assistant does NOT claim it sent.
- (f) After changing options, the card is still in the card picker without restarting HA.

## Extra speakers play — runbook

If more speakers play than the one you selected:

1. Call `tts_broadcast.debug_selection` from Developer Tools and read the output.
2. Turn exactly one switch ON, call `tts_broadcast.speak` with `return_response`, and compare `targeted` (exact list sent to tts.speak) with `unexpected_started`.
3. If `unexpected_started` is empty and `targeted` has exactly one entity but other speakers still play, the cause is OUTSIDE this integration: check the Logbook for who started those players, list automations/scripts that call `tts.speak` or `media_player.play_media`, and look for the old YAML package (script `loa_phat_tts`, the "Assist - thông báo ra loa" automation, `input_boolean.loa_*`).
4. If `targeted` has more than one entity, send the full `debug_selection` output, the switch states, and the integration log lines.

## Manual hardware checklist

1. Call `tts_broadcast.speak` from Developer Tools with a message.
2. Type a sentence in Assist using the configured trigger phrase.
3. Speak a sentence through Assist.
4. Press Stop during a long message and observe whether ESPHome announcement playback stops.
5. Restart Home Assistant and verify restored switch, volume and message states; nothing speaks automatically.
6. Disable one speaker and confirm the remaining speakers still play.
7. Card appears in picker after hard browser refresh.
8. Card renders all speakers and toggles/volume/message/Speak/Stop/Assist work.
9. Add a speaker in options flow and confirm card updates without edits.
10. Brand icon visible in Devices & services.
11. YAML generator output pastes and works.
