#!/usr/bin/env python
"""
Mod Importer for Games by SuperGiant Games'

https://github.com/MagicGnomads/sgg-mod-format
"""
__version__ = "0.1"
__status__ = "Development"

import logging

from sggmi import deploy_mods, initialize_logs


def main(*args, **kwargs):

    initialize_logs()

    try:
        deploy_mods(*args, **kwargs)
    except Exception as exc:
        logging.error(
            "There was a critical error, now attempting to display the error.\n"
            "(if this doesn't work, try again in a terminal that doesn't close, or check the log files)"
        )
        logging.getLogger("root").exception(exc)

    input("Press any key to end program...")
