# Raspberry Pi (RPi) Python Heating, Ventilation, Air Conditioning (HVAC)

RPi HVAC control middleware for a cafe

1. `docker stop flask-hvac`
2. `docker rm flask-hvac` 
3. `docker build --tag flask-hvac-container -f flask_server/Dockerfile .` (optionally with `--no-cache`)
4. `sudo docker run -p 9025:9025 -d --restart=always --network=nginx_proxy --rm --name flask-hvac flask-hvac-container`
