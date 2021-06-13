"""
This script is a component of the monitoring service for the Piminder alert management utility.
It is the main monitoring system which relies on Piminder.service to store messages and displays those messages on
the GFXHat attached to the host Pi.

Author: Zac Adam-MacEwen (zadammac@kenshosec.com)
A Kensho Security Labs utility.
Produced under license.
Full license and documentation to be found at:
https://github.com/ZAdamMac/Piminder
"""

__version__ = "1.0.5"

import argparse
import base64
from configparser import ConfigParser
import getpass
from gfxhat import touch
import http.client
import json
from os import environ
from time import sleep
from . import screendriver as disp
import ssl
import textwrap
from datetime import datetime as dt

# Globals are a bad code smell, but in a single-threaded environment nobody should care:
current_index = 0  # For safety reasons, both these two indexes must be modulated in the actual display function.
current_line_index = 0
mark_current_read = False
delete_current = False
touched = 0  # A number of process cycles before the system will go back into standby mode. Prevents API hammering


def display_splash():
    length_break_seconds = 15
    disp.print_line(3, "Piminder Monitor")
    disp.print_line(4, "v%s" % __version__)
    disp.print_line(7, "Get Messages...\u008B")
    sleep(length_break_seconds)


def enable_touch():  # It may be desirable in future to break the buttons out as unique handlers.
    for i in range(6):
        touch.on(i, handler=handle_input)
        touch.set_led(i, 0)


def handle_input(ch, event):
    global current_index, current_line_index, mark_current_read, delete_current, touched
    if event != 'press':
        return
    if ch == 0:  # "^" button, scroll up.
        current_line_index -= 1
    if ch == 1:  # "v" button, scroll down
        current_line_index += 1
    if ch == 2:  # "<" button, mark the message as read.
        mark_current_read = True
    if ch == 3:  # "-" button, go to the previous message
        current_index -= 1
        current_line_index = 0
    if ch == 4:  # Circle/middle button, delete message
        delete_current = True
    if ch == 5:  # "+" button, go to the next message
        current_index += 1
        current_line_index = 0
    touched = 500


def parse_args():
    """Parse arguments and return the path to the config file."""
    parser = argparse.ArgumentParser(description="""
        Automatically backup or restore personal files from the system. 
        \n Full documentation at https://github.com/ZAdamMac/Tapestry/blob/master/DOCUMENTATION.md
                                        """)
    parser.add_argument('config', help="Path (ideally absolute) to the configuration file.",
                        action="store")
    args = parser.parse_args()

    return str(args.config)


def parse_config(config_path):
    parser = ConfigParser()
    parser.read(config_path)
    vars_config = {}
    for section in parser.sections():  # this yields a flattened dictionary with no sections; all keys must be unique
        for option in parser.options(section):
            value = parser.get(section, option)
            vars_config.update({option: value})

    try:
        monitor_username = environ['MONITOR_UID']
    except KeyError:
        monitor_username = input("Monitor Username: ")
    try:
        monitor_password = environ['MONITOR_PASSWORD']
    except:
        monitor_password = getpass.getpass("Monitor Password: ")

    auth_precode = monitor_username + ":" + monitor_password
    vars_config["authorization"] = "Basic %s" % (base64.b64encode(auth_precode.encode('utf8')).decode('utf8'))

    return vars_config


def retrieve_messages(configuration, ssl_context):
    conf = configuration
    conn = http.client.HTTPSConnection(conf["service_host"], int(conf["service_port"]), context=ssl_context)
    conn.request("GET", "/api/messages/", headers={"Authorization": conf["authorization"],
                                                   "Content-type": "application/json"})
    resp = conn.getresponse()
    dict_resp = json.loads(resp.read())
    if dict_resp["error"] not in [200, 400]:  # 400 just indicates that the message should not be marked read twice.
        disp.clear_screen()
        disp.print_line(0, "Retrieval Error:")
        disp.print_line(1, "HTTP %s" % dict_resp["error"])
        disp.print_line(2, "Fatal, exiting.")
        exit(1)
    list_msg = []
    for item in dict_resp.items():  # We don't actually want an item, an ordered list of message objects is fine.
        if item[0] != "error":
            list_msg.append(item[1])

    return list_msg


def delete_message(configuration, list_messages, target_index, ssl_context):
    if len(list_messages) > 0: # Needed to prevent a crash; calling this same length later can lead to a div/0 error
        target_index = target_index % len(list_messages)
        conf = configuration
        target_mid = list_messages[target_index]["messageId"]
        list_messages.pop(target_index)  # this simply removes the message from list_messages
        body_out = "{\"messageId\":\"%s\"}" % target_mid
        conn = http.client.HTTPSConnection(conf["service_host"], int(conf["service_port"]), context=ssl_context)
        conn.request("DELETE", "/api/messages/", headers={"Authorization": conf["authorization"],
                                                          "Content-type": "application/json"}, body=body_out)
        resp = conn.getresponse()
        dict_resp = json.loads(resp.read())
        if dict_resp["error"] not in [200, 400]:  # 400 prevents double-deletion from being fatal.
            disp.clear_screen()
            disp.print_line(0, "Deletion Error:")
            disp.print_line(1, "HTTP %s" % dict_resp["error"])
            disp.print_line(2, "Fatal, exiting.")
            exit(1)
    updated_messages = retrieve_messages(configuration, ssl_context)  # Fetching the messages forces a screen update

    return updated_messages


