import asyncio
import aiohttp

from aiotailwind import Auth, TailwindController, TailwindError


async def main():
    async with aiohttp.ClientSession() as session:
        # Set your Tailwind device's IP address and local control key below:
        auth = Auth(session, "http://192.168.0.123", "your_local_control_key")
        controller = TailwindController({}, auth)

        try:
            await controller.async_update()

            # Print door states
            for door in controller.doors:
                print(door.door_key + ": " + ("open" if door.is_open else "closed"))

            # Set status LED brightness
            # await controller.async_set_status_led_brightness(50)

            # Partially open first door
            # await controller.async_partial_open_door(0, 1500)
            
            # Open first door
            # await controller.async_open_door(0)

            # Close first door
            # await controller.async_close_door(0)
        except TailwindError as err:
            print(err)


asyncio.run(main())