"""
This script is a component of Piminder's back-end controller.
This resource handles a special creation case for messages; allowing them to be created only if
the bulk of their data is unique. This is useful for messages that are being generated frequently,
such as short-interval crons looking for live containers on a cluster.

Author: Zac Adam-MacEwen (zadammac@arcanalabs.com)
An Arcana Labs utility.

Produced under license.
Full license and documentation to be found at:
https://github.com/ZAdamMac/piminder
"""

import datetime
from flask_restful import Resource
from flask import current_app, request, make_response
import pymysql
import uuid
from .utilities import authenticated_exec, basic_auth, json_validate

__version__ = "1.1.0"


class UniqueMessageAPI(Resource):
    def post(self):
        """The post method allows the listing of a new message in the database.

        :return:
        """
        cookie = request.headers.get("Authorization")
        try:
            connection = pymysql.connect(host=current_app.config["DBHOST"],
                                         user=current_app.config["USERNAME"],
                                         password=current_app.config["PASSPHRASE"],
                                         db='Piminder',
                                         cursorclass=pymysql.cursors.DictCursor)
            connection.ping(reconnect=True)
        except KeyError:
            return {'message': 'Internal Server Error, Key error'}, 500
        except pymysql.Error as e:
            return {'message': 'Internal Server Error, sql error'}, 501
        proceed, user = basic_auth(cookie, connection)
        if proceed:  # A chicken ain't nothing but a bird.
            dict_return = authenticated_exec(user, 1, connection, messages_post, request.get_json())
            resp = make_response(dict_return)
            resp.status_code = dict_return["error"]
            resp.content_type = "application/json"
            return resp
        else:
            return {'message': 'unauthorized'}, 401

# Here follow the actual actions!


def unique_messages_post(body, connection):
    """Check if the given message exists on the messages table already and either create or update it."""
    cur = connection.cursor()
    dict_schema = {"name": "", "timestamp": "", "errorlevel": "", "message": "", "updateTimestamp": False}
    json_valid, errors = json_validate(body, dict_schema)
    if body["errorlevel"] not in ["info", "minor", "major"]:
        json_valid = False
        errors.update({"errorlevel": "Error level not one of info, minor, or major."})

    if json_valid:
        # Find if it exists already
        cmd = "SELECT id " \
              "FROM messages " \
              "WHERE name=%s AND message=%s"
        rows = cur.execute(cmd, (body["name"], body[message]))
        if rows:
            result = cur.fetchone()
        # If not, create it
        if rows == 0:
            d_message = {}
            d_message.update(body)
            d_message.update({"id": str(uuid.uuid4())})
            d_message.update({"read": False})
            d_message.update({"timestamp": datetime.datetime.strptime(body["timestamp"], "%Y-%m-%dT%H:%M:%SZ").timestamp()})
            cmd = "INSERT INTO messages " \
                "(id, name, time_raised, errorlevel, message, read_flag) " \
                "VALUES (%(id)s, %(name)s, FROM_UNIXTIME(%(timestamp)s), %(errorlevel)s, " \
                "%(message)s, %(read)s)"
            cur.execute(cmd, d_message)
            response = {"error": 200}
            connection.commit()
        # If so, and asked for in body
        if rows:
            if body["updateTimestamp"]:
                cmd = "UPDATE messages " \
                      "SET read_flag=FALSE, timestamp=FROM_UNIXTIME(%(timestamp)s) " \
                      "WHERE id=%(id)s"
            else:
                cmd = "UPDATE messages " \
                      "SET read_flag=FALSE, " \
                      "WHERE id=%(id)s"
            result.update({"timestamp": datetime.datetime.strptime(body["timestamp"], "%Y-%m-%dT%H:%M:%SZ").timestamp()})
            cur.execute(cmd, result)
            response = {"error": 200}
            connection.commit()

    else:
        response = {"all_errors": errors, "error": 400}

    return response

