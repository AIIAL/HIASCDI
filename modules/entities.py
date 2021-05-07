#!/usr/bin/env python
""" HIASCDI Entities Module.

This module provides the functionality to create, retrieve
and update HIASCDI entities.

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
import jsonpickle
import os
import sys

from mgoquery import Parser

from bson import json_util, ObjectId
from flask import Response

class entities():
	""" HIASCDI Entities Module.

	This module provides the functionality to create, retrieve
	and update HIASCDI entities.
	"""

	def __init__(self, helpers, mongodb, broker):
		""" Initializes the class. """

		self.helpers = helpers
		self.program = "HIASCDI Entities Module"

		self.mongodb = mongodb
		self.broker = broker

		self.helpers.logger.info(self.program + " initialization complete.")

	def getEntities(self, arguments):
		""" Gets entity data from the MongoDB.

		References:
			FIWARE-NGSI v2 Specification
			https://fiware.github.io/specifications/ngsiv2/stable/

			Reference
				- Entities
					- List entities
		"""

		params = []
		cparams = []
		sort = []
		query = {}

		# Removes the MongoDB ID
		fields = {'_id': False}

		# Sets a type query
		if arguments.get('type') is not None:
			eor = []
			types = arguments.get('type').split(",")
			if len(types) == 1:
				query.update({"type":
						{'$in': [types[0]]}
					})
			else:
				for eid in types:
					eor.append({"type":
							{'$in': [eid]}
						})
				params.append({"$or": eor})
		elif arguments.get('typePattern') is not None:
			query.update({"type":
					{'$regex': arguments.get('typePattern')}
				})

		# Sets a id query
		if arguments.get('id') is not None:
			eor = []
			ids = arguments.get('id').split(",")
			if len(ids) == 1:
				query.update({"id":
						{'$in': [ids[0]]}
					})
			else:
				for eid in ids:
					eor.append({"id":
							{'$in': [eid]}
						})
				params.append({"$or": eor})
		elif arguments.get('idPattern') is not None:
			query.update({"id":
					{'$regex': arguments.get('idPattern')}
				})

		# Sets a category query
		if arguments.get('category') is not None:
			eor = []
			categories = arguments.get('category').split(",")
			if len(categories) == 1:
				query.update({"category.value":
						{'$in': [categories[0]]}
					})
			else:
				for category in categories:
					eor.append({"category.value":
							{'$in': [category]}
						})
				params.append({"$or": eor})

		# Sets a attrs query
		if arguments.get('attrs') is not None:
			attribs = arguments.get('attrs').split(",")
			for attr in attribs:
				fields.update({attr: True})

		# Sets a q query
		if arguments.get('q') is not None:
			qs = arguments.get('q').split(",")
			for q in qs:
				if "==" in q:
					qp = q.split("==")
					query.update({qp[0]: int(qp[1]) if qp[1].isdigit() else qp[1]})
				if  ":" in q:
					qp = q.split(":")
					query.update({qp[0]: int(qp[1]) if qp[1].isdigit() else qp[1]})
				if "!=" in q:
					qp = q.split("!=")
					query.update({qp[0]: {"$ne": int(qp[1]) if qp[1].isdigit() else qp[1]}})
				if "<" in q:
					qp = q.split("<")
					query.update({qp[0]: {"$lt": int(qp[1])}})
				if "<=" in q:
					qp = q.split("<=")
					query.update({qp[0]: {"$lte": int(qp[1])}})
				if ">" in q:
					qp = q.split("<")
					query.update({qp[0]: {"$gt": int(qp[1])}})
				if ">=" in q:
					qp = q.split(">=")
					query.update({qp[0]: {"$gte": int(qp[1])}})

		# Sets a geospatial query
		if arguments.get('georel') is not None and arguments.get('geometry') is not None and arguments.get('coords') is not None:
			georels = arguments.get('georel').split(";")
			georelslen = len(georels)
			coords = arguments.get('coords').split(";")
			coordslen = len(coords)
			geometry = arguments.get('geometry').capitalize()
			geotype = georels[0]
			if geotype == 'near':
				# Near geospatial query
				if geometry != "Point":
					return self.respond(400, self.helpers.confs["errorMessages"][str(400)])

				if georelslen < 2:
					return self.respond(400, self.helpers.confs["errorMessages"][str(400)])

				if coordslen > 1:
					return self.respond(400, self.helpers.confs["errorMessages"][str(400)])

				data = {"location.value": {
					"$near": {
						"$geometry": {
							"type": geometry,
							"coordinates": [float(p) for p in coords[0].split(",")]
						}
					}
				}}

				modifiers = georels[1:]
				for modifier in modifiers:
					msplit = modifier.split(":")
					data["location.value"]["$near"].update({"$"+msplit[0]: int(msplit[1])})
				query.update(data)
			elif geotype == 'intersects':
				# Intersects geospatial query
				if geometry != "Polygone":
					return self.respond(400, self.helpers.confs["errorMessages"][str(400)])

				if coordslen > 4:
					return self.respond(400, self.helpers.confs["errorMessages"][str(400)])

				polygone = []
				for poly in coords:
					polygone.append([float(p) for p in poly.split(",")])

				query.update({"location.value": {
					"$geoIntersects": {
						"$geometry": {
							"type": geometry,
							"coordinates": polygone
						}
					}
				}})
			elif geotype == 'coveredBy':
				# coveredBy geospatial query
				if geometry != "Polygone":
					return self.respond(400, self.helpers.confs["errorMessages"][str(400)])

				if coordslen > 4:
					return self.respond(400, self.helpers.confs["errorMessages"][str(400)])

				polygone = []
				for poly in coords:
					polygone.append([float(p) for p in poly.split(",")])

				query.update({"location.value": {
					"$geoWithin": {
						"$geometry": {
							"type": geometry,
							"coordinates": polygone
						}
					}
				}})
			elif geotype == 'equals':
				# Equals geospatial query
				eor = []
				coords = arguments.get('coords').split(";")
				for coord in coords:
					coord = coord.split(",")
					eor.append({"location.value.coordinates": [
								float(coord[0]), float(coord[1])]})
				params.append({"$or": eor})
			elif geotype == 'disjoint':
				# Disjoint geospatial query
				return self.respond(501, self.helpers.confs["errorMessages"][str(501)])
			else:
				# None supported geospatial query
				return self.respond(400, self.helpers.confs["errorMessages"][str(400)])

		# TO REMOVE
		if arguments.get('values') is not None:
			valuesArr = arguments.get('values').split(",")
			for value in valuesArr:
				pair = value.split("|")
				query.update({pair[0]: int(pair[1]) if pair[1].isdigit() else pair[1]})


		if len(params):
			query.update({"$and": params})

		# Sets the query ordering
		if arguments.get('orderBy') is not None:
			orders = arguments.get('orderBy').split(",")
			for order in orders:
				if order[0] is "!":
					orderBy = -1
					order = order[1:]
				else:
					orderBy = 1
				sort.append((order, orderBy))

		# Prepares the offset
		if arguments.get('offset') is None:
			offset = False
		else:
			offset = int(arguments.get('offset'))

		# Prepares the query limit
		if arguments.get('limit') is None:
			limit = 0
		else:
			limit = int(arguments.get('limit'))

		try:
			# Creates the full query
			if len(sort) and offset:
				entities = list(self.mongodb.mongoConn.Entities.find(
					query, fields).skip(offset).sort(sort).limit(limit))
			elif offset:
				entities = list(self.mongodb.mongoConn.Entities.find(
					query, fields).skip(offset).limit(limit))
			elif len(sort):
				entities = list(self.mongodb.mongoConn.Entities.find(
					query, fields).sort(sort).limit(limit))
			else:
				entities=list(self.mongodb.mongoConn.Entities.find(query, fields).limit(limit))

			if not len(entities):
				self.helpers.logger.info(
					self.program + " 404: " + self.helpers.confs["errorMessages"][str(404)]["Description"])

				return self.respond(404, self.helpers.confs["errorMessages"][str(404)])
			else:
				self.helpers.logger.info(
					self.program + " 200: " + self.helpers.confs["successMessage"][str(200)]["Description"])

				return self.respond(200, json.loads(json_util.dumps(entities)))
		except:
			self.helpers.logger.info(
				self.program + " 404: " + self.helpers.confs["errorMessages"][str(404)]["Description"])

			return self.respond(404, self.helpers.confs["errorMessages"][str(404)])

	def getEntity(self, typeof, _id, attrs):
		""" Gets a specific HIASCDI Entity.

		References:
			FIWARE-NGSI v2 Specification
			https://fiware.github.io/specifications/ngsiv2/stable/

			Reference
				- Entities
					- Entity by ID
						- Retrieve Entity
		"""

		query = {'id': _id}
		fields = {'_id': False}

		if attrs is not None:
			attribs = attrs.split(",")
			for attr in attribs:
				fields.update({attr: True})

		if typeof is not None:
			query.update({"type": typeof})

		entity = list(self.mongodb.mongoConn.Entities.find(query, fields))

		if not entity:
			self.helpers.logger.info(
				self.program + " 404: " + self.helpers.confs["errorMessages"][str(404)]["Description"])

			return self.respond(404, self.helpers.confs["errorMessages"][str(404)])
		elif len(entity) > 1:
			self.helpers.logger.info(
				self.program + " 409: " + self.helpers.confs["errorMessages"][str(409)]["Description"])

			return self.respond(409, self.helpers.confs["errorMessages"][str(409)])
		else:
			self.helpers.logger.info(
				self.program + " 200: " + self.helpers.confs["successMessage"][str(200)]["Description"])

			return self.respond(200, json.loads(json_util.dumps(entity[0])))

	def createEntity(self, data):
		""" Creates a new HIASCDI Entity.

		References:
			FIWARE-NGSI v2 Specification
			https://fiware.github.io/specifications/ngsiv2/stable/

			Reference
				- Entities
					- Create Entity
		"""

		if data["type"] not in self.mongodb.collextions:
			data["type"] = "Thing"

		_id = self.insert(self.mongodb.mongoConn.Entities, data, data["type"])

		if str(_id) is not False:
			resp = {
				"Response": "OK",
				"ID": str(_id),
				"Entity": json.loads(json_util.dumps(data))
			}
			return self.respond(201, resp, "v1/entities/" + data["id"] + "?type=" + data["type"])
		else:
			return self.respond(400, self.helpers.confs["errorMessages"][str(400)])

	def updateEntityPost(self, _id, typeof, data):
		""" Updates an HIASCDI Entity.

		References:
			FIWARE-NGSI v2 Specification
			https://fiware.github.io/specifications/ngsiv2/stable/

			Reference
				- Entities
					- Entity by ID
						- Update or Append Entity Attributes
		"""

		updated = False

		if "id" in data:
			del data['id']

		if "type" in data:
			del data['type']

		for update in data:
			self.mongodb.mongoConn.Entities.update_one({"id" : _id}, {"$set": {update: data[update]}}, upsert=True)
			updated = True

		if updated:
			return self.respond(204, self.helpers.confs["successMessage"][str(204)])
		else:
			return self.respond(400, self.helpers.confs["errorMessages"][str(400)])

	def updateEntityPatch(self, _id, typeof, data):
		""" Updates an HIASCDI Entity.

		References:
			FIWARE-NGSI v2 Specification
			https://fiware.github.io/specifications/ngsiv2/stable/

			Reference
				- Entities
					- Entity by ID
						- Update Existing Entity Attributes
		"""

		failed = False

		if "id" in data:
			del data['id']

		if "type" in data:
			del data['type']

		for update in data:
			updated = self.mongodb.mongoConn.Entities.update_one({"id" : _id}, {"$set": {update: data[update]}});
			if updated.matched_count == 0:
				failed = True

		if failed:
			return self.respond(400, self.helpers.confs["errorMessages"][str(400)])
		else:
			return self.respond(204, self.helpers.confs["successMessage"][str(204)])

	def updateEntityPut(self, _id, typeof, data):
		""" Updates an HIASCDI Entity.

		References:
			FIWARE-NGSI v2 Specification
			https://fiware.github.io/specifications/ngsiv2/stable/

			Reference
				- Entities
					- Entity by ID
					- Replace all entity attributes
		"""

		updated = False

		if "id" in data:
			del data['id']

		if "type" in data:
			del data['type']

		entity = list(self.mongodb.mongoConn.Entities.find({"id" : _id}))

		for update in data:
			if update in entity[0]:
				self.mongodb.mongoConn.Entities.update({"id" : _id}, {'$unset': {update: ""}})
			updated = self.mongodb.mongoConn.Entities.update_one({"id" : _id}, {"$set": {update: data[update]}}, upsert=True);

		if failed:
			return self.respond(400, self.helpers.confs["errorMessages"][str(400)])
		else:
			return self.respond(204, self.helpers.confs["successMessage"][str(204)])

	def deleteEntity(self, typeof, _id):
		""" Deletes an HIASCDI Entity.

		References:
			FIWARE-NGSI v2 Specification
			https://fiware.github.io/specifications/ngsiv2/stable/

			Reference
				- Entities
					- Entity by ID
					- Remove entity
		"""

		if typeof in self.mongodb.collextions:
			collection = self.mongodb.collextions[typeof]
		else:
			return self.respond(400, self.helpers.confs["errorMessages"][str(400)])

		deleted = False
		result = collection.delete_one({"id": _id});

		if result.deleted_count is True:
			self.helpers.logger.info("Mongo data delete OK")
			return self.respond(204, {})
		else:
			self.helpers.logger.info("Mongo data delete FAILED")
			return self.respond(400, self.helpers.confs["errorMessages"][str(400)])

	def insert(self, collection, doc, entity):
		""" Creates an HIASCDI Entity.

		References:
			FIWARE-NGSI v2 Specification
			https://fiware.github.io/specifications/ngsiv2/stable/

			Reference
				- Entities
					- Entity by ID
					- Remove entity
		"""

		try:
			_id = collection.insert(doc)
			self.helpers.logger.info("Mongo data inserted OK")
			if entity is "Device":
				self.mongodb.Locations.find_one_and_update(
						{"id": doc.lid.entity},
						{'$inc': {'devices.value': 1}}
					)
				self.mongodb.Zones.find_one_and_update(
						{"id": doc.zid.entity},
						{'$inc': {'devices.value': 1}}
					)
			if entity is "Application":
				self.mongodb.Locations.find_one_and_update(
						{"id": doc.lid.entity},
						{'$inc': {'applications.value': 1}}
					)
				self.helpers.logger.info("Mongo data update OK")
			return _id
		except:
			e = sys.exc_info()
			self.helpers.logger.info("Mongo data inserted FAILED!")
			self.helpers.logger.info(str(e))
			return False

	def respond(self, responseCode, response, location=None):
		""" Builds the request repsonse """

		return Response(response=json.dumps(response, indent=4), status=responseCode,
						mimetype="application/json")