def mark_read_message(configuration, list_messages, target_index, ssl_context):
    if len(list_messages) > 0:  # Needed to prevent a crash; calling this same length later can lead to a div/0 error
        target_index = target_index % len(list_messages)
        conf = configuration
        target_mid = list_messages[target_index]["messageId"]
        body_out = "{\"messageId\":\"%s\"}" % target_mid
        conn = http.client.HTTPSConnection(conf["service_host"], int(conf["service_port"]), context=ssl_context)
        conn.request("PATCH", "/api/messages/", headers={"Authorization": conf["authorization"],
                                                         "Content-type": "application/json"}, body=body_out)
        resp = conn.getresponse()
        dict_resp = json.loads(resp.read())
        if dict_resp["error"] not in [200, 400]:  # 400 is an error but not fatal; just means the message got hit twice.
            disp.clear_screen()
            disp.print_line(0, "Marking Read Error:")
            disp.print_line(1, "HTTP %s" % dict_resp["error"])
            disp.print_line(2, "Fatal, exiting.")
            exit(1)
    updated_messages = retrieve_messages(configuration, ssl_context)  # fetching the messages forces a screen update.

    return updated_messages


def display_messages(list_messages, target_message, current_top_line, config):
    if len(list_messages) > 0: # Needed to prevent a crash; calling this same length later can lead to a div/0 error
        target_message = target_message % len(list_messages)
        this_message = list_messages[target_message]
        severity = this_message["errorLevel"]
        body = this_message["message"]
        service = this_message["name"]
        time = this_message["timestamp"]
        time_modifier = dt.strptime(time, "%Y-%m-%dT%H:%M:%SZ")  # The API returns an ISO 8601-compliant timestamp, but
        time = time_modifier.strftime("%y-%m-%dT%H:%MZ")         # we need a shorter output time for the display
        is_read = this_message["read"]
        if not is_read:
            touch.set_led(2, 1)
        else:
            touch.set_led(2, 0)
        if severity.lower() == "info":
            disp.backlight_set_hue(config["info_color"])
            service = "%-15s\u0089" % service
        elif severity.lower() == "major":
            disp.backlight_set_hue(config["major_error_color"])
            service = "%-15s\u0087" % service
        elif severity.lower() == "minor":
            disp.backlight_set_hue(config["minor_error_color"])
            service = "%-15s\u0088" % service
        body_wrapped = textwrap.wrap(body, 16)
        current_top_line = current_top_line % len(body_wrapped)
        if current_top_line == 0:
            touch.set_led(0, 0)
        else:
            touch.set_led(0, 1)
        if current_top_line < len(body_wrapped) and len(body_wrapped) > 6:
            touch.set_led(1, 1)
        else:
            touch.set_led(1, 0)
        if target_message == 0:
            touch.set_led(3, 0)
        else:
            touch.set_led(3, 1)
        if target_message != (len(list_messages) - 1):
            touch.set_led(5, 1)
        else:
            touch.set_led(5, 0)
        disp.print_line(0, service)
        disp.print_line(1, time)
        for each in range(6):
            try:
                disp.print_line(2+each, body_wrapped[each+current_top_line])
            except IndexError:  # We have reached the end of the message
                disp.print_line(2+each, "")


def obtain_ssl_context(config):
    if str(config["custom_cert"]).lower in ['true', 't', 'yes', 'y', '1']:
        ssl_context = ssl.create_default_context(cafile=config["trusted_cert"])
        if str(config["allow_self-signed_certs"]) in ['true', 't', 'yes', 'y', '1']:
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE
    else:
        ssl_context = ssl.create_default_context()

    return ssl_context


def runtime():
    global current_index, current_line_index, mark_current_read, delete_current, touched
    path_config = parse_args()  # Since the monitor is callable (I _think_) from modules, we need to know where .cfg is
    dict_config = parse_config(path_config)  # If there was ever a kenshosec code smell, it's returning cfg as a dict
    ssl_context = obtain_ssl_context(dict_config)
    enable_touch()  # each button needs its own handler so we can't just loop.
    disp.backlight_set_hue(dict_config["color_resting"])
    display_splash()  # The delay for the splash screen display is set in display_splash as a constant.
    list_messages = []  # To avoid a race condition that can cause a crash.
    while True:
        try:
            if touched == 0:
                list_messages = retrieve_messages(dict_config, ssl_context)
                touched = 500
            else:
                touched -= 1
            if delete_current:
                list_messages = delete_message(dict_config, list_messages, current_index, ssl_context)
                delete_current = False
            if mark_current_read:
                list_messages = mark_read_message(dict_config, list_messages, current_index, ssl_context)
                mark_current_read = False
            if len(list_messages) != 0:
                display_messages(list_messages, current_index, current_line_index, dict_config)
            else:
                touched = 0  # Without this, we will iterate over touch at a rate of -1 in 15 sec = Bad
                disp.backlight_set_hue(dict_config["color_resting"])
                disp.clear_screen()
                for each in range(6):
                    touch.set_led(each, 0)
                display_splash()
        except KeyboardInterrupt:  # Hard to imagine how this could happen but it would still be nice to be graceful
            disp.clear_screen()
            disp.kill_backlight()
            for each in range(6):
                touch.set_led(each, 0)
            exit(0)
        except OSError:  # In the event of a network availability issue, the other functions can raise this.
            disp.clear_screen()
            for each in range(6):
                touch.set_led(each, 0)
            disp.print_line(3, "Piminder Monitor")
            disp.print_line(4, "v%s" % __version__)
            disp.print_line(7, "Network Fault...\u008B")
            disp.backlight_set_hue(config["minor_error_color"])
            sleep(60)


if __name__ == "__main__":
    runtime()
