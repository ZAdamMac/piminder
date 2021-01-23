"""
This script is a component of the pyminder helpers package. It defines classes to be used in other programs to interact
with the pyminder service.

Author: Zac Adam-MacEwen (zadammac@kenshosec.com)
A Kensho Security Labs utility.

Produced under license.
Full license and documentation to be found at:
https://github.com/ZAdamMac/pyminder
"""

import datetime
import http.client
import json


class PyminderException(BaseException):
    pass


class PyminderService(object):
    def __init__(self, shared_secret, host, port, service_name):
        self.pyminder_key = shared_secret
        self.host = str(host)
        self.port = int(port)
        self.name = str(service_name)

    def post_message(self, message, level):
        connection = http.client.HTTPConnection(host=self.host, port=self.port)
        request_data = {
            "name": self.name,
            "message": message,
            "errorlevel": level,
            "timestamp": datetime.datetime.utcnow().isoformat(sep="T", timespec="seconds") + "Z",
        }
        request_body = json.dumps(request_data)
        connection.request("POST", "/api/messages/", body=request_body, headers={"x-pyminder-secret": self.pyminder_key,
                                                                                 "Content-type": "application/json"})
        resp = connection.getresponse()
        if resp.status != 200:  # We have encountered an error condition
            raise PyminderException()

    def info(self, message):
        self.post_message(message, "info")

    def minor(self, message):
        self.post_message(message, "minor")

    def major(self, message):
        self.post_message(message, "major")