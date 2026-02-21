"""Tests for the HBX Controls integration setup (__init__.py)."""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant

from custom_components.hbx_controls import (
    PLATFORMS,
    async_setup_entry,
    async_unload_entry,
)
from custom_components.hbx_controls.const import DOMAIN

from .conftest import (
    MOCK_DEVICE_ID,
    MOCK_USERNAME,
    make_coordinator_data,
)


# ---------------------------------------------------------------------------
# async_setup_entry tests
# ---------------------------------------------------------------------------


async def test_setup_entry_creates_coordinator(
    hass: HomeAssistant, mock_config_entry, mock_setup_coordinator
):
    """Test setup_entry creates coordinator and stores it in hass.data."""
    result = await async_setup_entry(hass, mock_config_entry)

    assert result is True
    assert DOMAIN in hass.data
    assert mock_config_entry.entry_id in hass.data[DOMAIN]


async def test_setup_entry_forwards_platforms(
    hass: HomeAssistant, mock_config_entry, mock_setup_coordinator
):
    """Test setup_entry forwards to all 6 platforms."""
    with patch.object(
        hass.config_entries, "async_forward_entry_setups", new_callable=AsyncMock
    ) as mock_forward:
        await async_setup_entry(hass, mock_config_entry)

    mock_forward.assert_called_once_with(mock_config_entry, PLATFORMS)


async def test_platforms_list():
    """Test PLATFORMS includes all expected platforms."""
    from homeassistant.const import Platform

    assert Platform.SENSOR in PLATFORMS
    assert Platform.BINARY_SENSOR in PLATFORMS
    assert Platform.CLIMATE in PLATFORMS
    assert Platform.NUMBER in PLATFORMS
    assert Platform.SWITCH in PLATFORMS
    assert Platform.SELECT in PLATFORMS
    assert len(PLATFORMS) == 6


# ---------------------------------------------------------------------------
# async_unload_entry tests
# ---------------------------------------------------------------------------


async def test_unload_entry(
    hass: HomeAssistant, mock_config_entry, mock_setup_coordinator
):
    """Test unload_entry removes coordinator from hass.data and shuts down."""
    await async_setup_entry(hass, mock_config_entry)

    mock_setup_coordinator.async_shutdown = AsyncMock()

    with patch.object(
        hass.config_entries,
        "async_unload_platforms",
        new_callable=AsyncMock,
        return_value=True,
    ):
        result = await async_unload_entry(hass, mock_config_entry)

    assert result is True
    assert mock_config_entry.entry_id not in hass.data.get(DOMAIN, {})
    mock_setup_coordinator.async_shutdown.assert_called_once()


async def test_unload_entry_failure(
    hass: HomeAssistant, mock_config_entry, mock_setup_coordinator
):
    """Test unload_entry returns False when platform unload fails."""
    await async_setup_entry(hass, mock_config_entry)

    with patch.object(
        hass.config_entries,
        "async_unload_platforms",
        new_callable=AsyncMock,
        return_value=False,
    ):
        result = await async_unload_entry(hass, mock_config_entry)

    assert result is False
    # Coordinator should NOT have been removed from hass.data
    assert mock_config_entry.entry_id in hass.data[DOMAIN]
