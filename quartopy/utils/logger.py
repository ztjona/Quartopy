# -*- coding: utf-8 -*-

"""
Python 3
25 / 05 / 2025
@author: z_tjona

"I find that I don't understand things unless I try to program them."
-Donald E. Knuth
"""
# ----------------------------- logging --------------------------
import logging
from sys import stdout
from datetime import datetime


logging.basicConfig(
    level=logging.DEBUG,
    format="[%(asctime)s][%(levelname)s] %(message)s",
    stream=stdout,
    datefmt="%m-%d %H:%M:%S",
)
logger = logging.getLogger("Quartopy")
logger.debug("Creating logger for Quartopy game")
logger.info(datetime.now())
