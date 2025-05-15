import logging
from datetime import timedelta
import homeassistant.helpers.event as event
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from .const import DOMAIN, CONF_SENSOR, CONF_THRESHOLD, CONF_DURATION, CONF_PRECIP_SENSOR, CONF_PRECIP_THRESHOLD, CONF_CHECK_INTERVAL, DEFAULT_CHECK_INTERVAL

_LOGGER = logging.getLogger(__name__)

async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    return True

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    conf = entry.data
    sensor = conf[CONF_SENSOR]
    threshold = conf[CONF_THRESHOLD]
    duration = conf[CONF_DURATION]
    precip_sensor = conf[CONF_PRECIP_SENSOR]
    precip_threshold = conf[CONF_PRECIP_THRESHOLD]
    interval = conf.get(CONF_CHECK_INTERVAL, DEFAULT_CHECK_INTERVAL)

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = {
        'remaining': duration * 60,
        'running': False,
        'sensor': sensor,
        'threshold': threshold,
        'precip_sensor': precip_sensor,
        'precip_threshold': precip_threshold,
        'interval': interval
    }

    def check_conditions(now):
        data = hass.data[DOMAIN][entry.entry_id]
        imp_exp = float(hass.states.get(data['sensor']).state)
        precip = float(hass.states.get(data['precip_sensor']).attributes.get('precipitation', 0))
        if not data['running'] and data['remaining'] > 0 and imp_exp < data['threshold'] and precip < data['precip_threshold']:
            dur = min(300, data['remaining'])
            _LOGGER.debug("Lancement arrosage %s secondes", dur)
            hass.services.call('script', 'arroser', {'duration': int(dur/60)})
            data['running'] = True

    def import_export_changed(event):
        entity = event.data.get('entity_id')
        if entity != hass.data[DOMAIN][entry.entry_id]['sensor']:
            return
        new_state = event.data.get('new_state')
        if not new_state:
            return
        val = float(new_state.state)
        data = hass.data[DOMAIN][entry.entry_id]
        if data['running'] and val > 0:
            _LOGGER.debug("Arrêt arrosage car import/export > 0")
            hass.services.call('switch', 'turn_off', {'entity_id': 'switch.arrosage'})
            data['running'] = False

    def complete_arrosage(now):
        data = hass.data[DOMAIN][entry.entry_id]
        if data['remaining'] > 0:
            _LOGGER.debug("Compléter arrosage à 22h de %s secondes", data['remaining'])
            hass.services.call('script', 'arroser', {'duration': int(data['remaining']/60)})

    def reset_arrosage(now):
        hass.data[DOMAIN][entry.entry_id]['remaining'] = duration * 60
        _LOGGER.debug("Reset compteur arrosage")

    event.track_time_interval(hass, check_conditions, timedelta(seconds=interval))
    hass.bus.async_listen('state_changed', import_export_changed)
    event.track_time_change(hass, complete_arrosage, hour=22, minute=0, second=0)
    event.track_time_change(hass, reset_arrosage, hour=0, minute=0, second=0)

    return True
```

```python
# Fichier: custom_components/arrosage/config_flow.py
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.helpers import selector
from .const import DOMAIN, CONF_SENSOR, CONF_THRESHOLD, CONF_DURATION, CONF_PRECIP_SENSOR, CONF_PRECIP_THRESHOLD, CONF_CHECK_INTERVAL

class ArrosageConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1
    async def async_step_user(self, user_input=None):
        if user_input is None:
            data_schema = vol.Schema({
                vol.Required(CONF_SENSOR): selector.EntitySelector(selector.EntitySelectorConfig(domain="sensor")),
                vol.Required(CONF_THRESHOLD, default=600): selector.NumberSelector(selector.NumberSelectorConfig(min=0, max=10000, unit_of_measurement="W")),
                vol.Required(CONF_DURATION, default=30): selector.NumberSelector(selector.NumberSelectorConfig(min=1, max=1440, unit_of_measurement="min")),
                vol.Required(CONF_PRECIP_SENSOR): selector.EntitySelector(selector.EntitySelectorConfig(domain="weather")),
                vol.Required(CONF_PRECIP_THRESHOLD, default=10): selector.NumberSelector(selector.NumberSelectorConfig(min=0, max=100, unit_of_measurement="mm")),
                vol.Optional(CONF_CHECK_INTERVAL, default=300): selector.NumberSelector(selector.NumberSelectorConfig(min=60, max=3600, unit_of_measurement="s")),
            })
            return self.async_show_form(step_id="user", data_schema=data_schema)
        return self.async_create_entry(title="Arrosage Automatique", data=user_input)
