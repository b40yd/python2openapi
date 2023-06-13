# encoding: utf-8

import os
import sys
import logging

path = os.path.dirname(__file__)

sys.path.append(os.path.dirname(os.path.abspath(path)))
from test_schema import (
    test_list_object_validate,
    test_list_validate,
    test_object_validate,
    test_validate,
)


if __name__ == "__main__":
    test_validate()
    test_list_validate()
    test_list_object_validate()
    test_object_validate()

    # format the log message
    logging.info("hello, world")
