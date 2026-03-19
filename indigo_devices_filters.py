"""
indigo_devices_filters.py

Usage: from indigo_devices_filters import DEVICE_FILTERS

Import into test files as needed and reference the filter list as a standard list. I.e.,

    device_type_filter = DEVICE_FILTERS[X]

These filters should allow for more human-friendly device type filtering in test files.
"""
DEVICE_FILTERS = [
    "com.somePlugin.devTypeId" 
    "com.somePlugin",     # all device types defined by some other plugin
    "indigo.controller",  # include devices that can send commands
    "indigo.dimmer",      # dimmer devices
    "indigo.insteon",     # include INSTEON devices - this is an interface filter that can be used with other filters
    "indigo.iodevice",    # input/output devices
    "indigo.relay",       # relay devices
    "indigo.responder",   # include devices whose state can be changed
    "indigo.sensor",      # all sensor type devices that have a virtual state in Indigo
    "indigo.sprinkler",   # sprinklers
    "indigo.thermostat",  # thermostats
    "indigo.x10",         # include X10 devices - this is an interface filter that can be used with other filters
    "indigo.zwave",       # include Z-Wave devices - this is an interface filter that can be used with other filters
    "self.devTypeId",     # all devices where deviceTypeId is one of the device types specified by the calling plugin
    "self",               # all device types defined by the calling plugin
]
