#!/bin/bash
# ratos-cartographer installer: adds Cartographer 3D as a Z probe to RatOS 2.1 (Beacon is left untouched).
# Run as your normal user (not root):  bash ~/ratos-cartographer/install.sh
# Safe to run again at any time.
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RATOS_CFG="${HOME}/ratos-configurator/configuration"
KLIPPER_DIR="${HOME}/klipper"
CONFIG_DIR="${HOME}/printer_data/config"
MOONRAKER_CONF="${CONFIG_DIR}/moonraker.conf"
DROPIN_DIR="/etc/systemd/system/klipper.service.d"

if [ "$(id -u)" -eq 0 ]; then
	echo "Do not run as root. Run as your normal user (sudo is used where needed)."
	exit 1
fi

echo "==> Checking requirements"
[ -d "${RATOS_CFG}/z-probe" ] || { echo "RatOS configuration not found at ${RATOS_CFG}"; exit 1; }
[ -d "${KLIPPER_DIR}/klippy/extras" ] || { echo "Klipper not found at ${KLIPPER_DIR}"; exit 1; }
PLUGIN_MISSING=0
if ! "${HOME}/klippy-env/bin/python" -c "import cartographer" 2>/dev/null; then
	PLUGIN_MISSING=1
	echo "NOTE: Cartographer Klipper plugin not installed yet. That is fine: install it after the"
	echo "      RatOS Setup Wizard (see GUIDE.md). Klipper shows an error about [cartographer] until then."
fi

echo "==> Linking optional Klipper extra trsync_timeout.py (off unless [trsync_timeout] is in printer.cfg)"
ln -sf "${HERE}/klippy/trsync_timeout.py" "${KLIPPER_DIR}/klippy/extras/trsync_timeout.py"

echo "==> Generating ${RATOS_CFG}/z-probe/cartographer.cfg"
python3 "${HERE}/build.py" --ratos-config "${RATOS_CFG}" --config-dir "${CONFIG_DIR}"

echo "==> Installing system parts (needs sudo)"
# 1. udev rule -> /dev/cartographer
sed "s#@RATOS_SCRIPTS@#${RATOS_CFG}/scripts#" "${HERE}/99-cartographer.rules.in" > /tmp/99-cartographer.rules
sudo install -m 644 /tmp/99-cartographer.rules /etc/udev/rules.d/99-cartographer.rules
rm -f /tmp/99-cartographer.rules
sudo udevadm control --reload-rules
sudo udevadm trigger --subsystem-match=tty
# 2. Rebuild cartographer.cfg every time Klipper starts, so RatOS updates are picked up automatically.
#    The leading '-' means a failed build never stops Klipper; the previous cartographer.cfg is kept.
#    The same run also disables the [probe] section the RatOS configurator generates for Cartographer.
BUILD_CMD="/usr/bin/python3 ${HERE}/build.py --quiet --ratos-config ${RATOS_CFG} --config-dir ${CONFIG_DIR}"
sudo mkdir -p "${DROPIN_DIR}"
printf '[Service]\nExecStartPre=-%s\n' "${BUILD_CMD}" | sudo tee "${DROPIN_DIR}/ratos-cartographer.conf" > /dev/null
# 3. Run the same fix immediately when the configurator saves RatOS.cfg / printer.cfg.
sudo tee /etc/systemd/system/ratos-cartographer.service > /dev/null <<EOF
[Unit]
Description=ratos-cartographer: keep cartographer.cfg and generated RatOS config in sync
[Service]
Type=oneshot
User=$(id -un)
ExecStart=${BUILD_CMD}
EOF
sudo tee /etc/systemd/system/ratos-cartographer.path > /dev/null <<EOF
[Unit]
Description=ratos-cartographer: watch RatOS.cfg and printer.cfg
[Path]
PathChanged=${CONFIG_DIR}/RatOS.cfg
PathChanged=${CONFIG_DIR}/printer.cfg
[Install]
WantedBy=multi-user.target
EOF
sudo systemctl daemon-reload
sudo systemctl enable --now ratos-cartographer.path

echo "==> Moonraker update manager"
ORIGIN="$(git -C "${HERE}" remote get-url origin 2>/dev/null || true)"
if [ -z "${ORIGIN}" ]; then
	echo "Not a git clone, skipping (install with git clone to get updates in Mainsail/Fluidd)."
elif grep -q '^\[update_manager ratos-cartographer\]' "${MOONRAKER_CONF}" 2>/dev/null; then
	echo "Already present in moonraker.conf"
else
	BRANCH="$(git -C "${HERE}" rev-parse --abbrev-ref HEAD)"
	cat >> "${MOONRAKER_CONF}" <<EOF

[update_manager ratos-cartographer]
type: git_repo
path: ${HERE}
origin: ${ORIGIN}
primary_branch: ${BRANCH}
is_system_service: False
managed_services: klipper
EOF
	echo "Added [update_manager ratos-cartographer]. Restart Moonraker to see it in the update list."
fi

sleep 1
echo
if [ -e /dev/cartographer ]; then echo "/dev/cartographer -> $(readlink -f /dev/cartographer)"; else echo "NOTE: /dev/cartographer not present (Cartographer not on USB?)"; fi
echo
echo "Done. Next steps (see GUIDE.md):"
echo " 1. RatOS Setup Wizard: choose 'Cartographer 3D' as Z probe and save."
if [ "${PLUGIN_MISSING}" -eq 1 ]; then
	echo " 2. Install the Cartographer (hardware, firmware, Klipper plugin): https://docs.cartographer3d.com"
	echo "    Skip its printer.cfg / [safe_z_home] / [homing_override] parts."
fi
echo " -> printer.cfg: set [cartographer] x_offset/y_offset and [bed_mesh] zero_reference_position."
echo " -> Restart Klipper, calibrate, then run CARTOGRAPHER_RATOS_STATUS."
