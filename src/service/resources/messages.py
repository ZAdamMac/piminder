"""
This script is a component of pyminder's back-end controller.
This resource handles the registration of messages and handling existing messages through various restful methods.

Author: Zac Adam-MacEwen (zadammac@kenshosec.com)
A Kensho Security Labs utility.

Produced under license.
Full license and documentation to be found at:
https://github.com/ZAdamMac/Enumpi-C2
"""

import datetime
from flask_restful import Resource
from flask import current_app, request, make_response
import json
from os import urandom
import pymysql
import uuid
from .utilities import authenticated_exec, json_validate, token_validate, check_system_secret

__version__ = "prototype"


class MessageAPI(Resource):
    def get(self):
        """An authenticated user with reporting permissions may retrieve a
        full listing of all commands logged by the server set up on the server.

        :return: In the valid case, a json dictionary of (row, action) pairs
        """
        # FUTURE add query scoping.
        cookie = request.headers.get["x-pyminder-secret"]
        ttl = int(current_app.config["CLIENT_TTL"])*60
        iss = current_app.config["NETWORK_LABEL"]
        try:
            connection = pymysql.connect(host=current_app.config["DBHOST"],
                                         user=current_app.config["USERNAME"],
                                         password=current_app.config["PASSPHRASE"],
                                         db='enumpi',
                                         charset='utf8mb4',
                                         cursorclass=pymysql.cursors.DictCursor)
            connection.ping(reconnect=True)
        except KeyError:
            return {'message': 'Internal Server Error'}, 500
        except pymysql.Error:
            return {'message': 'Internal Server Error'}, 500
        if check_system_secret(cookie, current_app.PYMINDER_SECRET):
            dict_return = messages_get()
            resp = make_response(dict_return)
            resp.status_code = dict_return["error"]
            resp.content_type = "application/json"
            return resp
        else:
            return {'message': 'unauthorized'}, 401

    def post(self):
        """The post method allows the listing of a new message in the database.

        :return:
        """
        cookie = request.headers.get["x-pyminder-secret"]
        ttl = int(current_app.config["CLIENT_TTL"])*60
        iss = current_app.config["NETWORK_LABEL"]
        try:
            connection = pymysql.connect(host=current_app.config["DBHOST"],
                                         user=current_app.config["USERNAME"],
                                         password=current_app.config["PASSPHRASE"],
                                         db='enumpi',
                                         charset='utf8mb4',
                                         cursorclass=pymysql.cursors.DictCursor)
            connection.ping(reconnect=True)
        except KeyError:
            return {'message': 'Internal Server Error'}, 500
        except pymysql.Error:
            return {'message': 'Internal Server Error'}, 500
        if check_system_secret(cookie, current_app.PYMINDER_SECRET):
            dict_return = messages_post(request.get_json())
            resp = make_response(dict_return)
            resp.status_code = dict_return["error"]
            resp.content_type = "application/json"
            return resp
        else:
            return {'message': 'unauthorized'}, 401

    def delete(self):
        """This will mark a specified message as read. The message is not wholly discarded immediately, but will be
        garbage-collected by a cron job run against the DB itself.

        :return:
        """
        # deactivate (set permissions 0) a user if authenticated.
        cookie = request.headers.get["x-pyminder-secret"]
        ttl = int(current_app.config["CLIENT_TTL"]) * 60
        iss = current_app.config["NETWORK_LABEL"]
        try:
            connection = pymysql.connect(host=current_app.config["DBHOST"],
                                         user=current_app.config["USERNAME"],
                                         password=current_app.config["PASSPHRASE"],
                                         db='enumpi',
                                         charset='utf8mb4',
                                         cursorclass=pymysql.cursors.DictCursor)
            connection.ping(reconnect=True)
        except KeyError:
            return {'message': 'Internal Server Error'}, 500
        except pymysql.Error:
            return {'message': 'Internal Server Error'}, 500
        if check_system_secret(cookie, current_app.PYMINDER_SECRET):
            dict_return = messages_delete(request.get_json())
            resp = make_response(dict_return)
            resp.status_code = dict_return["error"]
            resp.content_type = "application/json"
            return resp
        else:
            return {'message': 'unauthorized'}, 401

# Here follow the actual actions!


def messages_get(body, connection):
    """A stored join function that gets all the currently registered commands,
    their relevant metadata, the name of the client they are associated with
    and the message, if any. This is returned to the requestor in a JSON
    format for further processing."""
    cur = connection.cursor()
    del body

    # Unwieldy command handles most of the data processing in SQL which is faster than doing this in python.

    cmd = "SELECT * FROM messages ODER BY timestamp desc;"
    cur.execute(cmd)
    messages = cur.fetchall()
    response = {}
    counter = -1
    for message in messages:
        output_keys = {"id": "messageId", "name": "name", "read": "read", "errorlevel": "errorLevel",
                       "timestamp": "timestamp", "message": "message"}
        counter += 1
        this_message = {}
        for key in output_keys.keys():
            this_message.update({output_keys[key]: message[key]})
        response.update({str(counter): this_message})
    response.update({"error": 200})

    return response


def messages_post(body, connection):
    """A very simplistic function that adds a fresh command to the commands table."""
    cur = connection.cursor()
    dict_schema = {"name": "", "timestamp": "", "errorlevel": "", "message": ""}
    json_valid, errors = json_validate(body, dict_schema)
    if body["errorlevel"] not in ["info", "minor", "major"]:
        json_valid = False
        errors.update({"errorlevel": "Error level not one of info, minor, or major."})

    if json_valid:
        d_message = {}
        d_message.update(body)
        d_message.update({"id": str(uuid.uuid4())})
        d_message.update({"read": False})
        d_message.update({"timestamp": datetime.datetime.strptime(body["timestamp"], "%Y-%m-%dT%H:%M:%SZ").timestamp()})
        cmd = "INSERT INTO message " \
              "(id, name, timestamp, errorlevel, message, read) " \
              "VALUES (%(id)s, %(name)s, FROM_UNIXTIME(%(timestamp)s), %(errorlevel)s, " \
              "%(message)s, %(read)s"
        cur.execute(cmd, d_message)
        response = {"error": 200}
    else:
        response = {"all_errors": errors, "error": 400}

    return response


def messages_delete(body, connection):
    """This function indicates in the DB that a message has been read.
    A stored procedure or cron job will garbage collect."""
    cur = connection.cursor()
    dict_schema = {"messageId": ""}
    json_valid, errors = json_validate(body, dict_schema)

    if json_valid:
        # First, make sure this hasn't already been executed.
        cmd = "SELECT time_acknowledged " \
              "FROM commands " \
              "WHERE command_id=%s"
        cur.execute(cmd, body["messageId"])
        response = cur.fetchone()
        # Gotta be a better way to do the following line, but...
        try:
            if not response["read"]:
                cmd = "UPDATE messages " \
                      "SET read=TRUE" \
                      "WHERE id=%s"
                cur.execute(cmd, body["messageId"])
                response = {"error": 200}
            else:
                response = {"error": 400, "message": "Could not delete command - already acknowledged."}
        except KeyError:
            response = {"error": 400, "message": "The indicated ID does not exist in the messages table."}
    else:
        response = {"all_errors": errors, "error": 400}

    return response
