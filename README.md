<p align="center">
  <img src="static/falk.webp" alt="falk" width="350"/>
</p>

# Falk
Falk was conceived due to the need to save electricity consumption. 
It aims to be a planner, controller, and manager of a space's electricity consumption.

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
You will need to log In in [Tuya Platform](https://platform.tuya.com/) and after that 
go to [Tuya API Explorer](https://eu.platform.tuya.com/cloud/explorer) to retrieve the `local_key`. 

![tuya local_key](static/tuya-local_key.png)

## Database

### New Database Tables
New database tables can be created with:
```bash
alembic upgrade head
```

### Database Migrations

Database migrations can be created with:
```bash
uv run -- alembic revision --autogenerate -m "message"
uv run -- alembic upgrade head
```

### Some Database Queries
```sql
SELECT 
    s.name, 
    sm.current, 
    sm.voltage, 
    sm.power, 
    sm.recorded_at
FROM 
    switch_metric sm
JOIN 
    smart_switch s ON sm.switch_id = s.id
ORDER BY 
    sm.recorded_at DESC
LIMIT 15;
```

or in a single line:
```sql
SELECT s.name, sm.current, sm.voltage, sm.power, sm.recorded_at FROM switch_metric sm JOIN smart_switch s ON sm.switch_id = s.id ORDER BY sm.recorded_at DESC LIMIT 15;
```

Query Energy Meter metrics
```sql
SELECT * FROM energy_meter JOIN em_metric ON energy_meter.id = em_metric.em_id JOIN energy_phase ON em_metric.id = energy_phase.em_metric_id
```

### Examples how to add devices
```python
from falk import telemetry

telemetry.add_em_device('sqlite:///falk.db', name='Energy Meter SAXI Home', model='Shelly 3EM-63W', ip='192.168.1.132', shelly_id='em:0')
telemetry.add_switch_device('sqlite:///falk.db', name='TSP004-20A-daewoo', ip='192.168.1.118', tuya_id='*', local_key='*', version='3.5')
```


## Telemetry Cronjob
```bash
#!/usr/bin/env bash

cd $HOME/repos/falk

uv run -- python -m falk.telemetry
```

then in Crontab:
```bash
*/5 * * * * sh $HOME/falk-telemetry-cronjob.sh &> /dev/null
```



