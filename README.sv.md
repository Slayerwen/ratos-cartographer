# Cartographer 3D för RatOS 2.1

[English](README.md) · **Ny? Följ [steg-för-steg-guiden](GUIDE.md) (på engelska).**

Lägger till **Cartographer 3D** som valbar Z-probe i RatOS 2.1, bredvid Beacon. Beacon-stödet ändras
inte. Ingenting i RatOS eller Klipper ändras, så deras uppdateringar fungerar som vanligt.

## Det här får du

- **"Cartographer 3D" i RatOS-configuratorn** som val av Z-probe.
- **Touch true zero i START_PRINT.** Efter att bädden värmts, Z-tilt och omhoming värms munstycket
  till 150 °C (Cartographers standard), och `CARTOGRAPHER_TOUCH_HOME` sätter Z=0 genom att nudda
  bädden vid `zero_reference_position`. Sedan görs en snabb scan-mesh som nollas i samma punkt.
- **Adaptiv priming fungerar.** RatOS mäter bädden där blobben läggs (tidigare stoppade det med
  "No probe, beacon or bltouch section found"). Blob-höjden går att ställa in.
- **Live-accelerometer** på RatOS Analysis-sida för Cartographer V4 (se nedan).
- **Lösning på "Communication timeout during homing"** på långsamma datorer (Raspberry Pi 3):
  Klippers synkfönster mellan korten höjs från 25 till 50 ms med en liten tilläggsmodul, utan att
  Klipper ändras.
- `CARTOGRAPHER_RATOS_STATUS` visar offsets, modeller och inställningar.

## Stöds

| | |
|---|---|
| Skrivare | Skrivare med RatOS 2.1 |
| Probe | Cartographer 3D **V3 och V4** |
| Anslutning | **USB eller CAN** (väljs när du installerar Cartographer; för CAN sätter du `canbus_uuid`, se guiden) |
| Plugin | cartographer3d-plugin 1.9 eller nyare |

Hittills testat med Cartographer V4 via USB (firmware 6.0.0, plugin 1.9.0, RatOS 2.1.3 på en
Raspberry Pi 3): homing, Z-tilt, touch true zero, adaptiv scan-mesh, adaptiv priming och en hel
utskrift. V3 och CAN använder samma plugin och bör fungera. Rapportera gärna hur det går.

## Krav

- RatOS 2.1 med Klipper.
- Cartographer3D Klipper-plugin (`cartographer3d-plugin` >= 1.9): <https://docs.cartographer3d.com>.
  På en ny skrivare installeras det efter RatOS Setup Wizard; [guiden](GUIDE.md) visar ordningen.

## Installation

På skrivaren (via SSH):

```bash
git clone https://github.com/Slayerwen/ratos-cartographer ~/ratos-cartographer
bash ~/ratos-cartographer/install.sh
```

Installationsskriptet:

1. skapar `RatOS/z-probe/cartographer.cfg` utifrån RatOS-makrona på din skrivare,
2. installerar en udev-regel så att proben alltid heter `/dev/cartographer`,
3. låter Klipper bygga om `cartographer.cfg` vid varje start, så att **RatOS-uppdateringar tas med
   automatiskt**,
4. bevakar `RatOS.cfg` / `printer.cfg` och stänger av den `[probe]`-sektion som configuratorn
   genererar (se "Om configuratorn"),
5. lägger till paketet i update manager, så att uppdateringar syns i Mainsail/Fluidd.

Sedan:

1. Välj **Cartographer 3D** som Z-probe i RatOS-configuratorn och spara (eller lägg till
   `[include RatOS/z-probe/cartographer.cfg]` i din genererade RatOS-config).
2. Sätt dina värden i `printer.cfg`:

```ini
[cartographer]
x_offset: -28.18      # dina probe-offsets
y_offset: -6.37

[bed_mesh]
zero_reference_position: 250,250   # krävs; är också platsen för touch (bäddens mitt)
```

