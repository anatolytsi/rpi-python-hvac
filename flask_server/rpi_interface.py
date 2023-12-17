import os
import time
from threading import Thread, Lock
from typing import Callable

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


class HvacRpi:
    def __init__(self):
        self._he_temperatures = [.0, .0, .0]
        self._outside_temperature = .0
        self._inside_temperature = .0
        self._valves_states = [False, False, False, False]
        self._valves_activated_states = [True, True, True, True]
        self._feed_temperature = 0
        self._hysteresis = .0
        self._mode = Mode.MANUAL
        self._values_fresh = False
        self._updater_thread = None
        self._lock = Lock()
        self._update_interval = 5000
        self._update_stop_after = 300000

    def _updater(self):
        self._values_fresh = True
        counter = 0
        exit_counter = self._update_stop_after // self._update_interval
        while counter < exit_counter:
            with self._lock:
                for num, temperature in enumerate(self._he_temperatures):
                    self._he_temperatures[num] = get_he_temperature(num + 1)
                self._outside_temperature = get_outside_temperature()
                self._inside_temperature = get_inside_temperature()
                for num, valve_state in enumerate(self._valves_states):
                    self._valves_states[num] = get_valve_opened(num + 1)
                self._feed_temperature = get_feed_temperature()
                self._hysteresis = get_hysteresis()
                self._mode = get_mode()
            time.sleep(self._update_interval)
            counter += 1
        self._values_fresh = False

    def _start_updater(self):
        self._updater_thread = Thread(daemon=True, target=self._updater)
        self._updater_thread.start()

    def _get_param_value(self, param_name: str, updater: Callable, num: int = None):
        if param_name not in self.__dict__:
            raise Exception(f'Class parameter {param_name} is undefined')
        with self._lock:
            if isinstance(self.__dict__[param_name], list):
                if num is None:
                    raise Exception(f'Number argument should be defined when list is passed')
                if not self._values_fresh:
                    self.__dict__[param_name][num - 1] = updater(num)
                    self._start_updater()
                return self.__dict__[param_name][num - 1]
            else:
                if not self._values_fresh:
                    self.__dict__[param_name] = updater()
                    self._start_updater()
                return self.__dict__[param_name]

    def _set_param_value(self, setter: Callable, *args):
        with self._lock:
            if not self._values_fresh:
                self._start_updater()
            return setter(*args)

    def get_he_temperature(self, number: int) -> float:
        return self._get_param_value('_he_temperatures', get_he_temperature, number)

    def get_outside_temperature(self) -> float:
        return self._get_param_value('_outside_temperature', get_outside_temperature)

    def get_inside_temperature(self) -> float:
        return self._get_param_value('_inside_temperature', get_inside_temperature)

    def get_valve_opened(self, number: int) -> bool:
        return self._get_param_value('_valves_states', get_valve_opened, number)

    def get_feed_temperature(self) -> float:
        return self._get_param_value('_feed_temperature', get_feed_temperature)

    def set_feed_temperature(self, temperature) -> bool:
        return self._set_param_value(set_feed_temperature, temperature)

    def get_hysteresis(self) -> float:
        return self._get_param_value('_hysteresis', get_hysteresis)

    def set_hysteresis(self, hysteresis) -> bool:
        return self._set_param_value(set_hysteresis, hysteresis)

    def get_mode(self) -> Mode:
        return self._get_param_value('_mode', get_mode)

    def set_mode(self, mode: Mode) -> bool:
        return self._set_param_value(set_mode, mode)
    
    def get_valve_activated(self, number) -> bool:
        return self._get_param_value('_valves_activated_states', get_valve_activated, number)
    
    def set_valve_activated(self, number, activated) -> bool:
        return self._set_param_value(set_valve_activated, number, activated)

    def open_valve(self, number: int):
        return self._set_param_value(open_valve, number)

    def close_valve(self, number: int):
        return self._set_param_value(close_valve, number)


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
    return Mode(response.json())


def set_mode(mode: Mode):
    """
    Sets operation mode
    :param mode: operation mode
    :return: operation success
    """
    response = make_request('put', f'{HVAC_URL}/properties/mode', data=mode.value)
    return response.status_code // 100 == 2


def get_valve_activated(number: int) -> Mode:
    """
    Gets valve activated status
    :return: valve activated status
    """
    response = make_request('get', f'{HVAC_URL}/properties/valveActivated{number}')
    return response.json()


def set_valve_activated(number: int, activated: bool):
    """
    Sets valve activated status
    :param number: valve number
    :param activated: is valve activated
    :return: operation success
    """
    response = make_request('put', f'{HVAC_URL}/properties/valveActivated{number}', data=activated)
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
