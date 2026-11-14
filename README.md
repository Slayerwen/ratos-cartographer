# Cartographer 3D for RatOS 2.1

[Svenska](README.sv.md)

Lets you choose **Cartographer 3D** as the Z probe in the RatOS Setup Wizard.

- Touch homing (exact Z=0) in RatOS's START_PRINT, after z-tilt and before the bed mesh
- Fast scan bed mesh, and adaptive priming that measures the bed
- Cartographer V4 accelerometer for input shaper and Realtime Analysis
- Does not modify RatOS or Klipper, so their updates keep working

**Supports:** Cartographer V3 and V4, USB or CAN, plugin 1.9 or newer.
**Tested** on a V4 over USB with RatOS 2.1.3. V3 and CAN should work too. Reports are welcome!

---

# Install guide

Follow the steps from top to bottom. Each step says **where**, **what to do**, and **how you know it
worked**. Do not skip ahead.

**You need:** a printer with RatOS 2.1, a Cartographer 3D, and a computer on the same network.

## Step 1 — Install RatOS

**Where:** RatOS website → <https://os.ratrig.com/docs/installation>

**Do:**

1. Flash RatOS to the SD card.
2. Connect the printer to Wi-Fi.
3. Update everything in Mainsail (**Machine → Update Manager → Update all**).

⚠️ **Stop when the Setup Wizard asks for your printer and hardware.** Do not finish the Setup Wizard yet.

✅ **Done when:** you can open Mainsail in your browser and everything in the Update Manager is up to date.

## Step 2 — Install this add-on

**Where:** a terminal on your computer.

1. Open a terminal:
   - **Windows:** press Start, type `PowerShell`, press Enter.
   - **Mac:** open **Terminal**.
2. Connect to the printer. Type this and press Enter:
   ```bash
   ssh pi@ratos.local
   ```
   - If it asks *"Are you sure you want to continue connecting?"*, type `yes` and press Enter.
   - Password: `raspberry`. Nothing shows while you type, that is normal.
   - If `ratos.local` does not work, use the printer's IP address instead, e.g. `ssh pi@192.168.1.50`.
3. Copy this line, paste it into the terminal and press Enter:
   ```bash
   git clone https://github.com/Slayerwen/ratos-cartographer ~/ratos-cartographer
   ```
4. Copy this line, paste it and press Enter:
   ```bash
   bash ~/ratos-cartographer/install.sh
   ```
   Type the password (`raspberry`) again if it asks.

✅ **Done when:** the last lines say `Done. Next steps`.
A line saying the Cartographer plugin is not installed yet is OK.

## Step 3 — Finish the RatOS Setup Wizard

**Where:** Mainsail → **Configurator** (in the left menu).

1. Continue the Setup Wizard where you stopped in step 1.
2. On the hardware page, set **Probe** to **Cartographer 3D**.
3. Fill in the rest of your hardware as usual and click **Confirm and save**.

✅ **Done when:** the configuration is saved.

ℹ️ Klipper will now show an error about Cartographer. **That is expected.** It goes away during step 4.

## Step 4 — Install and calibrate the Cartographer

**Where:** Cartographer website. Start here and follow their pages in order, up to and including
**Touch Calibration**:
<https://docs.cartographer3d.com/cartographer-probe/installation-and-setup/probe-installation/>

Follow their guide as written. Put their config sections in `printer.cfg`, **below**
`[include RatOS.cfg]` and **above** the `#*# SAVE_CONFIG` line.

⚠️ **Do not add `[safe_z_home]` or `[homing_override]`** from their guide. RatOS has its own homing,
and Klipper won't start with them. Step 5 has the full list of what to leave out.

✅ **Done when:** you finished their **Touch Calibration** page and ran `SAVE_CONFIG`, and typing
`CARTOGRAPHER_RATOS_STATUS` in the Mainsail console shows your offsets plus a **scan model** and
**touch model** that are not `none`.

## Step 5 — Check printer.cfg

**Where:** Mainsail → **Machine** (left menu) → click `printer.cfg`.

### ❌ Remove these if they are in printer.cfg

| From Cartographer's guide | Why |
|---|---|
| `[safe_z_home]` | RatOS has its own homing. |
| `[homing_override]` | RatOS has its own homing. |
| **CAN only:** the `serial:` and `restart_method:` lines under `[mcu cartographer]` | Klipper won't start with them when `canbus_uuid` is used. |

Also do **not** put `CARTOGRAPHER_TOUCH_HOME` in your slicer's start G-code. RatOS's START_PRINT
already does it.

### ✔️ Check this value

In `[bed_mesh]`, `zero_reference_position` must be the **middle of your bed**, for example
`250, 250` for a 500 bed or `150, 150` for a 300 bed. The nozzle touches the bed there before every
print.

### ➕ Paste these

Paste in printer.cfg

1. **Prime blob height.** Raises the nozzle while priming, so it doesn't get buried in plastic:
   ```ini
   [gcode_macro RatOS]
   variable_prime_blob_z: 1.5
   ```
2. **Accelerometer.** Cartographer's guide added it as `[adxl345]`. RatOS Realtime Analysis can only
   show it under the name "Control Board", so **rename** these two lines from step 4:
   ```ini
   [adxl345 controlboard]       # was: [adxl345]
   cs_pin: cartographer:PA0     # V4. For V3: cartographer:PA3
   spi_bus: spi1

   [resonance_tester]
   accel_chip: adxl345 controlboard   # was: adxl345
   ```
   ⚠️ Skip this if you have another accelerometer plugged into your control board.
