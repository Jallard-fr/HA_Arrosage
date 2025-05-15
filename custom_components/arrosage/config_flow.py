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
