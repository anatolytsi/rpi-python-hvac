import base64
import os
import hashlib
import dataclasses
import functools
from enum import Enum

from dotenv import load_dotenv
from flask import request, make_response, Response
from flask_restful import Resource, reqparse
from flask_basic_roles import BasicRoleAuth

from rpi_interface import Mode as OpMode

load_dotenv()

basic_username = os.getenv('USERNAME')
basic_password = os.getenv('PASSWORD')
basic_username_hash = f'{hashlib.md5(os.getenv("USERNAME").encode("utf-8")).hexdigest()}'
basic_password_hash = f'{hashlib.md5(os.getenv("PASSWORD").encode("utf-8")).hexdigest()}'

su_username = os.getenv('SU_USERNAME')
su_password = os.getenv('SU_PASSWORD')
su_username_hash = f'{hashlib.md5(os.getenv("SU_USERNAME").encode("utf-8")).hexdigest()}'
su_password_hash = f'{hashlib.md5(os.getenv("SU_PASSWORD").encode("utf-8")).hexdigest()}'

auth = BasicRoleAuth()
auth.add_user(user=basic_username, password=basic_password, roles='user')
auth.add_user(user=basic_username_hash, password=basic_password_hash, roles='user')
auth.add_user(user=su_username, password=su_password, roles='superuser')
auth.add_user(user=su_username_hash, password=su_password_hash, roles='superuser')


def cross_origin(origin="*"):
    def cross_origin(func):
        @functools.wraps(func)
        def _decoration(*args, **kwargs):
            ret = func(*args, **kwargs)
            _cross_origin_header = {"Access-Control-Allow-Origin": origin,
                                    "Access-Control-Allow-Headers":
                                        "Origin, X-Requested-With, Content-Type, Accept"}
            if isinstance(ret, tuple):
                if len(ret) == 2 and isinstance(ret[0], dict) and isinstance(ret[1], int):
                    # this is for handle response like: ```{'status': 1, "data":"ok"}, 200```
                    return ret[0], ret[1], _cross_origin_header
                elif isinstance(ret, str):
                    response = make_response(ret)
                    response.headers["Access-Control-Allow-Origin"] = origin
                    response.headers["Access-Control-Allow-Headers"] = "Origin, X-Requested-With, Content-Type, Accept"
                    return response
                elif isinstance(ret, Response):
                    ret.headers["Access-Control-Allow-Origin"] = origin
                    ret.headers["Access-Control-Allow-Headers"] = "Origin, X-Requested-With, Content-Type, Accept"
                    return ret
                else:
                    raise ValueError("Cannot handle cross origin, because the return value is not matched!")
            return ret

        return _decoration

    return cross_origin


def catch_error(func):
    """
    Error catching decorator
    :param func: function to decorate
    :return: Flask response
    """

    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            error, status = e, 500
        return str(error), status

    return wrapper


class TemperatureHe(Resource):
    hvac = None

    @catch_error
    @cross_origin()
    @auth.require(roles=('user', 'superuser'))
    def get(self, number):
        return self.hvac.get_he_temperature(number)


class TemperatureOutside(Resource):
    hvac = None

    @catch_error
    @cross_origin()
    @auth.require(roles=('user', 'superuser'))
    def get(self):
        return self.hvac.get_outside_temperature()


class TemperatureInside(Resource):
    hvac = None

    @catch_error
    @cross_origin()
    @auth.require(roles=('user', 'superuser'))
    def get(self):
        return self.hvac.get_inside_temperature()


class TemperatureFeed(Resource):
    hvac = None

    @catch_error
    @cross_origin()
    @auth.require(roles=('user', 'superuser'))
    def get(self):
        return self.hvac.get_feed_temperature()

    @catch_error
    @cross_origin()
    @auth.require(roles=('user', 'superuser'))
    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument('value', type=float, help='Feed temperature value')
        args = parser.parse_args()
        return self.hvac.set_feed_temperature(args.value)


class Hysteresis(Resource):
    hvac = None

    @catch_error
    @cross_origin()
    @auth.require(roles=('user', 'superuser'))
    def get(self):
        return self.hvac.get_hysteresis()

    @catch_error
    @cross_origin()
    @auth.require(roles=('superuser',))
    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument('value', type=int, help='Hysteresis value')
        args = parser.parse_args()
        return self.hvac.set_hysteresis(args.value)


class Mode(Resource):
    hvac = None

    @catch_error
    @cross_origin()
    @auth.require(roles=('user', 'superuser'))
    def get(self):
        return self.hvac.get_mode().value

    @catch_error
    @cross_origin()
    @auth.require(roles=('superuser',))
    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument('type', type=str, help='Operation mode')
        args = parser.parse_args()
        mode_type = OpMode(args.type)
        return self.hvac.set_mode(mode_type)


class ValveAction(Enum):
    open = 'open'
    close = 'close'


class Valve(Resource):
    hvac = None

    @catch_error
    @cross_origin()
    @auth.require(roles=('user', 'superuser'))
    def get(self, number):
        return self.hvac.get_valve_opened(number)

    @catch_error
    @cross_origin()
    @auth.require(roles=('superuser',))
    def post(self, number):
        parser = reqparse.RequestParser()
        parser.add_argument('action', type=str, help='Valve action type')
        args = parser.parse_args()
        valve_action = ValveAction(args.action)
        if valve_action.value == 'open':
            return self.hvac.open_valve(number)
        elif valve_action.value == 'close':
            return self.hvac.close_valve(number)
        else:
            raise Exception(f'Incorrect action name {args.action.value}')


class ValveActivated(Resource):
    hvac = None

    @catch_error
    @cross_origin()
    @auth.require(roles=('user', 'superuser'))
    def get(self, number):
        return self.hvac.get_valve_activated(number)

    @catch_error
    @cross_origin()
    @auth.require(roles=('superuser',))
    def post(self, number):
        parser = reqparse.RequestParser()
        parser.add_argument('value', type=bool, help='Is valve activated')
        args = parser.parse_args()
        return self.hvac.set_valve_activated(number, args.value)


class FullState(Resource):
    hvac = None

    @catch_error
    @cross_origin()
    @auth.require(roles=('user', 'superuser'))
    def get(self):
        return dataclasses.asdict(self.hvac.get_full_state())


class SuAccess(Resource):
    @staticmethod
    @cross_origin()
    @auth.require(roles=('user', 'superuser'))
    def get():
        token = request.headers['Authorization']
        username, password = base64.b64decode(token.split('Basic ')[-1]).decode('utf-8').split(':')
        if username in [su_username, su_username_hash]:
            return True
        return False
