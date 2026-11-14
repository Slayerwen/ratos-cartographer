# Raises Klipper's multi-MCU homing sync timeout (mcu.TRSYNC_TIMEOUT) without editing
# klippy/mcu.py, so the Klipper repo stays clean for updates.
#
# Fixes "Communication timeout during homing" when homing/probing involves two MCUs
# (e.g. Cartographer on USB + mainboard) on slower hosts such as a Raspberry Pi 3.
# Klipper's TriggerDispatch reads mcu.TRSYNC_TIMEOUT each time homing starts.
#
# [trsync_timeout]
# timeout: 0.05
import logging

import mcu


class TrsyncTimeout:
    def __init__(self, config):
        self.timeout = config.getfloat("timeout", 0.05, minval=0.025, maxval=0.25)
        if not hasattr(mcu, "TRSYNC_TIMEOUT"):
            raise config.error("trsync_timeout: this Klipper version has no mcu.TRSYNC_TIMEOUT")
        old = mcu.TRSYNC_TIMEOUT
        mcu.TRSYNC_TIMEOUT = self.timeout
        logging.info("trsync_timeout: TRSYNC_TIMEOUT %.3f -> %.3f", old, self.timeout)

    def get_status(self, eventtime):
        return {"timeout": mcu.TRSYNC_TIMEOUT}


def load_config(config):
    return TrsyncTimeout(config)
