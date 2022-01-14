import base64
import os
import hashlib
from enum import Enum

from dotenv import load_dotenv
from flask import request
from flask_restful import Resource, reqparse
from flask_basic_roles import BasicRoleAuth

from rpi_interface import get_he_temperature, get_outside_temperature, get_inside_temperature, get_feed_temperature, \
    set_feed_temperature, get_hysteresis, set_hysteresis, get_mode, set_mode, get_valve_opened, open_valve, close_valve
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
    @staticmethod
    @catch_error
    @auth.require(roles=('user', 'superuser'))
    def get(number):
        return get_he_temperature(number)


class TemperatureOutside(Resource):
    @staticmethod
    @catch_error
    @auth.require(roles=('user', 'superuser'))
    def get():
        return get_outside_temperature()


class TemperatureInside(Resource):
    @staticmethod
    @catch_error
    @auth.require(roles=('user', 'superuser'))
    def get():
        return get_inside_temperature()


class TemperatureFeed(Resource):
    @staticmethod
    @catch_error
    @auth.require(roles=('user', 'superuser'))
    def get():
        return get_feed_temperature()

    @staticmethod
    @catch_error
    @auth.require(roles=('user', 'superuser'))
    def post():
        parser = reqparse.RequestParser()
        parser.add_argument('value', type=float, help='Feed temperature value')
        args = parser.parse_args()
        return set_feed_temperature(args.value)


class Hysteresis(Resource):
    @staticmethod
    @catch_error
    @auth.require(roles=('user', 'superuser'))
    def get():
        return get_hysteresis()

    @staticmethod
    @catch_error
    @auth.require(roles=('superuser',))
    def post():
        parser = reqparse.RequestParser()
        parser.add_argument('value', type=int, help='Hysteresis value')
        args = parser.parse_args()
        return set_hysteresis(args.value)


class Mode(Resource):
    @staticmethod
    @catch_error
    @auth.require(roles=('user', 'superuser'))
    def get():
        return get_mode()

    @staticmethod
    @catch_error
    @auth.require(roles=('superuser',))
    def post():
        parser = reqparse.RequestParser()
        parser.add_argument('type', type=OpMode, help='Operation mode')
        args = parser.parse_args()
        return set_mode(args.type)


class ValveAction(Enum):
    open = 'open'
    close = 'close'


class Valve(Resource):
    @staticmethod
    @catch_error
    @auth.require(roles=('user', 'superuser'))
    def get(number):
        return get_valve_opened(number)

    @staticmethod
    @catch_error
    @auth.require(roles=('superuser',))
    def post(number):
        parser = reqparse.RequestParser()
        parser.add_argument('action', type=ValveAction, help='Valve action type')
        args = parser.parse_args()
        if args.action.value == 'open':
            return open_valve(number)
        elif args.action.value == 'close':
            return close_valve(number)
        else:
            raise Exception(f'Incorrect action name {args.action.value}')


class SuAccess(Resource):
    @staticmethod
    @auth.require(roles=('user', 'superuser'))
    def get():
        token = request.headers['Authorization']
        username, password = base64.b64decode(token.split('Basic ')[-1]).decode('utf-8').split(':')
        if username in [su_username, su_username_hash]:
            return True
        return False
