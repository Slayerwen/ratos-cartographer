# Guide: Cartographer 3D on RatOS 2.1

Do these steps in order. For the RatOS and Cartographer parts, follow their own guides and come back
here.

## 1. Install RatOS

Follow the RatOS guide: <https://os.ratrig.com/docs/installation>

Flash the image, connect Wi-Fi and update the software. **Stop before the Setup Wizard's hardware
steps** and come back here.

## 2. Install this package

SSH into the printer (`ssh pi@ratos.local`, default password `raspberry`) and run:

```bash
git clone https://github.com/Slayerwen/ratos-cartographer ~/ratos-cartographer
```

```bash
bash ~/ratos-cartographer/install.sh
```

A note that the Cartographer plugin is not installed yet is normal.

## 3. Run the RatOS Setup Wizard

Continue the Setup Wizard as the RatOS guide describes, and choose **Probe → Cartographer 3D**.

- If you already have a working `printer.cfg`, choose **Keep existing file** for it.
- After saving, Klipper shows an error about Cartographer until step 4 is done. That is normal.

## 4. Install the Cartographer

Follow the Cartographer guides:

- Hardware: <https://docs.cartographer3d.com/cartographer-probe/installation-and-setup/probe-installation/>
- Klipper setup: <https://docs.cartographer3d.com/cartographer-probe/installation-and-setup/software-configuration/klipper-setup/>

Use USB or CAN, whichever you prefer. In the Klipper setup:

- **Do** install the plugin and the firmware, add the Moonraker update sections, and find your serial
  path or CAN UUID.
- **Do not** add `[safe_z_home]` or `[homing_override]`. They break RatOS homing.
- **Skip** the rest of the config sections. RatOS and this package already have them, except for the
  few values in step 5.

## 5. Add your values to printer.cfg

```ini
[cartographer]
x_offset: -28.18                    # your probe offsets
y_offset: -6.37

[bed_mesh]
zero_reference_position: 250, 250   # centre of your bed
```

**CAN only:** also add your UUID:

```ini
[mcu cartographer]
canbus_uuid: 0123456789ab
```

Save & Restart.

## 6. Calibrate

Follow Cartographer's [scan calibration](https://docs.cartographer3d.com/cartographer-probe/installation-and-setup/software-configuration/scan-calibration/)
and [touch calibration](https://docs.cartographer3d.com/cartographer-probe/installation-and-setup/software-configuration/touch-calibration/),
then run `SAVE_CONFIG`.

Check with `CARTOGRAPHER_RATOS_STATUS`. Then you are ready to print with your normal RatOS slicer
profile. **Do not** add `CARTOGRAPHER_TOUCH_HOME` to your slicer start G-code, because RatOS's
START_PRINT does it now.

---

## Optional

**Prime blob buries the nozzle?** Raise it in printer.cfg:

```ini
[gcode_macro RatOS]
variable_prime_blob_z: 1.5   # default 0.5
```

**Use the Cartographer's accelerometer** (RatOS Realtime Analysis → Control Board, and input shaper).
Only do this if no other accelerometer is wired to your control board:

```ini
[adxl345 controlboard]
cs_pin: cartographer:PA0   # V4. V3: cartographer:PA3
spi_bus: spi1

[resonance_tester]
accel_chip: adxl345 controlboard
probe_points:
    250, 250, 20
```

More settings and how the package works: see the [README](README.md).

## Problems?

| Problem | Fix |
|---|---|
| Cartographer 3D not in the Setup Wizard | Do step 2, then reload the Configurator page. |
| Klipper won't start after the Setup Wizard saved | Run `python3 ~/ratos-cartographer/build.py`, then restart Klipper. |
| `Communication timeout during homing` | Run `bash ~/ratos-cartographer/install.sh` again. |
| `Nozzle temperature must be below 150C` | Add `variable_cartographer_touch_true_zero_temp: 145` under `[gcode_macro RatOS]`. |
| Something else | Open an issue on GitHub with the error, the output of `CARTOGRAPHER_RATOS_STATUS` and your `klippy.log`. |
