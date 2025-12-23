"""aioasuswrt and pyasuswrt bridge classes."""

from __future__ import annotations

import logging
from typing import Any, NamedTuple, final

from aioasuswrt import (
    AsusWrt as AsusWrtLegacy,
    AuthConfig,
    ConnectionType,
    Mode,
    Settings,
    connect_to_router as create_connection_aioasuswrt,
)

from homeassistant.const import (
    CONF_HOST,
    CONF_MODE,
    CONF_PASSWORD,
    CONF_PORT,
    CONF_PROTOCOL,
    CONF_USERNAME,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import format_mac

from .const import (
    CONF_DNSMASQ,
    CONF_INTERFACE,
    CONF_REQUIRE_IP,
    CONF_SSH_KEY,
    DEFAULT_DNSMASQ,
    DEFAULT_INTERFACE,
    KEY_METHOD,
    KEY_SENSORS,
    MODE_ROUTER,
    PROTOCOL_TELNET,
    SENSORS_BYTES,
    SENSORS_LOAD_AVG,
    SENSORS_MEMORY,
    SENSORS_RATES,
    SENSORS_UPTIME,
)

SENSORS_TYPE_BYTES = "sensors_bytes"
SENSORS_TYPE_COUNT = "sensors_count"
SENSORS_TYPE_CPU = "sensors_cpu"
SENSORS_TYPE_LOAD_AVG = "sensors_load_avg"
SENSORS_TYPE_MEMORY = "sensors_memory"
SENSORS_TYPE_RATES = "sensors_rates"
SENSORS_TYPE_TEMPERATURES = "sensors_temperatures"
SENSORS_TYPE_UPTIME = "sensors_uptime"


class WrtDevice(NamedTuple):
    """WrtDevice structure."""

    ip: str | None
    name: str | None
    conneted_to: str | None


_LOGGER = logging.getLogger(__name__)


@final
class AsusWrtBridge:
    """The Base Bridge abstract class."""

    @classmethod
    def get_bridge(
        cls,
        hass: HomeAssistant,
        conf: dict[str, str | int],
        options: dict[str, str | bool | int] | None = None,
    ) -> AsusWrtBridge:
        """Get Bridge instance."""
        return cls(hass, conf, options)

    def __init__(
        self,
        hass: HomeAssistant,
        conf: dict[str, str | int],
        options: dict[str, str | bool | int] | None = None,
    ) -> None:
        """Initialize Bridge."""
        _host: str = str(conf[CONF_HOST])
        self._configuration_url = f"http://{_host}"
        self._host = _host
        self._firmware: str | None = None
        self._label_mac: str | None = None
        self._model: str | None = None
        self._model_id: str | None = None
        self._serial_number: str | None = None

        self._api: AsusWrtLegacy = self._get_api(conf, options)

    @staticmethod
    def _get_api(
        conf: dict[str, str | int],
        options: dict[str, str | bool | int] | None = None,
    ) -> AsusWrtLegacy:
        """Get the AsusWrtLegacy API."""
        opt = options or {}
        port = conf.get(CONF_PORT, None)

        return create_connection_aioasuswrt(
            str(conf[CONF_HOST]),
            AuthConfig(
                username=str(conf.get(CONF_USERNAME)),
                password=str(conf.get(CONF_PASSWORD)),
                connection_type=ConnectionType.TELNET
                if conf[CONF_PROTOCOL] == PROTOCOL_TELNET
                else ConnectionType.SSH,
                ssh_key=str(conf.get(CONF_SSH_KEY)),
                port=int(port) if port else None,
                passphrase=None,
            ),
            Settings(
                mode=Mode.ROUTER if conf[CONF_MODE] == MODE_ROUTER else Mode.AP,
                require_ip=opt.get(CONF_REQUIRE_IP, True),
                wan_interface=opt.get(CONF_INTERFACE, DEFAULT_INTERFACE),
                dnsmasq=opt.get(CONF_DNSMASQ, DEFAULT_DNSMASQ),
            ),
        )

    @property
    def is_connected(self) -> bool:
        """Get connected status."""
        return self._api.is_connected

    async def async_connect(self) -> None:
        """Connect to the device."""
        try:
            await self._api.connect()
        except ConnectionError as err:
            _LOGGER.error("Unable to connect to router (%s)", err)
            return

        # get main router properties
        if self._label_mac is None:
            await self._get_label_mac()
        if self._firmware is None:
            await self._get_firmware()
        if self._model is None:
            await self._get_model()

    async def async_disconnect(self) -> None:
        """Disconnect to the device."""
        await self._api.disconnect()

    async def async_get_connected_devices(self) -> dict[str, WrtDevice]:
        """Get list of connected devices."""
        _devices = await self._api.get_connected_devices(reachable=True)
        if not _devices:
            return {}
        return {
            format_mac(mac): WrtDevice(
                dev.device_data.get("ip"),
                dev.device_data.get("name"),
                dev.interface.get("name"),
            )
            for mac, dev in _devices.items()
        }

    async def _get_nvram_info(self, info_type: str) -> dict[str, str] | None:
        """Get AsusWrt router info from nvram."""
        return await self._api.get_nvram(info_type)

    async def _get_label_mac(self) -> None:
        """Get label mac information."""
        label_mac = await self._get_nvram_info("LABEL_MAC")
        if label_mac and "label_mac" in label_mac:
            self._label_mac = format_mac(label_mac["label_mac"])

    async def _get_firmware(self) -> None:
        """Get firmware information."""
        firmware = await self._get_nvram_info("FIRMWARE")
        if firmware and "firmver" in firmware:
            firmver: str = firmware["firmver"]
            if "buildno" in firmware:
                firmver += f" (build {firmware['buildno']})"
            self._firmware = firmver

    async def _get_model(self) -> None:
        """Get model information."""
        model = await self._get_nvram_info("MODEL")
        if model and "model" in model:
            self._model = model["model"]

    async def async_get_available_sensors(self) -> dict[str, dict[str, Any]]:
        """Return a dictionary of available sensors for this bridge."""
        sensors_temperatures = await self._get_available_temperature_sensors()
        return {
            SENSORS_TYPE_BYTES: {
                KEY_SENSORS: SENSORS_BYTES,
                KEY_METHOD: self._get_bytes,
            },
            SENSORS_TYPE_LOAD_AVG: {
                KEY_SENSORS: SENSORS_LOAD_AVG,
                KEY_METHOD: self._get_load_avg,
            },
            SENSORS_TYPE_RATES: {
                KEY_SENSORS: SENSORS_RATES,
                KEY_METHOD: self._get_rates,
            },
            SENSORS_TYPE_TEMPERATURES: {
                KEY_SENSORS: sensors_temperatures,
                KEY_METHOD: self._get_temperatures,
            },
        }

    async def _get_available_temperature_sensors(self) -> dict[str, float] | None:
        """Check which temperature information is available on the router."""
        return await self._api.get_temperature()

    async def _get_bytes(self) -> dict[str, int]:
        """Fetch byte information from the router."""
        items = await self._api.total_transfer()
        return {f"sensor_{key}_bytes": value for key, value in items.items()}

    async def _get_rates(self) -> dict[str, int] | None:
        """Fetch rates information from the router."""
        items = await self._api.get_current_transfer_rates()
        if items:
            return {f"sensor_{key}_rates": value for key, value in items.items()}
        return None

    async def _get_load_avg(self) -> dict[str, float] | None:
        """Fetch load average information from the router."""
        return await self._api.get_loadavg()

    async def _get_temperatures(self) -> dict[str, float] | None:
        """Fetch temperatures information from the router."""
        return await self._api.get_temperature()
