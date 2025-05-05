#!/usr/bin/env python3
# -*- coding: utf-8 -*-
##########################################################################
#
#
#  File name: common.py
#
#   Synopsis:  This program is used by Matrox Capture Works as a plug-in.
#              It contains common settings used by all plug-ins.
#
#  Copyright © Matrox Electronic Systems Ltd., 1992-YYYY.
#  All Rights Reserved

import ctypes
import mil as MIL

class RoutingFunctions:
    GET_VERSION = 0
    GET_DESCRIPTION = 1
    DIG_IS_SUPPORTED = 2
    ALLOCATE = 3
    FREE = 4
    GET_UNIQUE_ID = 5
    GET_JSON = 6
    SET_VALUE = 7
    GET_VALUE = 8
    GRAB_CALLBACK = 9
    PREPROCESS_FRAME = 10
    LICENSE_IS_VALID = 11
    GET_IMG_PATH = 12
    FREE_RESOURCE = 13
    DUMP_SETTINGS = 14
    IS_GRAB_CAPABLE = 15
    CW_BUTTON_CLICKED = 16

class ButtonEvent:
    SINGLE_GRAB = 1
    START_CONTINUOUS_GRAB = 2
    STOP_CONTINUOUS_GRAB = 3
    GRAB_ABORT = 4
    FILE_ACCESS_DOWNLOAD = 5
    FILE_ACCESS_UPLOAD = 6

class LogType:
    LOG_ERROR = 0
    LOG_INFO = 1
    LOG_WARNING = 2
    LOG_DEBUG = 3


# define template json keys
KEY_DIG_ID = "dig id"
KEY_DISPLAY = "display"
KEY_DISPLAY_TITLE = "display title"
KEY_CONTAINER = "container"
KEY_CONTAINER_NAME = "container name"
KEY_NAME = "name"
KEY_MIL_ID = "mil_id"
KEY_MESSAGES = "messages"
KEY_MSG_STR = "msg"
KEY_MSG_SOURCE = "source"
KEY_MSG_TYPE = "msg type"
KEY_TITLE = "title"
KEY_X_TITLE = "x title"
KEY_Y_TITLE = "y title"
KEY_HISTOGRAM = "histogram"
KEY_MEMORY_TABLE = "mem table"
KEY_DATA_TABLE = "data table"
KEY_STATS = "stats"
KEY_MIN = "min"
KEY_MAX = "max"
KEY_MEAN = "mean"
KEY_VALUE = "Value"
KEY_SERVICE = "service"
KEY_ACCESS_MODE = "AccessMode"

class Service:
    CREATE_CONTAINER = 1
    EVENT_CALLBACK = 2
    SEND_MSG = 3
    SINGLE_GRAB = 4

