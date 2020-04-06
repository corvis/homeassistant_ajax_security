# HomeAssistant AjaxSecurity Bridge

Bridge between [ajax security modules](https://ajax.systems/) and [Home Assistant](https://www.home-assistant.io/).
The modules connects to the home assistant instance via [UART Bridge](https://ajax.systems/products/uartbridge/) which provides [Jeweller](https://ajax.systems/jeweller/)(native ajax radio protocol) <> UART interface. In order to connect bridge to home assistant USB-UART adaptor is required. Please avoid super low-cost chineese adaptors as they are extreamly unstables.

Currently supported Ajax products are:
* [Fire Protect](https://ajax.systems/products/fireprotect/)

## Required Hardware

* [Ajax UART Bridge](https://ajax.systems/products/uartbridge/), to interface wireless Ajax devices
* USB-UART adaptor, to connect UART bridge to home assistant server. UART bridge compatible with 3.3v logic.

### USB-UART devices known to work fine
* Chinees devices built on CP2102 chip

### USB-UART devices known to work poorly or doesn't work
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

TBD

# Development

For development purposes it is highly recommended to bootstrap the new and clean home assistnant environment. You may use the content of the `dev_hass_config` folder to start. Just put it in some folder which will be you project root and create virtual environment with reqired dependancies:

```
virtualenv venv
source ./venv/bin/activate
pip install -r ./requirements.txt
```

Now you could run local home assistant instance like this: `hass`

## Credits
Dmitry Berezovsky

## Disclaimer
This module is licensed under GPL v3. This means you are free to use it even in commercial projects.

The GPL license clearly explains that there is no warranty for this free software. Please see the included LICENSE file for details.
