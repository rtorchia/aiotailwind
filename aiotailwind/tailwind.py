from aiohttp import ClientResponse, ContentTypeError
from .auth import Auth
from typing import List

COMMAND_OPEN = "open"
COMMAND_CLOSE = "close"


class TailwindError(Exception):
    def __init__(self, info: str):
        self.info = info
    
    def __str__(self) -> str:
        return "Tailwind error: {}".format(self.info)

class Door:
    """Class that represents an individual door on a Tailwind iQ3 controler."""

    def __init__(self, key: str, door_data: dict, auth: Auth):
        """Initialize an iQ3 Door object."""
        self.key = key
        self.raw_data = door_data
        self.auth = auth

    @property
    def door_key(self) -> str:
        """The key within the doors dict for this door."""
        return self.key

    @property
    def is_open(self) -> bool:
        """Is this door open?"""
        return self.raw_data["status"] == "open"

    @property
    def is_enabled(self) -> bool:
        """Is this door enabled?"""
        return self.raw_data["enabled"] == 1

    @property
    def is_locked_out(self) -> bool:
        """Is this door locked out due to a failed command?"""
        # Tailwind are going to change this key to be clearer.
        if "lockedout" in self.raw_data:
            return self.raw_data["lockedout"] == 1
        return self.raw_data["lockup"] == 1

class Light:
    """Class that represents a Tailwind light device."""
    
    def __init__(self, raw_data: dict, auth: Auth):
        """Initialize a Tailwind Light object."""
        self.raw_data = raw_data
        self.auth = auth

    @property
    def mode(self) -> str:
        """Mode: "manual" = user-controlled; "auto" = motion-controlled."""
        return self.raw_data["mode"]

    @property
    def light_power(self) -> int:
        """Brightness level; 0-100"""
        return self.raw_data["light"]["power"]

    @property
    def light_frequency(self) -> int:
        """Unclear; possibly PWM frequency?"""
        return self.raw_data["light"]["frequency"]

    @property
    def motion_sensitivity(self) -> int:
        """Motion sensitivity level (0-15)."""
        return self.raw_data["radar"]["distance"]

    @property
    def motion_max_lux(self) -> int:
        """Motion sensing kicks in below this ambient light level."""
        return self.raw_data["radar"]["lux"]

    @property
    def motion_off_delay(self) -> int:
        """Number of seconds to keep the light on after sensing motion."""
        return self.raw_data["radar"]["delay"]

    

class TailwindController:
    """Class that represents a Tailwind controller device."""

    def __init__(self, raw_data: dict, auth: Auth):
        """Initialize an iQ3 object."""
        self.raw_data = raw_data
        self.auth = auth

    @property
    def id(self) -> int:
        """Return the ID of the iQ3 device."""
        return self.raw_data["dev_id"]

    @property
    def product(self) -> str:
        """Return the product name/model"""
        return self.raw_data["product"]

    @property
    def num_doors(self) -> int:
        """Return the number of doors."""
        if self.product != "iQ3":
            return 0
        return self.raw_data["door_num"]

    @property
    def firmware_version(self) -> str:
        """Return the firmware version."""
        return self.raw_data["fw_ver"]

    @property
    def protocol_version(self) -> str:
        """Return the protocol version."""
        return self.raw_data["proto_ver"]

    @property
    def night_mode(self) -> bool:
        """Return whether night mode is enabled."""
        if self.product != "iQ3":
            return False
        return self.raw_data["night_mode_en"] == 1

    @property
    def doors(self) -> List[Door]:
        """Return a list of door enitities."""
        if self.product != "iQ3":
            return []
        return [Door(key, door_data, self.auth) for (key, door_data) in self.raw_data["data"].items()][:self.num_doors]

    @property
    def light(self) -> Light:
        """Return a Light entity, if applicable."""
        if self.product != "light":
            return None
        return Light(self.raw_data["data"], self.auth)

    async def async_control_door(self, index: int, command: str, partial_time: int=None):
        """Control a door."""
        req = {
            "version": "0.1",
            "data": {
                "type": "set",
                "name": "door_op",
                "value": {
                    "door_idx": index,
                    "cmd": command,
                }
            }
        }

        if command == COMMAND_OPEN and partial_time is not None:
            req["data"]["value"]["partial_time"] = partial_time
        
        resp = await self.auth.request(
            "post", f"json", json=req
        )
        
        await self.get_json(resp)
        
        await self.async_update()
    
    async def async_open_door(self, index: int):
        """Open a door."""
        await self.async_control_door(index, COMMAND_OPEN)
    
    async def async_partial_open_door(self, index: int, partial_time: int):
        """Open a door partially."""
        await self.async_control_door(index, COMMAND_OPEN, partial_time)
    
    async def async_close_door(self, index: int):
        """Close a door."""
        await self.async_control_door(index, COMMAND_CLOSE)

    async def async_set_status_led_brightness(self, brightness: int):
        """Set the status LED brightness (percent)."""
        req = {
            "version": "0.1",
            "data": {
                "type": "set",
                "name": "status_led",
                "value": {
                    "brightness": brightness,
                }
            }
        }
        resp = await self.auth.request(
            "post", f"json", json=req
        )
        
        await self.get_json(resp)
        
        await self.async_update()

    async def async_update(self):
        """Update the device data / status."""
        req = {
            "version": "0.1",
            "data": {
                "type": "get",
                "name": "dev_st"
            }
        }
        resp = await self.auth.request("post", f"json", json=req)
        
        self.raw_data = await self.get_json(resp)

    async def get_json(self, resp: ClientResponse) -> dict:
        """A wrapper to handle extracting the JSON response payload."""

        # If there's an HTTP error, raise it up front.
        resp.raise_for_status()

        try:
            # The Tailwind firmware team say they'll change the content-type to
            # text/json in the next firmware version; try that (default) first.
            raw_data = await resp.json()
        except ContentTypeError:
            # Initial JSON API implementation uses incorrect content-type.
            raw_data = await resp.json(content_type="text/html")

        if raw_data is None:
            raise TailwindError("empty response (request may be invalid)")
            
        if raw_data["result"] != "OK":
            raise TailwindError(raw_data["info"])

        return raw_data