3. Starta om Klipper och kalibrera en gång: `CARTOGRAPHER_SCAN_CALIBRATE`,
   `CARTOGRAPHER_TOUCH_CALIBRATE`, `SAVE_CONFIG`.
4. Kontrollera med `CARTOGRAPHER_RATOS_STATUS`.

## Om configuratorn

RatOS-configuratorn lägger till en vanlig `[probe]`-sektion (`pin: ^probe_pin`) för alla probar utom
Beacon och BLTouch. Med Cartographer gör den sektionen att Klipper inte startar, eftersom Cartographer
själv registrerar sig som Klippers probe. Bevakningen som installeras kommenterar bort den automatiskt
(rader som börjar med `#ratos-cartographer#`, och printer.cfg säkerhetskopieras först). För att rätta
för hand kör du `python3 ~/ratos-cartographer/build.py`. Med `--dry-run` visas bara vad som skulle ändras.

När configuratorn frågar om **printer.cfg**, välj **"Keep existing file"** om du redan har en
fungerande printer.cfg. Annars ersätts dina egna värden (offsets, rotation distance, PID med mera).

## Inställningar

```ini
[gcode_macro RatOS]
variable_cartographer_touch_start_print_true_zero: True   # False = bara scan, ingen touch i START_PRINT
variable_cartographer_touch_true_zero_temp: 150           # max 150 (pluginets gräns)
variable_prime_blob_z: 0.5                                # höj (t.ex. 1.5) om blobben dränker munstycket
```

## Live-accelerometer (Cartographer V4)

RatOS Analysis-sida kan bara visa Host, Control Board, Toolboard och Beacon. Om ingen ADXL är
inkopplad på styrkortet kan du döpa Cartographers ADXL345 till `controlboard`. Då syns den live under
Stream → Accelerometer → **Control Board**, och input shaper använder den också:

```ini
[adxl345 controlboard]
cs_pin: cartographer:PA0   # V4 (V3: PA3)
spi_bus: spi1

[resonance_tester]
accel_chip: adxl345 controlboard
```

## Live Z-offset

Justera Z i Mainsail under utskriften, tryck sedan **Save** (`Z_OFFSET_APPLY_PROBE`) och `SAVE_CONFIG`.
Eftersom START_PRINT gör touch uppdateras touch-modellens z_offset. Pluginet tillåter inte positiv
z_offset för touch, så munstycket kan som mest sänkas med nuvarande (negativa) touch-offset.

## Så fungerar det

`build.py` kopierar de RatOS-makron som bara känner till `[probe]`, `[bltouch]` och `[beacon]`
(`SAVE_PROBE_RESULT`, `PROBE_FOR_PRIMING`, `PRIME_BLOB`, `_START_PRINT_BED_MESH`) från din
RatOS-installation och ändrar dem med exakta textmatchningar. Om en RatOS-uppdatering ändrar något så
att en ändring inte passar längre, stoppar bygget och behåller föregående `cartographer.cfg` i stället
för att skriva en felaktig (se `journalctl -u klipper` eller kör `python3 ~/ratos-cartographer/build.py`).

## Stöds inte

Funktioner i RatOS som bara finns för Beacon: adaptiv heat soak, scan compensation, kompensation för
munstyckets värmeutvidgning, contact-mesh/Z-tilt och configuratorns knapp för Beacon-firmware.

## Avinstallera

```bash
rm ~/ratos-configurator/configuration/z-probe/cartographer.cfg ~/klipper/klippy/extras/trsync_timeout.py
sudo systemctl disable --now ratos-cartographer.path
sudo rm /etc/udev/rules.d/99-cartographer.rules /etc/systemd/system/klipper.service.d/ratos-cartographer.conf \
  /etc/systemd/system/ratos-cartographer.path /etc/systemd/system/ratos-cartographer.service
sudo systemctl daemon-reload
```

Välj sedan en annan probe i configuratorn och ta bort `[update_manager ratos-cartographer]` från
`moonraker.conf`.

## Licens

GPL-3.0, samma som Klipper och RatOS. Inte kopplat till Rat Rig eller Cartographer3D.
