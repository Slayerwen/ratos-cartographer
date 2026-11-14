#!/usr/bin/env python3
"""Generate RatOS/z-probe/cartographer.cfg.

Copies the RatOS macros that only know about [probe], [bltouch] and [beacon]
from the RatOS installation on this printer, and patches them so they also
handle [cartographer]. Every patch must apply exactly as expected; if RatOS
changed the macro, the build stops instead of producing a wrong config.

It also disables the "[probe]" section that the RatOS configurator generates for
every probe except Beacon and BLTouch (it would clash with Cartographer, which
registers itself as Klipper's probe). Only RatOS.cfg / printer.cfg are touched,
only when RatOS.cfg includes cartographer.cfg, and only the exact generated block.

Usage: python3 build.py [--ratos-config DIR] [--config-dir DIR] [--out FILE] [--quiet] [--dry-run]
"""
import argparse
import os
import re
import shutil
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_RATOS = os.path.expanduser("~/ratos-configurator/configuration")
DEFAULT_CONFIG_DIR = os.path.expanduser("~/printer_data/config")
CARTO_INCLUDE = "[include RatOS/z-probe/cartographer.cfg]"
SAVE_CONFIG_MARKER = "#*# <---------------------- SAVE_CONFIG"
DISABLED_MARK = "#ratos-cartographer# "


class PatchError(Exception):
    pass


def disable_generated_probe(text):
    """Comment out the configurator-generated '# Probe configuration' + '[probe]' block.

    Only matches a [probe] header directly preceded by '# Probe configuration' and
    containing a 'pin:' line, up to the next blank line or section. The SAVE_CONFIG
    block is never touched. Returns (new_text, changed).
    """
    body, sep, tail = text.partition(SAVE_CONFIG_MARKER)
    lines = body.split("\n")
    out = []
    changed = False
    i = 0
    while i < len(lines):
        if lines[i].strip() == "[probe]" and out and out[-1].strip() == "# Probe configuration":
            j = i + 1
            while j < len(lines) and lines[j].strip() != "" and not lines[j].lstrip().startswith("["):
                j += 1
            block = lines[i:j]
            if any(line.lstrip().startswith("pin:") for line in block):
                out[-1] = DISABLED_MARK + out[-1] + "  (disabled: Cartographer is the probe)"
                out.extend(DISABLED_MARK + line for line in block)
                changed = True
                i = j
                continue
        out.append(lines[i])
        i += 1
    return "\n".join(out) + sep + tail, changed


def sanitize_generated_configs(config_dir, dry_run=False, quiet=False):
    ratos_cfg = os.path.join(config_dir, "RatOS.cfg")
    printer_cfg = os.path.join(config_dir, "printer.cfg")
    try:
        with open(ratos_cfg, encoding="utf-8") as f:
            if CARTO_INCLUDE not in f.read():
                return
    except OSError:
        return
    targets = [ratos_cfg]
    try:
        with open(printer_cfg, encoding="utf-8") as f:
            if re.search(r"^\[include RatOS\.cfg\]", f.read(), re.M):
                targets.append(printer_cfg)
    except OSError:
        pass
    for path in targets:
        with open(path, encoding="utf-8") as f:
            text = f.read()
        new, changed = disable_generated_probe(text)
        if not changed:
            continue
        if dry_run:
            print("--- would change %s:" % path)
            for line in new.split("\n"):
                if line.startswith(DISABLED_MARK):
                    print(line)
            continue
        if path == printer_cfg:
            shutil.copy2(path, path + ".pre-ratos-cartographer-" + time.strftime("%Y%m%d_%H%M%S"))
        with open(path, "w", encoding="utf-8", newline="\n") as f:
            f.write(new)
        print("ratos-cartographer: disabled configurator-generated [probe] in %s" % path)


def extract_section(text, name, source):
    """Return the full text of [name] up to the next section header."""
    m = re.search(r"^\[" + re.escape(name) + r"\]\n", text, re.M)
    if not m:
        raise PatchError("section [%s] not found in %s" % (name, source))
    rest = text[m.end():]
    n = re.search(r"^\[", rest, re.M)
    body = rest[: n.start()] if n else rest
    return m.group(0) + body.rstrip() + "\n"


def replace_exact(section, old, new, count, label):
    found = section.count(old)
    if found != count:
        raise PatchError("%s: expected %d match(es), found %d for:\n%s" % (label, count, found, old))
    return section.replace(old, new)


def uses_can(config_dir):
    """True if printer.cfg has an active canbus_uuid in [mcu cartographer]."""
    try:
        with open(os.path.join(config_dir, "printer.cfg"), encoding="utf-8") as f:
            body = f.read().partition(SAVE_CONFIG_MARKER)[0]
    except OSError:
        return False
    m = re.search(r"^\[mcu cartographer\][^\n]*\n(.*?)(?=^\[|\Z)", body, re.M | re.S)
    return bool(m and re.search(r"^canbus_uuid\s*:", m.group(1), re.M))