3. Click **Save & Restart**.

✅ **Done when:** Mainsail shows no error, the printer is **Ready**, and in the Configurator → **Realtime Analysis** →
**Stream → Accelerometer → Control Board** shows a live graph.

## Step 6 — Print

1. Slice with your normal RatOS slicer profile: <https://os.ratrig.com/docs/slicers>
   Do **not** add `CARTOGRAPHER_TOUCH_HOME` to the start G-code, because RatOS does it for you.
2. Start a small print and watch the first layer.
3. If the first layer is too high or too low, change the **Z offset** in Mainsail while printing.
   After the print, click **Save** next to the Z offset and run `SAVE_CONFIG`.

✅ **Done!** 🎉

## Already have RatOS set up and printing?

1. Do **step 2**.
2. In the Configurator, set **Probe** to **Cartographer 3D** and click **Confirm and save**.
   For `printer.cfg`, click **Review changes** → **Keep existing file**.
3. If the Cartographer is not installed and calibrated yet, do **step 4**.
4. In `printer.cfg`, delete what you added yourself to make Cartographer work with RatOS:
   `[safe_z_home]`, `[homing_override]`, `[probe]`, and your own `PROBE_FOR_PRIMING`, `PRIME_BLOB`
   or `_USER_START_PRINT_BED_MESH` macros. Also remove `CARTOGRAPHER_TOUCH_HOME` from your slicer's
   start G-code. Keep the Cartographer sections from their guide and everything below `SAVE_CONFIG`.
5. Click **Save & Restart**, run `CARTOGRAPHER_RATOS_STATUS` in the console, then do **step 5** and **step 6**.

## Problems?

| Problem | What to do |
|---|---|
| Cartographer 3D is not in the Probe list | Do step 2, then reload the Configurator page. |
| Klipper error right after step 3 | Normal, continue with step 4. |
| Klipper still won't start after step 4 | Check that `[safe_z_home]` / `[homing_override]` are not in printer.cfg, and with CAN that `serial` / `restart_method` are removed. Then in the terminal run `python3 ~/ratos-cartographer/build.py` and click **Restart** in Mainsail. |
| `Nozzle temperature must be below 150C` | Let the nozzle cool down, or add `variable_cartographer_touch_true_zero_temp: 145` under `[gcode_macro RatOS]` in printer.cfg. |
| `Communication timeout during homing` | See below. |
| Something else | Open an issue on GitHub with the error, the output of `CARTOGRAPHER_RATOS_STATUS` and your `klippy.log`. |

### Communication timeout during homing

1. **Check the power first.** In the terminal, run `vcgencmd get_throttled`. It must say
   `throttled=0x0`. Anything else means the Raspberry Pi gets too little power. Use a proper power
   supply and a short cable.
2. **If the error still happens**, add this to printer.cfg:
   ```ini
   [trsync_timeout]
   timeout: 0.05
   ```

---

# Technical details

## Settings

Under `[gcode_macro RatOS]` in printer.cfg:

| Setting | Default | What it does |
|---|---|---|
| `variable_cartographer_touch_start_print_true_zero` | `True` | Touch homing during START_PRINT. `False` = scan only |
| `variable_cartographer_touch_true_zero_temp` | `150` | Nozzle temperature for touch (max 150, plugin limit) |
| `variable_prime_blob_z` | `0.5` | Prime blob height above the measured bed |

## What the installer does

1. Generates `RatOS/z-probe/cartographer.cfg` from the RatOS macros installed on your printer.
2. Installs a udev rule so a USB Cartographer is always `/dev/cartographer`.
3. Rebuilds `cartographer.cfg` every time Klipper starts, so RatOS updates are picked up automatically.
4. Watches `RatOS.cfg` / `printer.cfg` and comments out the `[probe]` section the Setup Wizard adds
   for Cartographer (lines start with `#ratos-cartographer#`, printer.cfg is backed up first). The
   Setup Wizard adds it for every probe except Beacon and BLTouch, and it would stop Klipper from starting.
5. Adds `ratos-cartographer` to Mainsail's Update Manager.
6. Installs the optional `[trsync_timeout]` Klipper extra (does nothing unless you add the section).

With CAN (`canbus_uuid` in printer.cfg), the USB `serial` and `restart_method` lines are left out
automatically.

## How it works

`build.py` copies the RatOS macros that only know about `[probe]`, `[bltouch]` and `[beacon]`
(`SAVE_PROBE_RESULT`, `PROBE_FOR_PRIMING`, `PRIME_BLOB`, `_START_PRINT_BED_MESH`) from your RatOS
installation and patches them with exact text matches. If a RatOS update changes one of them so a
patch no longer fits, the build stops and keeps the previous `cartographer.cfg` instead of writing a
wrong one (see `journalctl -u klipper`, or run `python3 ~/ratos-cartographer/build.py`).

Live Z offset: because START_PRINT touch-homes, **Save** in Mainsail (`Z_OFFSET_APPLY_PROBE`) updates
the touch model. The plugin does not allow a positive touch z_offset, so you can lower the nozzle at
most by the current (negative) touch offset.

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

Then choose another probe in the Setup Wizard and remove `[update_manager ratos-cartographer]` from
`moonraker.conf`.

## License

GPL-3.0, like Klipper and RatOS. Not affiliated with Rat Rig or Cartographer3D.
