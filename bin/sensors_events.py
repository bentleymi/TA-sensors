#!/usr/bin/env python3
"""Emit one JSON event per cycle with all hwmon sensor readings."""
import sys

from sensors_common import (FAMILIES, discover_sensors, emit, fail)


def main():
    sensors = discover_sensors()
    if not sensors:
        return fail("no hwmon sensors found under /sys/class/hwmon")
    chips = {}
    for chip_name, key, label, family, value, status in sensors:
        chips.setdefault(chip_name, {})[key] = {
            "sensor_name": label,
            "reading": str(value),
            "reading_value": value,
            "units": FAMILIES[family][0],
            "status": status,
        }
    emit({"chips": chips})
    return 0


if __name__ == "__main__":
    sys.exit(main())
