# HomeAssistant AjaxSecurity Bridge

***DISCLAIMER: This component is under active development now. There are no any stable release yet, so please do not use it in your installation unless you are developer who would like to contribute into module***

Bridge between [ajax security modules](https://ajax.systems/) and [Home Assistant](https://www.home-assistant.io/).
The modules connects to the home assistant instance via [UART Bridge](https://ajax.systems/products/uartbridge/) which provides [Jeweller](https://ajax.systems/jeweller/)(native ajax radio protocol) <> UART interface. 

This integration __doesn't use Ajax cloud services__, doesn't require internet connection and doesn't expose any data outside of local network. However it requires special hardware module to interface Ajax wireless protocol, see Required Hardware section below.

Currently supported Ajax products are:
* [Fire Protect](https://ajax.systems/products/fireprotect/)

## Required Hardware

* [Ajax UART Bridge](https://ajax.systems/products/uartbridge/), to interface wireless Ajax devices
* USB-UART adaptor, to connect UART bridge to home assistant server. Please avoid super low-cost chineese adaptors as they might be extreamly unstables.

**USB-UART devices known to work fine**
* Chinees devices built on CP2102 chip

**USB-UART devices known to work poorly or doesn't work**
* TBD

## Instalation

From releases section download the latest realease. Put `ajax_security` folder from archive into `custom_components` folder of your home assistant installation. 
In the root of home assisatnce configuration add the following:

```yaml
ajax_security:
  name: bridge0
  port: /dev/ttyUSB0
  baudrate: 57600
```

Make sure to edit port to match the real device name.

TBD

## Configuration

| Name     | Type         | Default      | Description                              |
| -------- | ------------ | ------------ | ---------------------------------------- |
| name     | string       | uart_bridge0 | Name of the integration module. Must be set to unique value in case you need 2 or more simultaneously connected UART bridges. |
| port     | string       | required     | Path to TTY devices. May vary depending on USB-UART adaptor and operation system. Check your `/dev/tty*`.<br />**Example**: `/dev/ttyUSB0` |
| baudrate | positive int | 57600        | Baudrate of the the serial interface. Currently Ajax Bridge operates on **57600** |
| timeout  | positive int | 3            | Socket time out in seconds               |

# Development

For development purposes it is highly recommended to bootstrap the new and clean home assistnant environment. You may use the content of the `dev_hass_config` folder to start. Just put it in some folder which will be you project root and create virtual environment with reqired dependancies:

```
virtualenv venv
source ./venv/bin/activate
pip install -r ./requirements.txt
```

Now you could run local home assistant instance like this: `hass`

Documentation which describes UART Bridge protocol is [available here](https://drive.google.com/file/d/1My0iAjZrig5aIq9D1LeddCMkquKD1K7p/view).

## Credits
Dmitry Berezovsky

## Disclaimer
This module is licensed under GPL v3. This means you are free to use it even in commercial projects.

The GPL license clearly explains that there is no warranty for this free software. Please see the included LICENSE file for details.
