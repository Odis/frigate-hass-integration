"""Test the frigate binary sensor."""
from __future__ import annotations

import logging
from unittest.mock import AsyncMock

from pytest_homeassistant_custom_component.common import async_fire_mqtt_message

from custom_components.frigate.const import DOMAIN, NAME, VERSION
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr, entity_registry as er

from . import (
    TEST_BINARY_SENSOR_FRONT_DOOR_PERSON_MOTION_ENTITY_ID,
    TEST_BINARY_SENSOR_STEPS_PERSON_MOTION_ENTITY_ID,
    create_mock_frigate_client,
    setup_mock_frigate_config_entry,
)

_LOGGER = logging.getLogger(__package__)


async def test_binary_sensor_setup(hass: HomeAssistant) -> None:
    """Verify a successful binary sensor setup."""
    await setup_mock_frigate_config_entry(hass)

    entity_state = hass.states.get(
        TEST_BINARY_SENSOR_FRONT_DOOR_PERSON_MOTION_ENTITY_ID
    )
    assert entity_state
    assert entity_state.state == "unavailable"

    async_fire_mqtt_message(hass, "frigate/available", "online")
    await hass.async_block_till_done()
    entity_state = hass.states.get(
        TEST_BINARY_SENSOR_FRONT_DOOR_PERSON_MOTION_ENTITY_ID
    )
    assert entity_state
    assert entity_state.state == "off"

    async_fire_mqtt_message(hass, "frigate/front_door/person", "1")
    await hass.async_block_till_done()
    entity_state = hass.states.get(
        TEST_BINARY_SENSOR_FRONT_DOOR_PERSON_MOTION_ENTITY_ID
    )
    assert entity_state
    assert entity_state.state == "on"

    # Verify the steps (zone) motion sensor works.
    async_fire_mqtt_message(hass, "frigate/steps/person", "1")
    await hass.async_block_till_done()
    entity_state = hass.states.get(TEST_BINARY_SENSOR_STEPS_PERSON_MOTION_ENTITY_ID)
    assert entity_state
    assert entity_state.state == "on"

    async_fire_mqtt_message(hass, "frigate/front_door/person", "not_an_int")
    await hass.async_block_till_done()
    entity_state = hass.states.get(
        TEST_BINARY_SENSOR_FRONT_DOOR_PERSON_MOTION_ENTITY_ID
    )
    assert entity_state
    assert entity_state.state == "off"

    async_fire_mqtt_message(hass, "frigate/available", "offline")
    entity_state = hass.states.get(
        TEST_BINARY_SENSOR_FRONT_DOOR_PERSON_MOTION_ENTITY_ID
    )
    assert entity_state
    assert entity_state.state == "unavailable"


async def test_binary_sensor_api_call_failed(hass: HomeAssistant) -> None:
    """Verify a failed API call results in unsuccessful setup."""
    client = create_mock_frigate_client()
    client.async_get_stats = AsyncMock(side_effect=Exception)
    await setup_mock_frigate_config_entry(hass, client=client)
    assert not hass.states.get(TEST_BINARY_SENSOR_FRONT_DOOR_PERSON_MOTION_ENTITY_ID)


async def test_binary_sensor_device_info(hass: HomeAssistant) -> None:
    """Verify switch device information."""
    config_entry = await setup_mock_frigate_config_entry(hass)

    device_registry = dr.async_get(hass)
    entity_registry = er.async_get(hass)

    device = device_registry.async_get_device(
        identifiers={(DOMAIN, f"{config_entry.entry_id}:front_door")}
    )
    assert device
    assert device.manufacturer == NAME
    assert device.model == VERSION

    entities_from_device = [
        entry.entity_id
        for entry in er.async_entries_for_device(entity_registry, device.id)
    ]
    assert TEST_BINARY_SENSOR_FRONT_DOOR_PERSON_MOTION_ENTITY_ID in entities_from_device
    assert TEST_BINARY_SENSOR_STEPS_PERSON_MOTION_ENTITY_ID not in entities_from_device

    device = device_registry.async_get_device(
        identifiers={(DOMAIN, f"{config_entry.entry_id}:steps")}
    )
    assert device
    assert device.manufacturer == NAME
    assert device.model == VERSION

    entities_from_device = [
        entry.entity_id
        for entry in er.async_entries_for_device(entity_registry, device.id)
    ]
    assert (
        TEST_BINARY_SENSOR_FRONT_DOOR_PERSON_MOTION_ENTITY_ID
        not in entities_from_device
    )
    assert TEST_BINARY_SENSOR_STEPS_PERSON_MOTION_ENTITY_ID in entities_from_device
