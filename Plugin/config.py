#!/usr/bin/env python3
# -*- coding: utf-8 -*-
##########################################################################
#
# 
#  File name: config.py included by multi_altiz.py  
#
#   Synopsis:  This program is used by Matrox Capture Works as a plug-in.
#              It performs Multi-AltiZ configuration, alignment, transforms
#              and merge of all acquisitions into a single point-cloud.
#
#  Copyright © Matrox Electronic Systems Ltd., 1992-YYYY.
#  All Rights Reserved

from mil import *
import sys
import os

sys.path.append(os.path.dirname(os.path.realpath(__file__)))

from common import *

# define STRINGS
STRING_NOT_PART_TOPOLOGY = "Not part of topology"
STRING_CONNECTED = "Connected"
STRING_NOT_ALLOCATED = "Not allocated"
STRING_MAINCAMERA = "Main camera"
STRING_SECONDAY_CAMERA_CONNECTION = "Secondary camera connected to "
STRING_NOT_DETECTED = "Not detected"
STRING_PARTIAL_CONNECTION = " (only 1 output connected: line4)"
STRING_USERSET_CONTAINING_CONFIG = "UserSet3"
STRING_USERSET_DESCRIPTION = "MultiAltiZ Configuration"

class CglobalData:
    def __init__(self):
        self.main_camera = STRING_NOT_DETECTED
        self.selected_camera = ""
        self.display_all_cameras = True
        self.color = False
        self.grabbing = False
        self.autosave = True
        self.do_reprogram = True
        self.do_alignment = False
        self.laser_multiplexing_mode = "Neighbour"  # Off, Neighbour, # Custom
        self.cameras = {}
        self.distanceX = 0.0;


class CWCameraData:
    def __init__(self, dig_id):
        userset = STRING_USERSET_CONTAINING_CONFIG
        self.sys_id = MdigInquire(dig_id, M_OWNER_SYSTEM, None)
        self.dig_id = dig_id
        self.mil_grab_container = []
        self.topology_in = ""
        self.topology_out = ""
        self.pdata = {
            "Status" : "",
            "UserSet" : STRING_USERSET_CONTAINING_CONFIG,
            "Index" : 0,
            "TotalNumberOfCameras" : 0, 
            "LaserMode" : "",
            "LaserDelay": 0,
            "Distance": 0.0,
            "LaserDelayCustom": 0,
            "TranslationX": 0,
            "TranslationY": 0,
            "TranslationZ": 0,
            "RotationX": 0,
            "RotationY": 0,
            "RotationZ": 0            
        }


if "gData" not in globals():
    global gData
    gData = CglobalData()
