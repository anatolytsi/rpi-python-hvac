import os

import requests
import enum

from dotenv import load_dotenv

load_dotenv()

RPI_HOST = host if 'http://' in (host := os.getenv('RPI_HOST')) else f'http://{host}'
HVAC_NAME = os.getenv('HVAC_NAME')
HVAC_URL = f'{RPI_HOST}/{HVAC_NAME}'


class Mode(enum.Enum):
    MANUAL = 'manual'
    AUTO_WINTER = 'autoWinter'
    AUTO_SUMMER = 'autoSummer'


def make_request(method: str, url, **kwargs) -> requests.Response:
    """
    Make a generic request
    :param method: request method, e.g. "get" or "post"
    :param url: request URL
    :param kwargs: request parameters, check requests.request function
    :return: requests.Response
    """
    response = requests.request(method, url, **kwargs)
    if response.status_code // 100 != 2:
        raise Exception(f'RPi replied with code {response.status_code}')
    return response


def get_he_temperature(number: int) -> float:
    """
    Gets heat exchanger temperature with a given number
    :param number: heat exchanger number
    :return: temperature in Celsius
    """
    if not (0 < number < 4):
        raise Exception(f'Heat exchanger can be 1-3, not {number}')
    response = make_request('get', f'{HVAC_URL}/properties/temperatureHe{number}')
    return response.json()


def get_outside_temperature() -> float:
    """
    Gets outside temperature with a given number
    :return: temperature in Celsius
    """
    response = make_request('get', f'{HVAC_URL}/properties/temperatureOutside')
    return response.json()


def get_inside_temperature() -> float:
    """
    Gets inside temperature with a given number
    :return: temperature in Celsius
    """
    response = make_request('get', f'{HVAC_URL}/properties/temperatureInside')
    return response.json()


def get_valve_opened(number: int) -> bool:
    """
    Gets valve state with a given number
    :param number: valve number
    :return: valve opened status
    """
    if not (0 < number < 5):
        raise Exception(f'Valve can be 1-4, not {number}')
    response = make_request('get', f'{HVAC_URL}/properties/valveOpened{number}')
    return response.json()


def get_feed_temperature():
    """
    Gets feed temperature
    :return: feed temperature
    """
    response = make_request('get', f'{HVAC_URL}/properties/temperatureFeed')
    return response.json()


def set_feed_temperature(temperature: int):
    """
    Sets feed temperature
    :param temperature: feed temperature
    :return: operation success
    """
    response = make_request('put', f'{HVAC_URL}/properties/temperatureFeed', data=f'{temperature}')
    return response.status_code // 100 == 2


def get_hysteresis():
    """
    Gets hysteresis
    :return: hysteresis
    """
    response = make_request('get', f'{HVAC_URL}/properties/hysteresis')
    return response.json()


def set_hysteresis(hysteresis: float):
    """
    Sets hysteresis
    :param hysteresis: hysteresis
    :return: operation success
    """
    response = make_request('put', f'{HVAC_URL}/properties/hysteresis', data=f'{hysteresis}')
    return response.status_code // 100 == 2


def get_mode() -> Mode:
    """
    Gets operation mode
    :return: operation mode
    """
    response = make_request('get', f'{HVAC_URL}/properties/mode')
    return response.json()


def set_mode(mode: Mode):
    """
    Sets operation mode
    :param mode: operation mode
    :return: operation success
    """
    response = make_request('put', f'{HVAC_URL}/properties/mode', data=mode.value)
    return response.status_code // 100 == 2


def open_valve(number: int):
    """
    Opens valve with a given number
    :param number: valve number
    :return: operation success
    """
    if not (0 < number < 5):
        raise Exception(f'Valve can be 1-4, not {number}')
    response = make_request('post', f'{HVAC_URL}/actions/openValve{number}')
    return response.status_code // 100 == 2


def close_valve(number: int):
    """
    Closes valve with a given number
    :param number: valve number
    :return: operation success
    """
    if not (0 < number < 5):
        raise Exception(f'Valve can be 1-4, not {number}')
    response = make_request('post', f'{HVAC_URL}/actions/closeValve{number}')
    return response.status_code // 100 == 2


def main():
    # print(get_he_temperature(1))
    print(close_valve(1))


if __name__ == '__main__':
    main()
