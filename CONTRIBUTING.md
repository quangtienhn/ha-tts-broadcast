# Contributing to TTS Broadcast

Thanks for your interest in contributing to TTS Broadcast! This is a Home
Assistant custom integration that broadcasts TTS announcements to multiple
speakers, with a voice trigger through Assist.

## How to contribute

1. Fork the repository (once it is public) or work in a clone.
2. Create a branch from `main`.
3. Make your change, add or update tests, and keep commits small and focused.
4. Run the checks below and make sure they are green.
5. Open a pull request against `main` and describe what changed and why.

## Development setup

This integration is tested against Home Assistant Core 2026.10.4 (2026.11 line).

```bash
# Clone the repo into your HA config's custom_components folder, or run the
# test harness from this repository root.
python -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements_test.txt
```

## Checks

Run these before pushing:

```bash
ruff check .
ruff format --check .
pytest tests
```

Optionally validate the integration manifest with hassfest:

```bash
python -m script.hassfest --integration-path custom_components/tts_broadcast --core-path <path-to-home-assistant-core>
```

## Style

- Follow the existing code style (ruff, black-compatible formatting).
- Keep commits small and write a clear message.
- For every bug fix, add a regression test that fails first, then passes.
- All user-facing strings must have English and Vietnamese translations; run
  the translation parity test (`tests/test_translations.py`).

## License

MIT. See `LICENSE`.
