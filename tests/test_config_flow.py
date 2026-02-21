"""Test the HBX Controls config flow."""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from homeassistant.const import CONF_PASSWORD, CONF_USERNAME

from custom_components.hbx_controls.config_flow import (
    CannotConnect,
    ConfigFlow,
    InvalidAuth,
    OptionsFlowHandler,
    validate_input,
)
from custom_components.hbx_controls.const import (
    CONF_SCAN_INTERVAL,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
    ERROR_AUTH_FAILED,
    ERROR_CANNOT_CONNECT,
    ERROR_UNKNOWN,
)


VALID_USER_INPUT = {
    CONF_USERNAME: "test@example.com",
    CONF_PASSWORD: "test_password",
    CONF_SCAN_INTERVAL: DEFAULT_SCAN_INTERVAL,
}


# ---------------------------------------------------------------------------
# validate_input tests
# ---------------------------------------------------------------------------


async def test_validate_input_success(hass):
    """Test validate_input succeeds with valid credentials."""
    mock_sensorlinx = AsyncMock()
    mock_sensorlinx.login = AsyncMock()

    with patch(
        "custom_components.hbx_controls.config_flow.Sensorlinx",
        return_value=mock_sensorlinx,
    ):
        result = await validate_input(hass, VALID_USER_INPUT)

    assert result["title"] == f"HBX Controls ({VALID_USER_INPUT[CONF_USERNAME]})"
    mock_sensorlinx.login.assert_called_once()


async def test_validate_input_login_failure(hass):
    """Test validate_input raises CannotConnect on login failure."""
    mock_sensorlinx = AsyncMock()
    mock_sensorlinx.login = AsyncMock(side_effect=Exception("Connection error"))

    with (
        patch(
            "custom_components.hbx_controls.config_flow.Sensorlinx",
            return_value=mock_sensorlinx,
        ),
        pytest.raises(CannotConnect),
    ):
        await validate_input(hass, VALID_USER_INPUT)


# ---------------------------------------------------------------------------
# ConfigFlow user step tests
# ---------------------------------------------------------------------------


async def test_step_user_form_shown(hass):
    """Test the initial form is shown when no user input."""
    flow = ConfigFlow()
    flow.hass = hass
    flow.context = {}

    result = await flow.async_step_user(user_input=None)

    assert result["type"] == "form"
    assert result["step_id"] == "user"


async def test_step_user_creates_entry(hass):
    """Test a successful submission creates a config entry."""
    flow = ConfigFlow()
    flow.hass = hass
    flow.context = {}
    flow.async_set_unique_id = AsyncMock()
    flow._abort_if_unique_id_configured = MagicMock()

    with patch(
        "custom_components.hbx_controls.config_flow.validate_input",
        return_value={"title": f"HBX Controls ({VALID_USER_INPUT[CONF_USERNAME]})"},
    ):
        result = await flow.async_step_user(user_input=VALID_USER_INPUT)

    assert result["type"] == "create_entry"
    assert result["title"] == f"HBX Controls ({VALID_USER_INPUT[CONF_USERNAME]})"
    assert result["data"] == VALID_USER_INPUT


async def test_step_user_cannot_connect(hass):
    """Test we handle cannot connect error."""
    flow = ConfigFlow()
    flow.hass = hass
    flow.context = {}

    with patch(
        "custom_components.hbx_controls.config_flow.validate_input",
        side_effect=CannotConnect,
    ):
        result = await flow.async_step_user(user_input=VALID_USER_INPUT)

    assert result["type"] == "form"
    assert result["errors"] == {"base": ERROR_CANNOT_CONNECT}


async def test_step_user_invalid_auth(hass):
    """Test we handle invalid auth error."""
    flow = ConfigFlow()
    flow.hass = hass
    flow.context = {}

    with patch(
        "custom_components.hbx_controls.config_flow.validate_input",
        side_effect=InvalidAuth,
    ):
        result = await flow.async_step_user(user_input=VALID_USER_INPUT)

    assert result["type"] == "form"
    assert result["errors"] == {"base": ERROR_AUTH_FAILED}


async def test_step_user_unknown_error(hass):
    """Test we handle unexpected exceptions."""
    flow = ConfigFlow()
    flow.hass = hass
    flow.context = {}

    with patch(
        "custom_components.hbx_controls.config_flow.validate_input",
        side_effect=RuntimeError("something broke"),
    ):
        result = await flow.async_step_user(user_input=VALID_USER_INPUT)

    assert result["type"] == "form"
    assert result["errors"] == {"base": ERROR_UNKNOWN}


# ---------------------------------------------------------------------------
# OptionsFlowHandler tests
# ---------------------------------------------------------------------------


async def test_options_flow_form_shown(hass):
    """Test the options form is shown when no user input."""
    entry = MagicMock()
    entry.data = VALID_USER_INPUT
    entry.options = {}

    flow = OptionsFlowHandler(entry)
    flow.hass = hass

    result = await flow.async_step_init(user_input=None)

    assert result["type"] == "form"
    assert result["step_id"] == "init"


async def test_options_flow_updates_with_same_credentials(hass):
    """Test options flow when credentials haven't changed (no re-validation)."""
    entry = MagicMock()
    entry.data = dict(VALID_USER_INPUT)
    entry.options = {}

    flow = OptionsFlowHandler(entry)
    flow.hass = hass

    # Same credentials, just update scan interval
    new_input = dict(VALID_USER_INPUT)
    new_input[CONF_SCAN_INTERVAL] = 600

    result = await flow.async_step_init(user_input=new_input)

    assert result["type"] == "create_entry"


async def test_options_flow_validates_new_credentials(hass):
    """Test options flow re-validates when credentials change."""
    entry = MagicMock()
    entry.data = dict(VALID_USER_INPUT)
    entry.options = {}

    flow = OptionsFlowHandler(entry)
    flow.hass = hass

    new_input = {
        CONF_USERNAME: "new@example.com",
        CONF_PASSWORD: "new_password",
        CONF_SCAN_INTERVAL: DEFAULT_SCAN_INTERVAL,
    }

    with patch(
        "custom_components.hbx_controls.config_flow.validate_input",
        return_value={"title": "HBX Controls (new@example.com)"},
    ):
        result = await flow.async_step_init(user_input=new_input)

    assert result["type"] == "create_entry"


async def test_options_flow_cannot_connect_new_credentials(hass):
    """Test options flow handles cannot connect when credentials change."""
    entry = MagicMock()
    entry.data = dict(VALID_USER_INPUT)
    entry.options = {}

    flow = OptionsFlowHandler(entry)
    flow.hass = hass

    new_input = {
        CONF_USERNAME: "new@example.com",
        CONF_PASSWORD: "new_password",
        CONF_SCAN_INTERVAL: DEFAULT_SCAN_INTERVAL,
    }

    with patch(
        "custom_components.hbx_controls.config_flow.validate_input",
        side_effect=CannotConnect,
    ):
        result = await flow.async_step_init(user_input=new_input)

    assert result["type"] == "form"
    assert result["errors"] == {"base": ERROR_CANNOT_CONNECT}
