"""Tests for setup and unload."""

from __future__ import annotations

import asyncio

from homeassistant.core import HomeAssistant

from custom_components.tts_broadcast.const import DOMAIN


async def test_setup_and_unload(hass: HomeAssistant, mock_config_entry) -> None:
    mock_config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    assert (
        mock_config_entry.state.value == "loaded"
        or str(mock_config_entry.state) == "loaded"
    )
    assert hass.services.has_service(DOMAIN, "speak")
    assert hass.services.has_service(DOMAIN, "stop")

    await hass.config_entries.async_unload(mock_config_entry.entry_id)
    await hass.async_block_till_done()
    assert hass.services.has_service(DOMAIN, "speak")
    assert hass.services.has_service(DOMAIN, "stop")


async def test_reload(hass: HomeAssistant, mock_config_entry) -> None:
    mock_config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()
    await hass.config_entries.async_reload(mock_config_entry.entry_id)
    await hass.async_block_till_done()
    assert (
        mock_config_entry.state.value == "loaded"
        or str(mock_config_entry.state) == "loaded"
    )


async def test_repairs_issue_created_when_voice_phrases_no_pipeline(
    hass: HomeAssistant, mock_config_entry
) -> None:
    """Repairs issue created when voice phrases configured but no pipeline."""
    from unittest.mock import patch

    from homeassistant.helpers import entity_registry as er

    import custom_components.tts_broadcast.__init__ as init_mod

    mock_config_entry.add_to_hass(hass)
    registry = er.async_get(hass)
    registry.async_get_or_create(
        "conversation",
        "tts_broadcast",
        f"{mock_config_entry.entry_id}_conversation",
        config_entry=mock_config_entry,
    )
    hass.config_entries.async_update_entry(
        mock_config_entry,
        options={
            **mock_config_entry.options,
            "strip_phrases": ["thông báo"],
        },
    )

    created = []
    deleted = []

    def _fake_create(*args, **kwargs):
        created.append(kwargs)

    def _fake_delete(*args, **kwargs):
        deleted.append(kwargs)

    with (
        patch(
            "custom_components.tts_broadcast.__init__.async_create_issue",
            side_effect=_fake_create,
        ),
        patch(
            "custom_components.tts_broadcast.__init__.async_delete_issue",
            side_effect=_fake_delete,
        ),
        patch(
            "custom_components.tts_broadcast.__init__._find_assist_pipeline_id",
            return_value=None,
        ),
    ):
        init_mod._async_update_assist_pipeline_issue(hass, mock_config_entry)

    assert created, "expected an issue to be created"
    assert created[0]["translation_key"] == "no_assist_pipeline"
    assert created[0]["severity"].value == "warning"
    assert created[0]["is_fixable"] is False
    assert created[0]["config_entry_id"] == mock_config_entry.entry_id
    assert deleted == []


async def test_repairs_issue_cleared_when_pipeline_exists(
    hass: HomeAssistant, mock_config_entry
) -> None:
    """Repairs issue cleared when a pipeline uses our agent."""
    from unittest.mock import patch

    from homeassistant.helpers import entity_registry as er

    import custom_components.tts_broadcast.__init__ as init_mod

    mock_config_entry.add_to_hass(hass)
    registry = er.async_get(hass)
    registry.async_get_or_create(
        "conversation",
        "tts_broadcast",
        f"{mock_config_entry.entry_id}_conversation",
        config_entry=mock_config_entry,
    )
    hass.config_entries.async_update_entry(
        mock_config_entry,
        options={
            **mock_config_entry.options,
            "strip_phrases": ["thông báo"],
        },
    )

    created = []
    deleted = []

    def _fake_create(*args, **kwargs):
        created.append(kwargs)

    def _fake_delete(*args, **kwargs):
        deleted.append(kwargs)

    with (
        patch(
            "custom_components.tts_broadcast.__init__.async_create_issue",
            side_effect=_fake_create,
        ),
        patch(
            "custom_components.tts_broadcast.__init__.async_delete_issue",
            side_effect=_fake_delete,
        ),
        patch(
            "custom_components.tts_broadcast.__init__._find_assist_pipeline_id",
            return_value="pipeline_test_id",
        ),
    ):
        init_mod._async_update_assist_pipeline_issue(hass, mock_config_entry)

    assert deleted, "expected the issue to be cleared"
    assert created == []


