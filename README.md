# Cartographer 3D for RatOS 2.1

[Svenska](README.sv.md) · **New here? Follow the [step-by-step guide](GUIDE.md).**

Adds **Cartographer 3D** as a selectable Z probe in RatOS 2.1, next to Beacon. Beacon support is not
changed. Nothing in RatOS or Klipper is modified, so their updates keep working.

## What you get

- **"Cartographer 3D" in the RatOS configurator** as a Z probe choice.
- **Touch true zero in START_PRINT.** After bed heating, z-tilt and re-homing, the nozzle is set to
  150 °C (Cartographer default) and `CARTOGRAPHER_TOUCH_HOME` sets Z=0 by nozzle contact at
  `zero_reference_position`. Then a fast scan bed mesh is made, zero-referenced at the same point.
- **Adaptive priming works.** RatOS measures the bed at the prime blob location (it stopped with
  "No probe, beacon or bltouch section found" before). The blob height is configurable.
- **Live accelerometer** on the RatOS Analysis page for Cartographer V4 (see below).
- **Fix for "Communication timeout during homing"** on slow hosts (Raspberry Pi 3): Klipper's
  multi-MCU sync window is raised from 25 to 50 ms by a small Klipper extra, without editing Klipper.
- `CARTOGRAPHER_RATOS_STATUS` shows offsets, models and settings.

## Supported

| | |
|---|---|
| Printers | RatOS 2.1 printers |
| Probe | Cartographer 3D **V3 and V4** |
| Connection | **USB or CAN** (choose it when you install the Cartographer; for CAN set `canbus_uuid`, see the guide) |
| Plugin | cartographer3d-plugin 1.9 or newer |

Tested so far with a Cartographer V4 on USB (firmware 6.0.0, plugin 1.9.0, RatOS 2.1.3 on a
Raspberry Pi 3): homing, z-tilt, touch true zero, adaptive scan mesh, adaptive priming and a complete
print. V3 and CAN use the same plugin and are expected to work. Reports welcome.

## Requirements

- RatOS 2.1 with Klipper.
- Cartographer3D Klipper plugin (`cartographer3d-plugin` >= 1.9): <https://docs.cartographer3d.com>.
  On a new printer, install it after the RatOS Setup Wizard; the [step-by-step guide](GUIDE.md) shows
  the order.

## Install

On the printer (SSH):

```bash
git clone https://github.com/Slayerwen/ratos-cartographer ~/ratos-cartographer
bash ~/ratos-cartographer/install.sh
```

The installer:

1. generates `RatOS/z-probe/cartographer.cfg` from the RatOS macros installed on your printer,
2. installs a udev rule so the probe is always `/dev/cartographer`,
3. makes Klipper regenerate `cartographer.cfg` at every start, so **RatOS updates are picked up
   automatically**,
4. watches `RatOS.cfg` / `printer.cfg` and disables the `[probe]` section the configurator generates
   (see "Configurator note"),
5. adds an update manager entry, so updates show up in Mainsail/Fluidd.

Then:

1. In the RatOS configurator choose **Cartographer 3D** as Z probe and save (or add
   `[include RatOS/z-probe/cartographer.cfg]` to your generated RatOS config).
2. Set your values in `printer.cfg`:

```ini
[cartographer]
x_offset: -28.18      # your probe offsets
y_offset: -6.37

[bed_mesh]
zero_reference_position: 250,250   # required; also the touch homing position (bed center)
```

3. Restart Klipper and calibrate once: `CARTOGRAPHER_SCAN_CALIBRATE`, `CARTOGRAPHER_TOUCH_CALIBRATE`,
   `SAVE_CONFIG`.
4. Check with `CARTOGRAPHER_RATOS_STATUS`.

## Configurator note

The RatOS configurator adds a generic `[probe]` section (`pin: ^probe_pin`) for every probe except
Beacon and BLTouch. With Cartographer that section would stop Klipper from starting, because the
Cartographer registers itself as Klipper's probe. The installed watcher comments it out automatically
(lines prefixed `#ratos-cartographer#`, printer.cfg is backed up first). To fix it by hand, run
`python3 ~/ratos-cartographer/build.py`. Use `--dry-run` to only show what would change.

When the configurator asks about **printer.cfg**, choose **"Keep existing file"** if you already have a
working printer.cfg: accepting replaces your own values (offsets, rotation distance, PID, etc.).

## Settings

```ini
[gcode_macro RatOS]
variable_cartographer_touch_start_print_true_zero: True   # False = scan only, no touch in START_PRINT
variable_cartographer_touch_true_zero_temp: 150           # max 150 (plugin limit)
variable_prime_blob_z: 0.5                                # raise (e.g. 1.5) if the blob drowns the nozzle
```

## Live accelerometer (Cartographer V4)

The RatOS Analysis page only offers Host / Control Board / Toolboard / Beacon. If no ADXL is wired to
your controlboard, name the Cartographer's ADXL345 `controlboard` and it streams live under
Stream → Accelerometer → **Control Board**. Input shaper uses it too:

```ini
[adxl345 controlboard]
cs_pin: cartographer:PA0   # V4 (V3: PA3)
spi_bus: spi1

[resonance_tester]
accel_chip: adxl345 controlboard
```

## Live Z offset

Babystep in Mainsail during a print, then press **Save** (`Z_OFFSET_APPLY_PROBE`) and `SAVE_CONFIG`.
Because START_PRINT touch-homes, the touch model z_offset is updated. The plugin does not allow a
positive touch z_offset, so you can lower the nozzle at most by the current (negative) touch offset.

## How it works

`build.py` copies the RatOS macros that only know about `[probe]`, `[bltouch]` and `[beacon]`
(`SAVE_PROBE_RESULT`, `PROBE_FOR_PRIMING`, `PRIME_BLOB`, `_START_PRINT_BED_MESH`) from your RatOS
installation and patches them with exact text matches. If a RatOS update changes one of them so a
patch no longer fits, the build stops and keeps the previous `cartographer.cfg` instead of writing a
wrong one (see `journalctl -u klipper` or run `python3 ~/ratos-cartographer/build.py`).

## Not supported

Beacon-only RatOS features: adaptive heat soak, scan compensation, nozzle thermal expansion
compensation, contact bed mesh / z-tilt, and the configurator's Beacon firmware button.

## Uninstall

```bash
rm ~/ratos-configurator/configuration/z-probe/cartographer.cfg ~/klipper/klippy/extras/trsync_timeout.py
sudo systemctl disable --now ratos-cartographer.path
sudo rm /etc/udev/rules.d/99-cartographer.rules /etc/systemd/system/klipper.service.d/ratos-cartographer.conf \
  /etc/systemd/system/ratos-cartographer.path /etc/systemd/system/ratos-cartographer.service
sudo systemctl daemon-reload
```

Then choose another probe in the configurator and remove `[update_manager ratos-cartographer]` from
`moonraker.conf`.

## License

GPL-3.0, like Klipper and RatOS. Not affiliated with Rat Rig or Cartographer3D.
