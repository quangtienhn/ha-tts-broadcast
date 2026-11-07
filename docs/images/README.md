# Screenshots to add

This folder is intentionally empty in the repository. Before going public, the
repository owner should add the following screenshots here and reference them from
the README files (only reference an image if the file exists — see the broken-link
test in `tests/`).

Suggested screenshots:

1. `device-page.png` — TTS Broadcast device page in Settings -> Devices & Services
   (showing the per-speaker switches, volume, message, Speak/Stop buttons).
2. `card.png` — TTS Broadcast card on a dashboard, including the localized TALK
   (Assist) row.
3. `options-flow.png` — Options flow, Speakers & TTS step and Voice phrases step.
4. `assist-pipeline-setup.png` — Settings -> Voice assistants -> Add assistant,
   choosing conversation agent "TTS Broadcast".
5. `debug-view.png` — Developer Tools -> Services -> `tts_broadcast.debug_selection`
   result (sanitized).

**Redaction note:** Before publishing, remove or blur any personal information
from screenshots: real entity ids that reveal your house layout, real names of
people, device names, and any text that could identify your home. Prefer generic
examples such as `media_player.living_room_speaker`.

To reference an image from the README, use a relative link such as
`![Card](docs/images/card.png)` and only add it once the file exists. The
`test_readme_image_links` test fails on broken relative image links.
