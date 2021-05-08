""" HIASCDI Context Broker Module.

This module provides core helper functions for HIASCDI.

MIT License

Copyright (c) 2021 Asociación de Investigacion en Inteligencia Artificial
Para la Leucemia Peter Moss

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files(the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and / or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

Contributors:
- Adam Milton-Barker

"""

import json
import requests

class broker():
	""" HIASCDI Context Broker Module.

	This module provides core helper functions for HIASCDI.
	"""

	def __init__(self, helpers, mongodb):
		""" Initializes the class. """

		self.helpers = helpers
		self.program = "HIASCDI Helper Module"

		self.mongodb = mongodb

		self.headers = {
			"content-type": self.helpers.confs["contentType"]
		}

		self.auth = (self.helpers.confs["identifier"],
					self.helpers.confs["auth"])

		self.helpers.logger.info("HIASCDI initialization complete.")

	def checkAcceptsType(self, headers):
		""" Checks the request Accept type. """

		response = True
		if "Accept" not in headers or headers["Accept"] not in self.helpers.confs["contentTypes"]:
			response = False
		return response

	def checkContentType(self, headers):
		""" Checks the request Content-Type. """

		response = True
		if "Content-Type" not in headers or headers["Content-Type"] not in self.helpers.confs["contentTypes"]:
			response = False
		return response

	def checkJSON(self, payload):
		""" Checks the request Content-Type. """

		response = False
		try:
			json_object = json.loads(payload)
			response = True
		except ValueError as e:
			return False

		return response

