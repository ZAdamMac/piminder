# Piminder
A minimal-functionality heads-up-display/dashboard utility for the Raspberry Pi, premised on the [Pimoroni GFX Hat](https://shop.pimoroni.com/products/gfx-hat). This utility operates a small Flask-based RESTful API and provides two helper modules, `monitor` and `helpers`, allowing local scripts and cron jobs to display messages on the HAT in a structured way. Initial development is by [Arcana Labs](https://www.arcanalabs.ca). Development is very casually ongoing, with minor incremental improvements as they become desired within the lab.

## Fitness for Risk
Piminder is intended for use as a small-scale monitoring utility in a lab/private subnet capacity only. It is not hardened for or intended to for use with a WAN or direct exposure to the internet, and should be protected by a reverse proxy and other traffic shaping rules at all times if present on such a network. The release version, 1.0 and later, includes TLS capabilities. It is strongly recommended you read the documentation fully before configuring and using this product.

## System Requirements
It is supposed that the local versions of Raspbian and Python 3 are up to date. The test article also used an up-to-date version of Mariadb. Naturally, the GFX hat is also a requirement as the monitor will not work with any other display.

## Recommended Usage Instructions
Note: Apart from `SECURITY.md`, all referenced documentation is in the `documentation` folder.
1. Read the SECURITY.md and NETWORKING.md documentation thoroughly.
2. Follow the instructions in SERVICE_SETUP.md to install and configure Piminder's service on its target device and create your first auth credentials
3. `pip install Piminder` on any system where you wish to use `Piminder_helpers` or `Piminder_monitor`.
4. Configure the monitor and establish it as a service on the host pi based on the instructions in `MONITOR_Setup.md`

## Using Helpers
The helpers module exposes a class constructor and several convenience functions to allow scripts to more easily work with the Piminder API. 

To use:
1. instantiate a PiminderService object using the necessary configuration details:
   
```python3
somehandler = Piminder_helpers.PiminderService(username, password, hostname, hostport, job_identifier)
```
2. use the `.minor()`, `.major()`, and `.info()` methods of that object to post messages directly to the API, with the message as a string of arbitrary length.
  - Versions 1.1.0 and later: the flags `unique` and `update_timestamp` can now be passed to all alert levels to prevent flooding with frequently-run monitors.

## Using the APIs Directly.
The Piminder API is a REST-like API exposed via flask, at `$servicehost/api/messages/` and `$servicehost/api/users`. The API expects basic authentication.

## Interacting with Piminder
Careful observation of the GFXHat will note that each of the six buttons is individually marked. When Piminder is in operation, these buttons perform the following functions:
- "^" will scroll the current message upward.
- "v" will scroll the current message downward.
- "<" will mark the message as read.
- "-" will switch to the previous message.
- "+" will switch to the next message
- "Circle-Dot" will delete the currently displayed message.

Each of these buttons also has a corresponding LED:
- "^" indicates that there is more to this message if you scroll up.
- "v" indicates that there is more to this message if you scroll down
- "<" indicates this message is unread
- "-" indicates there is a message before this one.
- "+" indicates there is a message after this one.

The LCD is backlit, and the colour is used to indicate message severity. By default, this is green for `info`, yellow for `minor`, and red for `major`. These values can be changed in `/src/monitor/monitor.conf` by providing a hex colour code in the HTML-standard format, eg `#123456`.

## Special Font Characters
The font is a UTF-8 font, though the full keyspace is not defined. Characters 32-126 (the normal printing range) is defined. In addition, 12 special characters are defined:

|Python Escaped String Literal|Character Description|
|-----------------------------|---------------------|
|`\u0082`|Envelope Icon|
|`\u0081`|Progress Bar, Left End, Empty|
|`\u0082`|Progress Bar, Left End, Filled|
|`\u0083`|Progress Bar, Middle, Empty|
|`\u0084`|Progress Bar, Middle, Full|
|`\u0085`|Progress Bar, Right End, Empty|
|`\u0086`|Progress Bar, Right End, Full|
|`\u0087`|Major Severity Icon (! in Triangle)|
|`\u0088`|Minor Severity Icon (? in Square)|
|`\u0089`|Info Severity Icon (i in Circle)|
|`\u00BA`|Elipsis (...)|
|`\u008B`|Clock Icon|