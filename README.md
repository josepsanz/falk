<p align="center">
  <img src="static/falk.webp" alt="falk" width="350"/>
</p>

# Falk
Falk was conceived due to the need to save electricity consumption. It aims to be a planner, controller, and manager of a space's electricity consumption

## Installation
``` bash
uv sync
```

## Setup
``` bash
source .venv/bin/activate
tinytuya scan
```

After that, you will get a list of devices with their `id` but without the `local_key`. 
You will need to log In in (https://platform.tuya.com/)[Tuya Platform] and after that 
go to (https://eu.platform.tuya.com/cloud/explorer)[Tuya API Explorer] to retrieve the `local_key`. 

<p align="center">
  <img src="static/tuya-local_key.png" alt="tuya local_key" width="600"/>
</p>