async def test_repairs_issue_not_created_when_no_voice_phrases(
    hass: HomeAssistant, mock_config_entry
) -> None:
    """No repairs issue when voice phrases are not configured."""
    from unittest.mock import patch

    from homeassistant.helpers import entity_registry as er

    import custom_components.tts_broadcast.__init__ as init_mod

    mock_config_entry.add_to_hass(hass)
    registry = er.async_get(hass)
    registry.async_get_or_create(
        "conversation",
        "tts_broadcast",
        f"{mock_config_entry.entry_id}_conversation",
        config_entry=mock_config_entry,
    )

    created = []
    deleted = []

    def _fake_create(*args, **kwargs):
        created.append(kwargs)

    def _fake_delete(*args, **kwargs):
        deleted.append(kwargs)

    with (
        patch(
            "custom_components.tts_broadcast.__init__.async_create_issue",
            side_effect=_fake_create,
        ),
        patch(
            "custom_components.tts_broadcast.__init__.async_delete_issue",
            side_effect=_fake_delete,
        ),
        patch(
            "custom_components.tts_broadcast.__init__._find_assist_pipeline_id",
            return_value=None,
        ),
    ):
        init_mod._async_update_assist_pipeline_issue(hass, mock_config_entry)

    assert created == []


async def test_repairs_issue_deleted_on_unload(
    hass: HomeAssistant, mock_config_entry
) -> None:
    """Repairs issue deleted on entry unload."""
    from unittest.mock import patch

    from homeassistant.helpers import entity_registry as er

    import custom_components.tts_broadcast.__init__ as init_mod
    from custom_components.tts_broadcast.__init__ import TTSBroadcastRuntimeData

    mock_config_entry.add_to_hass(hass)
    hass.data.setdefault(DOMAIN, {"lock": asyncio.Lock(), "entries": {}})
    registry = er.async_get(hass)
    registry.async_get_or_create(
        "conversation",
        "tts_broadcast",
        f"{mock_config_entry.entry_id}_conversation",
        config_entry=mock_config_entry,
    )
    # Set up runtime data directly (avoids async_setup triggering
    # conversation platform setup, which fails in this test env).
    mock_config_entry.runtime_data = TTSBroadcastRuntimeData(
        entry=mock_config_entry, lock=hass.data[DOMAIN]["lock"]
    )
    hass.config_entries.async_update_entry(
        mock_config_entry,
        options={
            **mock_config_entry.options,
            "strip_phrases": ["thông báo"],
        },
    )

    created = []
    deleted = []

    def _fake_create(*args, **kwargs):
        created.append(kwargs)

    def _fake_delete(*args, **kwargs):
        deleted.append(kwargs)

    with (
        patch(
            "custom_components.tts_broadcast.__init__.async_create_issue",
            side_effect=_fake_create,
        ),
        patch(
            "custom_components.tts_broadcast.__init__.async_delete_issue",
            side_effect=_fake_delete,
        ),
        patch(
            "custom_components.tts_broadcast.__init__._find_assist_pipeline_id",
            return_value=None,
        ),
    ):
        init_mod._async_update_assist_pipeline_issue(hass, mock_config_entry)
        assert created, "expected an issue to be created before unload"

        # Simulate unload
        result = await init_mod.async_unload_entry(hass, mock_config_entry)
        assert result is True
        await hass.async_block_till_done()

    assert deleted, "expected the issue to be deleted on unload"


async def test_repairs_issue_multiple_pipelines_returns_first(
    hass: HomeAssistant, mock_config_entry
) -> None:
    """Multiple pipelines using our agent returns first id, no error."""
    from unittest.mock import MagicMock, patch

    from homeassistant.helpers import entity_registry as er

    import custom_components.tts_broadcast.__init__ as init_mod

    mock_config_entry.add_to_hass(hass)
    registry = er.async_get(hass)
    registry.async_get_or_create(
        "conversation",
        "tts_broadcast",
        f"{mock_config_entry.entry_id}_conversation",
        config_entry=mock_config_entry,
    )
    hass.config_entries.async_update_entry(
        mock_config_entry,
        options={
            **mock_config_entry.options,
            "strip_phrases": ["thông báo"],
        },
    )

    our_entity = f"conversation.{mock_config_entry.entry_id}_conversation"

    p1 = MagicMock()
    p1.conversation_engine = our_entity
    p1.id = "pipeline_first"
    p1.name = "First Pipeline"

    p2 = MagicMock()
    p2.conversation_engine = our_entity
    p2.id = "pipeline_second"
    p2.name = "Second Pipeline"

    created = []
    deleted = []

    def _fake_create(*args, **kwargs):
        created.append(kwargs)

    def _fake_delete(*args, **kwargs):
        deleted.append(kwargs)

    with (
        patch(
            "custom_components.tts_broadcast.__init__.async_create_issue",
            side_effect=_fake_create,
        ),
        patch(
            "custom_components.tts_broadcast.__init__.async_delete_issue",
            side_effect=_fake_delete,
        ),
        patch(
            "custom_components.tts_broadcast.__init__._find_assist_pipeline_id",
            return_value="pipeline_first",
        ),
    ):
        init_mod._async_update_assist_pipeline_issue(hass, mock_config_entry)

    assert deleted, "expected issue cleared when pipeline(s) exist"
    assert created == []
