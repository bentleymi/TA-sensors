#!/usr/bin/env python3
"""Emit flat numeric metrics (one JSON event per cycle) for analytics."""
import sys

from sensors_common import discover_sensors, emit, fail


def main():
    sensors = discover_sensors()
    if not sensors:
        return fail("no hwmon sensors found under /sys/class/hwmon")
    payload = {}
    for chip_name, key, label, family, value, status in sensors:
        metric = "%s_%s" % (chip_name, key)
        payload[metric] = value
        payload[metric + "_status"] = status
    emit(payload)
    return 0


if __name__ == "__main__":
    sys.exit(main())
