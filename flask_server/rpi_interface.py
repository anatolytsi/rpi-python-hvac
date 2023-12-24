import os
import time
from threading import Thread, Lock
from typing import Callable
from dataclasses import dataclass

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


@dataclass
class RpiState:
    he_temperatures: list
    feed_temperature: float
    hysteresis: int
    outside_temperature: float
    inside_temperature: float
    valves_states: list
    valves_activated_states: list
    mode: str


class HvacRpi:
    def __init__(self, log = None):
        self._he_temperatures = [.0, .0, .0]
        self._outside_temperature = .0
        self._inside_temperature = .0
        self._valves_states = [False, False, False, False]
        self._valves_activated_states = [True, True, True, True]
        self._feed_temperature = 0
        self._hysteresis = .0
        self._mode = Mode.MANUAL
        self._updater_thread = None
        self._pr_lock = Lock()
        self._last_refresh_timestamp = 0
        self._update_after = 30
        if log is not None:
            self.log = log.info
        else:
            self.log = self.log

    def _update_values(self):
        with self._pr_lock:
            self.log('Starting update')
            for num, temperature in enumerate(self._he_temperatures):
                self._he_temperatures[num] = get_he_temperature(num + 1)
            self._outside_temperature = get_outside_temperature()
            self._inside_temperature = get_inside_temperature()
            for num, valve_state in enumerate(self._valves_states):
                self._valves_states[num] = get_valve_opened(num + 1)
            for num, valve_activated_state in enumerate(self._valves_activated_states):
                self._valves_activated_states[num] = get_valve_activated(num + 1)
            self._feed_temperature = get_feed_temperature()
            self._hysteresis = get_hysteresis()
            self._mode = get_mode()
            self.log('Update finished')

    def _updater(self):
        self.log('Starting thread')
        while True:
            self._update_values()
            time.sleep(self._update_after)

    def start_updater(self):
        self.log('Requesting an update')
        self._updater_thread = Thread(daemon=True, target=self._updater)
        self._updater_thread.start()

    def _get_param_value(self, param_name: str, updater: Callable, num: int = None):
        if param_name not in self.__dict__:
            raise Exception(f'Class parameter {param_name} is undefined')
        if isinstance(self.__dict__[param_name], list):
            if num is None:
                raise Exception(f'Number argument should be defined when list is passed')
            self.log(f'{param_name} {num} = {self.__dict__[param_name][num - 1]}')
            return self.__dict__[param_name][num - 1]
        else:
            self.log(f'{param_name} = {self.__dict__[param_name]}')
            return self.__dict__[param_name]

    def get_he_temperature(self, number: int) -> float:
        # return get_he_temperature(number)
        return self._get_param_value('_he_temperatures', get_he_temperature, number)

    def get_outside_temperature(self) -> float:
        # return get_outside_temperature()
        return self._get_param_value('_outside_temperature', get_outside_temperature)

    def get_inside_temperature(self) -> float:
        # return get_inside_temperature()
        return self._get_param_value('_inside_temperature', get_inside_temperature)

    def get_valve_opened(self, number: int) -> bool:
        # return get_valve_opened(number)
        return self._get_param_value('_valves_states', get_valve_opened, number)

    def get_feed_temperature(self) -> float:
        # return get_feed_temperature()
        return self._get_param_value('_feed_temperature', get_feed_temperature)

    def set_feed_temperature(self, temperature) -> bool:
        return set_feed_temperature(temperature)

    def get_hysteresis(self) -> float:
        # return get_hysteresis()
        return self._get_param_value('_hysteresis', get_hysteresis)

    def set_hysteresis(self, hysteresis) -> bool:
        return set_hysteresis(hysteresis)

    def get_mode(self) -> Mode:
        # return get_mode()
        return self._get_param_value('_mode', get_mode)

    def set_mode(self, mode: Mode) -> bool:
        return set_mode(mode)

    def get_valve_activated(self, number) -> bool:
        # return get_valve_activated(number)
        return self._get_param_value('_valves_activated_states', get_valve_activated, number)

    def set_valve_activated(self, number, activated) -> bool:
        return set_valve_activated(number, activated)

    def open_valve(self, number: int):
        return open_valve(number)

    def close_valve(self, number: int):
        return close_valve(number)

    def get_full_state(self) -> RpiState:
        rpiState = RpiState(
            he_temperatures=self._he_temperatures,
            feed_temperature=self._feed_temperature,
            hysteresis=self._hysteresis,
            outside_temperature=self._outside_temperature,
            inside_temperature=self._inside_temperature,
            valves_states=self._valves_states,
            valves_activated_states=self._valves_activated_states,
            mode=self._mode.value
        )
        self.log(rpiState)
        return rpiState


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
    # self.log(get_he_temperature(1))
    self.log(close_valve(1))


if __name__ == '__main__':
    main()
