# Install guide: Cartographer 3D on RatOS 2.1

Follow the steps from top to bottom. Each step says **what to do**, **where**, and **how you know it worked**.
Do not skip ahead.

**You need:** a printer with RatOS 2.1, a Cartographer 3D (V3 or V4, USB or CAN), and a computer on the
same network.

---

## Step 1 — Install RatOS

**Where:** RatOS website → <https://os.ratrig.com/docs/installation>

**Do:**

1. Flash RatOS to the SD card.
2. Connect the printer to Wi-Fi.
3. Update everything in Mainsail (**Machine → Update Manager → Update all**).

⚠️ **Stop when the Setup Wizard asks for your printer and hardware.** Do not finish the Setup Wizard yet.

✅ **Done when:** you can open Mainsail in your browser and everything in the Update Manager is up to date.

---

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

---

## Step 3 — Finish the RatOS Setup Wizard

**Where:** Mainsail → **Configurator** (in the left menu).

1. Continue the Setup Wizard where you stopped in step 1.
2. On the hardware page, set **Probe** to **Cartographer 3D**.
3. Fill in the rest of your hardware as usual and click **Confirm and save**.

✅ **Done when:** the configuration is saved.

ℹ️ Klipper will now show an error about Cartographer. **That is expected.** It goes away after step 5.

---

## Step 4 — Install the Cartographer

**Where:** Cartographer website.

1. Mount and connect the probe:
   <https://docs.cartographer3d.com/cartographer-probe/installation-and-setup/probe-installation/>
2. Open the Klipper setup page:
   <https://docs.cartographer3d.com/cartographer-probe/installation-and-setup/software-configuration/klipper-setup/>

   On that page, **only do these parts**:

   | Part on Cartographer's page | Do it? |
   |---|---|
   | Install the Klipper plugin | ✅ Yes |
   | Download the firmware | ✅ Yes |
   | Add the update sections to `moonraker.conf` | ✅ Yes |
   | Find your serial path / CAN UUID | ✅ Yes, write it down |
   | Update the probe firmware | ✅ Yes |
   | `[safe_z_home]` and `[homing_override]` | ❌ **No!** They break RatOS homing |
   | All other config sections for `printer.cfg` | ❌ No, step 5 does it |
   | Calibration | ⏭ Later, in step 6 |

✅ **Done when:** the plugin and firmware are installed.

---

## Step 5 — Add your settings to printer.cfg

**Where:** Mainsail → **Machine** (left menu) → click `printer.cfg`.

1. Scroll down to the bottom, **just above** the line that starts with `#*# <---------------------- SAVE_CONFIG`.
   If there is no such line, go to the very end.
2. Paste this, and change the numbers to yours:
   ```ini
   [cartographer]
   x_offset: 0      # your probe X offset (from Cartographer's docs / your toolhead mount)
   y_offset: 20     # your probe Y offset

   [bed_mesh]
   zero_reference_position: 250, 250   # the middle of your bed: 150,150 (300 bed), 200,200 (400 bed), 250,250 (500 bed)
   ```
3. **Only if you use CAN**, also paste this with your UUID from step 4:
   ```ini
   [mcu cartographer]
   canbus_uuid: 0123456789ab
   ```
4. Click **Save & Restart** (top right).

✅ **Done when:** Mainsail shows no error and the printer status is **Ready**.

---

## Step 6 — Calibrate the Cartographer

**Where:** Mainsail → **Dashboard** → **Console** (type commands at the bottom and press Enter).

Make sure the nozzle is clean and **not hotter than 150 °C**.

1. Type `G28` and press Enter. The printer homes.
2. Type `CARTOGRAPHER_SCAN_CALIBRATE` and press Enter.
   A window opens: lower the nozzle until a sheet of paper just drags, then click **Accept**.
   [More help](https://docs.cartographer3d.com/cartographer-probe/installation-and-setup/software-configuration/scan-calibration/)
3. Type `CARTOGRAPHER_TOUCH_CALIBRATE` and press Enter. The nozzle gently touches the bed a few times.
   [More help](https://docs.cartographer3d.com/cartographer-probe/installation-and-setup/software-configuration/touch-calibration/)
4. Type `SAVE_CONFIG` and press Enter. Klipper restarts.
5. Type `CARTOGRAPHER_RATOS_STATUS` and press Enter.

✅ **Done when:** the status shows your offsets, and a **scan model** and **touch model** that are not `none`.

---

## Step 7 — Print

1. Slice with your normal RatOS slicer profile: <https://os.ratrig.com/docs/slicers>
   Do **not** add `CARTOGRAPHER_TOUCH_HOME` to the start G-code, because RatOS does it for you.
2. Start a small print and watch the first layer.
3. If the first layer is too high or too low, change the **Z offset** in Mainsail while printing.
   After the print, click **Save** next to the Z offset and run `SAVE_CONFIG`.

✅ **Done!** 🎉

---

## Optional extras

**The prime blob buries the nozzle in plastic.** Add this to printer.cfg to raise it:

```ini
[gcode_macro RatOS]
variable_prime_blob_z: 1.5
```

**Use the Cartographer V4's accelerometer** for input shaper and Realtime Analysis
(only if no other accelerometer is plugged into your control board):

```ini
[adxl345 controlboard]
cs_pin: cartographer:PA0   # V4. For V3 use: cartographer:PA3
spi_bus: spi1

[resonance_tester]
accel_chip: adxl345 controlboard
probe_points:
    250, 250, 20           # middle of your bed
```

In Realtime Analysis, choose **Stream → Accelerometer → Control Board**.

---

## Already have RatOS set up and printing?

1. Do **step 2**.
2. In the Configurator, set **Probe** to **Cartographer 3D** and click **Confirm and save**.
   For `printer.cfg`, click **Review changes** → **Keep existing file**.
3. If the Cartographer is not installed yet, do **step 4**.
4. In `printer.cfg`, delete anything you added before to make Cartographer work:
   `[safe_z_home]`, `[homing_override]`, `[probe]`, `[temperature_sensor cartographer]`,
   and your own `PROBE_FOR_PRIMING`, `PRIME_BLOB` or `_USER_START_PRINT_BED_MESH` macros.
   Keep `[cartographer]`, `[bed_mesh]` and everything below `SAVE_CONFIG`.
5. Do **step 5** for anything that is missing, then **step 6** if you are not calibrated yet.

---

## Problems?

| Problem | What to do |
|---|---|
| Cartographer 3D is not in the Probe list | Do step 2, then reload the Configurator page. |
| Klipper error right after step 3 | Normal, continue with steps 4 and 5. |
| Klipper still won't start after step 5 | In the terminal, run `python3 ~/ratos-cartographer/build.py`, then click **Restart** in Mainsail. |
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
