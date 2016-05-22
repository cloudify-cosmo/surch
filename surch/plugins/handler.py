import sys

from .. import logger


lgr = logger.init()


def show_result(log=None):
        with open(log, 'r') as results_file:
            results = results_file.read()
        lgr.info(results)
