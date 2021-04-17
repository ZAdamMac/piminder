# Pyminder
A simple heads-up-display/dashboard utility for the Raspberry Pi, premised on the [Pimoroni GFX Hat](https://shop.pimoroni.com/products/gfx-hat). This utility operates a small Flask-based RESTful API and provides two helper modules, `monitor` and `helpers`, allowing local scripts and cron jobs to display messages on the HAT in a structured way. Initial development is by [Arcana Labs](https://www.arcanalabs.ca). Development is very casually ongoing, with minor incremental improvements as they become desired within the lab.

## Fitness for Risk
Pyminder is intended for use as a small-scale monitoring utility in a lab/private subnet capacity only. It is not hardened for or intended to for use with a WAN or direct exposure to the internet. Messages, including the service shared secret, are currently stored and exchanged in plaintext. The intended use case is to run the service listening to localhost only. Please do not use Pyminder as a security appliance or to store sensitive information.

## System Requirements
It is supposed that the local versions of Raspbian and Python 3 are up to date. The test article also used an up-to-date version of Mariadb.

## Installation Steps
1. Clone this repo somewhere that will be accessible to you later.
2. Update `./src/service/pyminder-service.conf` as needed.
3. Update `./monitor/monitor.conf` as needed
4. run `/src/helpers/dbinit.py` to initialize the database.
5. Run `/src/serice/run.py` in the backround
6. cd to `/src` and invoke monitor as a module with `python3 -m monitor monitor/monitor.conf` in background or foreground as desired.

## Using Helpers
The helpers module exposes a class constructor and several convenience functions to allow scripts to more easily work with the Pyminder API. consider copying the directory to your `~/bin` for use with your cron jobs and ease of import (pypi/setuputils installation not currently provided).

To use:
1. instantiate a PyminderService object using the necessary configuration details:
   
```python3
somehandler = helpers.PyminderService(shared_secret, hostname, hostport, service_name)
```
2. use the `.minor()`, `.major()`, and `.info()` methods of that object to post messages directly to the API, with the message as a string of arbitrary length.

## Using the API Directly.
The pyminder API is a REST-like API exposed via flask, at `$servicehost/api/messages/`. For authentication it expects a `x-pyminder-secret` header to be included in the request.

It supports the following methods:
- `GET` returning a full array of all stored messages as discreet objects
- `POST` allowing the posting of one unique new message
- `PATCH` updating a given message (indicated by an ID) as read.
- `DELETE`, removing the given message from the DB.

In the case of POST, PATCH, and DELETE, refer to `src/service/resources/messages.py` for a full breakdown of expected post bodies. The project wiki includes details on the intended use of each property.

## Interacting with Pyminder
Careful observation of the GFXHat will note that each of the six buttons is individually marked. When Pyminder is in operation, these buttons perform the following functions:
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