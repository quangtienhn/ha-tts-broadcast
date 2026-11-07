"""Tests that every registered service is declared in services.yaml and translations."""

from __future__ import annotations

import json
from pathlib import Path

import yaml
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.tts_broadcast.const import DOMAIN

ROOT = Path(__file__).resolve().parents[1]
INTEGRATION = ROOT / "custom_components" / "tts_broadcast"
TRANS = INTEGRATION / "translations"


def _load_yaml(path: Path) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


async def test_registered_services_have_yaml_and_translations(
    hass: HomeAssistant, mock_config_entry: MockConfigEntry
) -> None:
    mock_config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    services_yaml = _load_yaml(INTEGRATION / "services.yaml")
    en = json.loads((TRANS / "en.json").read_text(encoding="utf-8"))
    vi = json.loads((TRANS / "vi.json").read_text(encoding="utf-8"))

    en_services = en.get("services", {})
    vi_services = vi.get("services", {})

    for service_id in hass.services.async_services().get(DOMAIN, {}):
        assert service_id in services_yaml, f"services.yaml missing {service_id}"
        assert service_id in en_services, f"en.json services missing {service_id}"
        assert service_id in vi_services, f"vi.json services missing {service_id}"
        svc_yaml = services_yaml[service_id] or {}
        yaml_fields = set((svc_yaml.get("fields") or {}).keys())
        en_fields = set((en_services[service_id].get("fields") or {}).keys())
        vi_fields = set((vi_services[service_id].get("fields") or {}).keys())
        msg = (
            f"{service_id}: yaml fields {sorted(yaml_fields)} != "
            f"en fields {sorted(en_fields)}"
        )
        assert yaml_fields == en_fields, msg
        msg = (
            f"{service_id}: yaml fields {sorted(yaml_fields)} != "
            f"vi fields {sorted(vi_fields)}"
        )
        assert yaml_fields == vi_fields, msg
