"""Shared collection logic for TA-sensors scripted inputs."""
import json
import os
import re
import sys

SYSFS_ROOT = os.environ.get("HWMON_ROOT", "/sys/class/hwmon")

# hwmon family -> (unit, scale)  scale divides the raw *_input value
FAMILIES = {
    "temp": ("celsius", 1000.0),
    "in": ("volts", 1000.0),
    "power": ("watts", 1000.0),
    "current": ("amps", 1000.0),
    "humidity": ("percent_rh", 1000.0),
    "fan": ("rpm", 1.0),
}

KEY_RE = re.compile(r"[^a-z0-9]+")


def sanitize(text):
    return KEY_RE.sub("_", text.lower()).strip("_")


def read_file(path):
    try:
        with open(path) as fh:
            return fh.read().strip()
    except OSError:
        return None


def discover_sensors():
    """Return list of (chip_name, key, label, family, value, status)."""
    results = []
    seen_chip_names = set()
    if not os.path.isdir(SYSFS_ROOT):
        return results
    for hwmon in sorted(os.listdir(SYSFS_ROOT)):
        chip_dir = os.path.join(SYSFS_ROOT, hwmon)
        chip_name = sanitize(read_file(os.path.join(chip_dir, "name")) or hwmon) or hwmon.lower()
        if chip_name in seen_chip_names:
            chip_name = "%s_%s" % (chip_name, hwmon.replace("hwmon", ""))
        seen_chip_names.add(chip_name)
        seen_keys = set()
        for entry in sorted(os.listdir(chip_dir)):
            if not entry.endswith("_input"):
                continue
            stem = entry[: -len("_input")]
            family = None
            for candidate in FAMILIES:
                if stem == candidate or stem.startswith(candidate):
                    family = candidate
                    break
            if family is None:
                continue
            raw = read_file(os.path.join(chip_dir, stem + "_input"))
            if raw is None:
                continue
            try:
                value = float(raw) / FAMILIES[family][1]
            except ValueError:
                continue
            label = read_file(os.path.join(chip_dir, stem + "_label")) or stem
            status = "ok"
            if (read_file(os.path.join(chip_dir, stem + "_alarm")) or "0") == "1":
                status = "alarm"
            key = sanitize(label) or sanitize(stem)
            if key in seen_keys:
                key = "%s_%s" % (sanitize(stem), sanitize(label))
            seen_keys.add(key)
            results.append((chip_name, key, label, family, round(value, 3), status))
    return results


def emit(payload):
    sys.stdout.write(json.dumps(payload, sort_keys=True) + "\n")
    sys.stdout.flush()


def fail(message):
    sys.stderr.write("TA-sensors collection error: %s\n" % message)
    return 1