def build(ratos_dir, can=False):
    def read(rel):
        path = os.path.join(ratos_dir, rel)
        with open(path, encoding="utf-8") as f:
            return f.read(), path

    priming, priming_path = read("macros/priming.cfg")
    mesh, mesh_path = read("macros/mesh.cfg")
    out = []

    # 1. SAVE_PROBE_RESULT: Cartographer's printer.probe.last_z_result is the toolhead Z where
    #    the scan was taken (~2mm); the estimated bed contact height is last_probe_position[2].
    s = extract_section(priming, "gcode_macro SAVE_PROBE_RESULT", priming_path)
    s = replace_exact(
        s,
        "\t{% elif printer.fastconfig.settings.bltouch is defined  %}\n",
        "\t{% elif printer.fastconfig.settings.cartographer is defined %}\n"
        "\t\t{% set last_z_offset = printer.probe.last_probe_position[2]|float %}\n"
        "\t{% elif printer.fastconfig.settings.bltouch is defined  %}\n",
        1, "SAVE_PROBE_RESULT")
    out.append(s)

    # 2. PROBE_FOR_PRIMING: get probe offsets from [cartographer].
    s = extract_section(priming, "gcode_macro PROBE_FOR_PRIMING", priming_path)
    s = replace_exact(
        s,
        "\t\t{% elif printer.fastconfig.settings.beacon is defined %}\n"
        "\t\t\t{% set x_offset = printer.fastconfig.settings.beacon.x_offset|float %}\n",
        "\t\t{% elif printer.fastconfig.settings.cartographer is defined %}\n"
        "\t\t\t{% set x_offset = printer.fastconfig.settings.cartographer.x_offset|float %}\n"
        "\t\t\t{% set y_offset = printer.fastconfig.settings.cartographer.y_offset|float %}\n"
        "\t\t\t{% set z_offset = 0 %}\n"
        "\t\t{% elif printer.fastconfig.settings.beacon is defined %}\n"
        "\t\t\t{% set x_offset = printer.fastconfig.settings.beacon.x_offset|float %}\n",
        1, "PROBE_FOR_PRIMING")
    out.append(s)

    # 3. PRIME_BLOB: accept [cartographer] as a valid probe for adaptive priming.
    s = extract_section(priming, "gcode_macro PRIME_BLOB", priming_path)
    s = replace_exact(
        s,
        "and printer.fastconfig.settings.beacon is not defined %}",
        "and printer.fastconfig.settings.beacon is not defined and printer.fastconfig.settings.cartographer is not defined %}",
        2, "PRIME_BLOB")
    # ...and make the blob extrusion height configurable (variable_prime_blob_z, RatOS default 0.5).
    s = replace_exact(
        s,
        "\tG1 Z{0.5 + start_z_offset} F{z_speed}\n",
        "\tG1 Z{printer[\"gcode_macro RatOS\"].prime_blob_z|default(0.5)|float + start_z_offset} F{z_speed}\n",
        1, "PRIME_BLOB height")
    out.append(s)

    # 4. _START_PRINT_BED_MESH: touch true zero right before meshing
    #    (after bed heating, z-tilt and re-homing).
    s = extract_section(mesh, "gcode_macro _START_PRINT_BED_MESH", mesh_path)
    s = replace_exact(
        s,
        "\tSET_MACRO_TRAVEL_SETTINGS\n",
        "\tSET_MACRO_TRAVEL_SETTINGS\n\n"
        "\t# Cartographer touch true zero (before meshing, so the mesh is relative to true zero)\n"
        "\t_CARTOGRAPHER_START_PRINT_TRUE_ZERO\n",
        1, "_START_PRINT_BED_MESH")
    out.append(s)

    with open(os.path.join(HERE, "cartographer.base.cfg"), encoding="utf-8") as f:
        base = f.read()
    if can:
        # Klipper does not read 'serial'/'restart_method' for CAN MCUs and would reject them as
        # unused options, so leave them out when printer.cfg sets canbus_uuid.
        base = replace_exact(
            base,
            "serial: /dev/cartographer\nrestart_method: command\n",
            "# CAN: canbus_uuid is set in printer.cfg (USB serial/restart_method left out)\n",
            1, "CAN mcu")
    return base + "\n" + "\n".join(out)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ratos-config", default=DEFAULT_RATOS)
    ap.add_argument("--out", default=None)
    ap.add_argument("--quiet", action="store_true", help="only print errors (used at Klipper start)")
    ap.add_argument("--config-dir", default=DEFAULT_CONFIG_DIR, help="printer config dir (RatOS.cfg, printer.cfg)")
    ap.add_argument("--dry-run", action="store_true", help="only show what would change in RatOS.cfg/printer.cfg")
    args = ap.parse_args()

    sanitize_generated_configs(args.config_dir, dry_run=args.dry_run, quiet=args.quiet)
    if args.dry_run:
        return 0

    out_path = args.out or os.path.join(args.ratos_config, "z-probe", "cartographer.cfg")
    try:
        cfg = build(args.ratos_config, can=uses_can(args.config_dir))
    except (PatchError, OSError) as e:
        print("ratos-cartographer: BUILD FAILED, existing cartographer.cfg kept: %s" % e, file=sys.stderr)
        return 1
    try:
        with open(out_path, encoding="utf-8") as f:
            if f.read() == cfg:
                if not args.quiet:
                    print("%s is up to date" % out_path)
                return 0
    except OSError:
        pass
    with open(out_path, "w", encoding="utf-8", newline="\n") as f:
        f.write(cfg)
    print("ratos-cartographer: wrote %s (%d lines)" % (out_path, cfg.count("\n")))
    return 0


if __name__ == "__main__":
    sys.exit(main())
