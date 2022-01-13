import os
import configparser

from flask import Flask
from flask_cors import CORS
from flask_restful import Api

from resources import TemperatureHe, TemperatureOutside, TemperatureInside, TemperatureFeed, Hysteresis, Mode, Valve, \
    SuAccess


class Server:
    def __init__(self, host, port, debug):
        self.host = host
        self.port = port
        self.debug = debug
        self.app = Flask(__name__)
        cors = CORS(self.app, resources={r"/*": {"origins": "*"}})
        self.api = Api(self.app)
        self.api.add_resource(TemperatureHe, '/temperatureHe/<int:number>')
        self.api.add_resource(TemperatureOutside, '/temperatureOutside')
        self.api.add_resource(TemperatureInside, '/temperatureInside')
        self.api.add_resource(TemperatureFeed, '/temperatureFeed')
        self.api.add_resource(Hysteresis, '/hysteresis')
        self.api.add_resource(Mode, '/mode')
        self.api.add_resource(Valve, '/valve/<int:number>')
        self.api.add_resource(SuAccess, '/suAccess')

    def run(self):
        self.app.run(self.host, self.port, self.debug)


def main():
    config = configparser.ConfigParser()
    config.read(f'{os.path.dirname(os.path.abspath(__file__))}/server.ini')
    server = Server(host=config['DEFAULT']['Host'],
                    port=config.getint('DEFAULT', 'Port'),
                    debug=config.getboolean('DEFAULT', 'Debug'))
    server.run()


if __name__ == '__main__':
    main()
