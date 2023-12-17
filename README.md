# aiotailwind

asyncio library to interact with [Tailwind](https://gotailwind.com) devices using their [local JSON API](https://github.com/Scott--R/Tailwind_Local_Control_API).

## Local Control Key

In order to use the local control API, it's necessary to obtain your Local Control Key (a 6-digit code), which you then provide when initialising an `Auth` instance.

To obtain your Local Control Key, ensure that you've updated your Tailwind iQ3 to the v9.95 firmware or later, and then:

1. Visit [Tailwind Web](https://web.gotailwind.com)
2. Log in with your Tailwind account
3. Click "Local Control Key" in the top menu (red box in screenshot)
4. If no key is displayed, click the "Create new local command key" button
5. Enter the 6-digit code (green box in screenshot) into the integration configuration

![Screenshot showing where to find the Local Control Key](local_control_key.png)

## Supported Devices

This library has been developed and tested against a Tailwind iQ3 garage door opener controller.  A rudimentary attempt to support the Light device referenced in the API documentation has been made, but without access to a physical device, it has not been possible to test whether this works.

## Demo

See [demo.py](https://github.com/pauln/aiotailwind/blob/main/demo.py) for a basic demo.
