"""
This script is a component of the Piminder helpers package. It defines classes to be used in other programs to interact
with the Piminder service.

Author: Zac Adam-MacEwen (zadammac@kenshosec.com)
A Kensho Security Labs utility.

Produced under license.
Full license and documentation to be found at:
https://github.com/ZAdamMac/Piminder
"""

import base64
import datetime
import http.client
import json
import ssl


class PiminderException(BaseException):
    pass


class PiminderService(object):
    def __init__(self, username, password, host, port, service_name, cert_path=None, self_signed=False):
        auth_precode = username + ":" + password
        self.Piminder_key = "Basic %s" % (base64.b64encode(auth_precode.encode('utf8')).decode('utf8'))
        self.host = str(host)
        self.port = int(port)
        self.name = str(service_name)
        self.ssl_context = ssl.create_default_context(capath=cert_path)
        if self_signed:
            self.ssl_context.check_hostname = False
            self.ssl_context.verify_mode = ssl.CERT_NONE

    def post_message(self, message, level):
        connection = http.client.HTTPSConnection(host=self.host, port=self.port, context=self.ssl_context)
        request_data = {
            "name": self.name,
            "message": message,
            "errorlevel": level,
            "timestamp": datetime.datetime.utcnow().isoformat(sep="T", timespec="seconds") + "Z",
        }
        request_body = json.dumps(request_data)
        connection.request("POST", "/api/messages/", body=request_body, headers={"Authorization": self.Piminder_key,
                                                                                 "Content-type": "application/json"})
        resp = connection.getresponse()
        if resp.status != 200:  # We have encountered an error condition
            raise PiminderException()

    def info(self, message):
        self.post_message(message, "info")

    def minor(self, message):
        self.post_message(message, "minor")

    def major(self, message):
        self.post_message(message, "major")