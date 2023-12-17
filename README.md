# Raspberry Pi (RPi) Python Heating, Ventilation, Air Conditioning (HVAC)

RPi HVAC control middleware for a cafe

1. `docker stop flask-hvac`
2. `docker rm flask-hvac` 
3. `docker build --tag flask-hvac-container -f flask_server/Dockerfile .` (optionally with `--no-cache`)
4. `docker run -p 5000:5000 --name flask-hvac flask-hvac-container`
