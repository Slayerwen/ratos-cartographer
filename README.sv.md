# Cartographer 3D för RatOS 2.1

[English](README.md)

Gör att du kan välja **Cartographer 3D** som Z-probe i RatOS Setup Wizard.

- Touch-homing (exakt Z=0) i RatOS START_PRINT, efter Z-tilt och före bed mesh
- Snabb scan-mesh, och adaptiv priming som mäter bädden
- Cartographer V4:s accelerometer för input shaper och Realtime Analysis
- Ändrar inte RatOS eller Klipper, så deras uppdateringar fungerar som vanligt

**Stöder:** Cartographer V3 och V4, USB eller CAN, plugin 1.9 eller nyare.
**Testat** med V4 via USB och RatOS 2.1.3. V3 och CAN bör också fungera. Rapportera gärna!

## Installation

Följ **steg-för-steg-guiden** i [README.md](README.md#install-guide) (på engelska). Kort sammanfattat:

1. Installera RatOS och **stanna innan Setup Wizard frågar efter hårdvara**.
2. Installera det här tillägget via SSH:
   ```bash
   git clone https://github.com/Slayerwen/ratos-cartographer ~/ratos-cartographer
   ```
   ```bash
   bash ~/ratos-cartographer/install.sh
   ```
3. Gör klart Setup Wizard och välj **Probe → Cartographer 3D**.
4. Installera och kalibrera Cartographer enligt deras guide, men lägg **inte** till `[safe_z_home]`
   eller `[homing_override]`. Kontrollera sedan med `CARTOGRAPHER_RATOS_STATUS`.
5. Kontrollera printer.cfg:
   - **Ta bort** `[safe_z_home]` och `[homing_override]`, och med CAN raderna `serial` och
     `restart_method`. Ha inte `CARTOGRAPHER_TOUCH_HOME` i slicerns startkod.
   - **Kontrollera** att `zero_reference_position` är bäddens mitt.
   - **Klistra in** `variable_prime_blob_z: 1.5` under `[gcode_macro RatOS]`, och döp om `[adxl345]`
     till `[adxl345 controlboard]` (och `accel_chip: adxl345 controlboard`) så att accelerometern
     syns i Realtime Analysis.
6. Skriv ut med din vanliga RatOS-slicerprofil.

Problem eller frågor: se avsnittet **Problems?** i [README.md](README.md#problems), eller skapa en
issue här på GitHub.

## Licens

GPL-3.0, samma som Klipper och RatOS. Inte kopplat till Rat Rig eller Cartographer3D.
