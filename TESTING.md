# Testing

## Automated
- `ruff check .`
- `ruff format --check .`
- `pytest tests`

## Manual hardware checklist
1. Call `tts_broadcast.speak` from Developer Tools with a message.
2. Type a sentence in Assist using the configured trigger phrase.
3. Speak a sentence through Assist.
4. Press Stop during a long message and observe whether ESPHome announcement playback stops.
5. Restart Home Assistant and verify restored switch, volume and message states; nothing speaks automatically.
6. Disable one speaker and confirm the remaining speakers still play.