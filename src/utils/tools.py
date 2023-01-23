from pytz import timezone, UTC
from datetime import timedelta
import time, datetime
import random
import uuid
from flask import Response
import json
from sqlalchemy.ext.declarative import DeclarativeMeta
from uuid import UUID
from decimal import Decimal


class MultipleJsonEncoders():
    """
    Combine multiple JSON encoders
    """
    def __init__(self, *encoders):
        self.encoders = encoders
        self.args = ()
        self.kwargs = {}

    def default(self, obj):
        for encoder in self.encoders:
            try:
                return encoder(*self.args, **self.kwargs).default(obj)
            except TypeError:
                pass
        raise TypeError(f'Object of type {obj.__class__.__name__} is not JSON serializable')

    def __call__(self, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs
        enc = json.JSONEncoder(*args, **kwargs)
        enc.default = self.default
        return enc

class AlchemyEncoder(json.JSONEncoder):

    def default(self, obj):
        if isinstance(obj.__class__, DeclarativeMeta):
            # an SQLAlchemy class
            fields = {}
            for field in [x for x in dir(obj) if not x.startswith('_') and x != 'metadata']:
                data = obj.__getattribute__(field)
                try:
                    json.dumps(data) # this will fail on non-encodable values, like other classes
                    fields[field] = data
                except TypeError:
                    fields[field] = None
            # a json-encodable dict
            return fields
		
        return super().default(obj)

class JsonDecimalEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, Decimal):
            return o.__str__()
        return super().default(o)

def nowDatetimeUserTimezone(user_timezone):
	tzone = timezone(user_timezone)
	return datetime.datetime.now(tzone)
	
def nowDatetimeUTC():
	tzone = UTC
	now = datetime.datetime.now(tzone)
	return now

def JsonResp(data, status):
	return Response(json.dumps(data,cls=MultipleJsonEncoders(AlchemyEncoder, JsonDecimalEncoder)), mimetype="application/json", status=status)

def SocketResp(data):
	return json.dumps(data, indent=4, sort_keys=True, default=str)

def randID():
	randId = uuid.uuid4().hex
	return randId

def randString(length):
	randString = ""
	for _ in range(length):
		randString += random.choice("AaBbCcDdEeFfGgHhIiJjKkLlMmNnOoPpQqRrSsTtUuVvWwXxYyZz1234567890")

	return randString

def randStringCaps(length):
	randString = ""
	for _ in range(length):
		randString += random.choice("ABCDEFGHJKLMNPQRSTUVWXYZ23456789")

	return randString

def randStringNumbersOnly(length):
	randString = ""
	for _ in range(length):
		randString += random.choice("23456789")

	return randString

def validateEmail(email):
	import re

	if re.match("^.+\\@(\\[?)[a-zA-Z0-9\\-\\.]+\\.([a-zA-Z]{2,3}|[0-9]{1,3})(\\]?)$", email) != None:
		return True
	else:
		return False

def validatePassword(password):
	import re

	if re.match("^(?=.*[a-z])(?=.*[A-Z])(?=.*\\d)(?=.*(_|[\\W])).+$", password) != None:
		return True
	else:
		return False