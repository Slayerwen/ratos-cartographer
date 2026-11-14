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
4. Installera Cartographer enligt deras guide, men lägg **inte** till `[safe_z_home]` eller
   `[homing_override]`.
5. Lägg in dina offsets och `zero_reference_position` (bäddens mitt) i printer.cfg.
6. Kalibrera: `G28`, `CARTOGRAPHER_SCAN_CALIBRATE`, `CARTOGRAPHER_TOUCH_CALIBRATE`, `SAVE_CONFIG`.
7. Skriv ut med din vanliga RatOS-slicerprofil.

Problem eller frågor: se avsnittet **Problems?** i [README.md](README.md#problems), eller skapa en
issue här på GitHub.

## Licens

GPL-3.0, samma som Klipper och RatOS. Inte kopplat till Rat Rig eller Cartographer3D.
