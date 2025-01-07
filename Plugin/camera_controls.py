#!/usr/bin/env python3
# -*- coding: utf-8 -*-
##########################################################################
#
#
#  File name: camera_controls included by multi_altiz.py
#
#   Synopsis:  This program is used by Matrox Capture Works as a plug-in.
#              It performs Multi-AltiZ configuration, alignment, transforms
#              and merge of all acquisitions into a single point-cloud.
#
#  Copyright © Matrox Electronic Systems Ltd., 1992-YYYY.
#  All Rights Reserved

from config import *
from common import *
from mil import *
import os
import sys
import json
sys.path.append(os.path.dirname(os.path.realpath(__file__)))


def set_io(dig_id, line, value):
    MdigControlFeature(
        dig_id,
        M_FEATURE_VALUE,
        MIL_TEXT("LineSelector"),
        M_TYPE_STRING,
        MIL_TEXT(line),
    )
    MdigControlFeature(
        dig_id,
        M_FEATURE_VALUE,
        MIL_TEXT("LineSource"),
        M_TYPE_STRING,
        MIL_TEXT("UserOutput0"),
    )

    MdigControlFeature(
        dig_id,
        M_FEATURE_VALUE,
        MIL_TEXT("UserOutputSelector"),
        M_TYPE_STRING,
        MIL_TEXT("UserOutput0"),
    )
    if value:
        MdigControlFeature(
            dig_id,
            M_FEATURE_VALUE,
            MIL_TEXT("UserOutputValue"),
            M_TYPE_STRING,
            MIL_TEXT("1"),
        )
    else:
        MdigControlFeature(
            dig_id,
            M_FEATURE_VALUE,
            MIL_TEXT("UserOutputValue"),
            M_TYPE_STRING,
            MIL_TEXT("0"),
        )


def get_io(dig_id, line):
    MdigControlFeature(
        dig_id,
        M_FEATURE_VALUE,
        MIL_TEXT("LineSelector"),
        M_TYPE_STRING,
        MIL_TEXT(line),
    )

    value = MdigInquireFeature(
        dig_id, M_FEATURE_VALUE, MIL_TEXT(
            "LineStatus"), M_TYPE_STRING, None
    )
    if value == "1":
        return True
    return False


def findconnection(cams, secondary_exlude, line, main):

    found_cam = ""
    set_io(gData.cameras[main].dig_id, line, True)
    for cam in cams:
        if get_io(gData.cameras[cam].dig_id, "Line0"):
            if cam not in secondary_exlude:
                found_cam = cam

    set_io(gData.cameras[main].dig_id, line, False)
    return found_cam


def auto_detect_camera_topology(main_camera_user_name):

    # populate active cameras
    cams = []

    for camera_name in gData.cameras.keys():
        gData.cameras[camera_name].topology_in = ""
        gData.cameras[camera_name].topology_out = ""
        gData.cameras[camera_name].pdata["Index"] = 0
        if gData.cameras[camera_name].dig_id:
            cams.append(camera_name)
            gData.cameras[camera_name].pdata["Status"] = ""
        else:
            gData.cameras[camera_name].pdata["Status"] = STRING_NOT_ALLOCATED

    # set all outputs off all cameras to OFF
    for camera_name in cams:
        set_io(gData.cameras[camera_name].dig_id, "Line4", False)

    # read line0 of all cameras to exclude does that are not OFF
    secondary_exlude = []
    for camera_name in cams:
        if get_io(gData.cameras[camera_name].dig_id, "Line0") == True:
            secondary_exlude.append(camera_name)

    # set all outputs off all cameras to OFF
    for camera_name in cams:
        set_io(gData.cameras[camera_name].dig_id, "Line5", False)

    # read line0 of all cameras to exclude does that are not OFF
    for camera_name in cams:
        if get_io(gData.cameras[camera_name].dig_id, "Line1") == True:
            secondary_exlude.append(camera_name)

    # find topology
    for cam in cams:
        foundcam4 = findconnection(cams, secondary_exlude, "Line4", cam)
        foundcam5 = findconnection(cams, secondary_exlude, "Line5", cam)
        if foundcam4:
            gData.cameras[cam].topology_out = foundcam4
            gData.cameras[foundcam4].topology_in = cam

            connectionstatus = STRING_PARTIAL_CONNECTION
            if foundcam5 == foundcam4:
                connectionstatus = STRING_CONNECTED

            gData.cameras[cam].pdata["Status"] = connectionstatus
            gData.cameras[foundcam4].pdata["Status"] = connectionstatus

    # find main camera
    for cam in cams:
        if (
            gData.cameras[cam].topology_in == ""
            and gData.cameras[cam].topology_out != ""
        ):
            gData.main_camera = cam
            gData.cameras[cam].pdata["Status"] = STRING_MAINCAMERA
        elif gData.cameras[cam].topology_in == "":
            gData.cameras[cam].pdata["Status"] = STRING_NOT_PART_TOPOLOGY
        else:
            extra = ""
            if gData.cameras[cam].pdata["Status"] == STRING_PARTIAL_CONNECTION:
                extra = STRING_PARTIAL_CONNECTION

            gData.cameras[cam].pdata["Status"] = (
                STRING_SECONDAY_CAMERA_CONNECTION
                + gData.cameras[cam].topology_in
                + extra
            )

    # set topology indexes
    if gData.main_camera != STRING_NOT_DETECTED:
        index = 0
        cam = gData.main_camera
        gData.cameras[cam].pdata["Index"] = index
        while gData.cameras[cam].topology_out != "":
            index += 1
            cam = gData.cameras[cam].topology_out
            gData.cameras[cam].pdata["Index"] = index
    
    # set total number of cameras.
    for cam in cams:
        gData.cameras[cam].pdata["TotalNumberOfCameras"] = len(cams)

    return


def program_cameras(main_camera_user_name):

    if gData.main_camera == STRING_NOT_DETECTED:
        return

    # adjust laser multplexing parameters based on exposure and position, before programming in camera, to make sure initial values are synchronized.
    set_laser_multiplexing(gData.laser_multiplexing_mode)

    isPartialConnected = False

    # program main camera to output on exposure out.
    main_dig_id = gData.cameras[main_camera_user_name].dig_id

    MdigControlFeature(
        main_dig_id,
        M_FEATURE_VALUE,
        MIL_TEXT("Scan3dCoordinateSystemAnchorMode"),
        M_TYPE_STRING,
        MIL_TEXT("ReferencePoint")
    )
    MdigControlFeature(
        main_dig_id,
        M_FEATURE_VALUE,
        MIL_TEXT("LineSelector"),
        M_TYPE_STRING,
        MIL_TEXT("Line4"),
    )
    MdigControlFeature(
        main_dig_id,
        M_FEATURE_VALUE,
        MIL_TEXT("LineSource"),
        M_TYPE_STRING,
        MIL_TEXT("ExposureActive"),
    )

    MdigControlFeature(
        main_dig_id,
        M_FEATURE_VALUE,
        MIL_TEXT("LineSelector"),
        M_TYPE_STRING,
        MIL_TEXT("Line5"),
    )
    MdigControlFeature(
       main_dig_id,
       M_FEATURE_VALUE,
       MIL_TEXT("LineSource"),
       M_TYPE_STRING,
       MIL_TEXT("LogicBlock0"),
    )

    MdigControlFeature(
        main_dig_id,
        M_FEATURE_VALUE,
        MIL_TEXT("LogicBlockSelector"),
        M_TYPE_STRING,
        MIL_TEXT("LogicBlock0"),
    )

    MdigControlFeature(
        main_dig_id,
        M_FEATURE_VALUE,
        MIL_TEXT("LogicBlockFunction"),
        M_TYPE_STRING,
        MIL_TEXT("LatchedLUT"),
    )

    MdigControlFeature(
        main_dig_id,
        M_FEATURE_VALUE,
        MIL_TEXT("LogicBlockLUTSelector"),
        M_TYPE_STRING,
        MIL_TEXT("Value"),
    )
    MdigControlFeature(
        main_dig_id,
        M_FEATURE_VALUE,
        MIL_TEXT("LogicBlockInputSelector"),
        M_TYPE_STRING,
        MIL_TEXT("0"),
    )
    MdigControlFeature(
        main_dig_id,
        M_FEATURE_VALUE,
        MIL_TEXT("LogicBlockInputSource"),
        M_TYPE_STRING,
        MIL_TEXT("AcquisitionActive"),
    )

    MdigControlFeature(
        main_dig_id,
        M_FEATURE_VALUE,
        MIL_TEXT("LogicBlockInputSelector"),
        M_TYPE_STRING,
        MIL_TEXT("1"),
    )
    MdigControlFeature(
        main_dig_id,
        M_FEATURE_VALUE,
        MIL_TEXT("LogicBlockInputSource"),
        M_TYPE_STRING,
        MIL_TEXT("False"),
    )

    MdigControlFeature(
        main_dig_id,
        M_FEATURE_VALUE,
        MIL_TEXT("LogicBlockLUTValueAll"),
        M_TYPE_STRING,
        MIL_TEXT("1"),
    )

    MdigControlFeature(
        main_dig_id,
        M_FEATURE_VALUE,
        MIL_TEXT("LogicBlockLUTSelector"),
        M_TYPE_STRING,
        MIL_TEXT("Enable"),
    )
    MdigControlFeature(
        main_dig_id,
        M_FEATURE_VALUE,
        MIL_TEXT("LogicBlockInputSelector"),
        M_TYPE_STRING,
        MIL_TEXT("0"),
    )
    MdigControlFeature(
        main_dig_id,
        M_FEATURE_VALUE,
        MIL_TEXT("LogicBlockInputSource"),
        M_TYPE_STRING,
        MIL_TEXT("AcquisitionActive"),
    )
    MdigControlFeature(
        main_dig_id,
        M_FEATURE_VALUE,
        MIL_TEXT("LogicBlockInputSelector"),
        M_TYPE_STRING,
        MIL_TEXT("1"),
    )

    MdigControlFeature(
        main_dig_id,
        M_FEATURE_VALUE,
        MIL_TEXT("LogicBlockInputSource"),
        M_TYPE_STRING,
        MIL_TEXT("AcquisitionStop"),
    )

    MdigControlFeature(
        main_dig_id,
        M_FEATURE_VALUE,
        MIL_TEXT("LogicBlockLUTValueAll"),
        M_TYPE_STRING,
        MIL_TEXT("6"),
    )


    MdigControlFeature(
        main_dig_id,
        M_FEATURE_VALUE,
        MIL_TEXT("TriggerSelector"),
        M_TYPE_STRING,
        MIL_TEXT("LineStart"),
    )
    MdigControlFeature(
        main_dig_id,
        M_FEATURE_VALUE,
        MIL_TEXT("TriggerSource"),
        M_TYPE_STRING,
        MIL_TEXT("Encoder0"),
    )
    MdigControlFeature(
        main_dig_id,
        M_FEATURE_VALUE,
        MIL_TEXT("TriggerMode"),
        M_TYPE_STRING,
        MIL_TEXT("On"),
    )
    MdigControlFeature(
        main_dig_id,
        M_FEATURE_VALUE,
        MIL_TEXT("TriggerActivation"),
        M_TYPE_STRING,
        MIL_TEXT("RisingEdge"),
    )

    effectiveStepWorld = MdigInquireFeature(
        main_dig_id,
        M_FEATURE_VALUE,
        MIL_TEXT("Scan3dMotionEffectiveStepWorld"),
        M_TYPE_DOUBLE,
        None,)

    # inquire main camera settings

    # copy the feature from the main camera to the secondary cameras.
    features_to_copy = ["Scan3dVolumeLengthWorld", "SourceSynchronizationMode", "Scan3dVolumeZMode", "Scan3dCoordinateSystemAnchorMode", "Scan3dMotionDirection",
                        "DecimationHorizontal", "DecimationVertical", "SourceSelector",
                        "QuickSetupFusionRange", "QuickSetupFusionConfidence", "QuickSetupFusionReflectance", "QuickSetupFusionScatter",
                        "Scan3dPeakWidthNominal", "Scan3dPeakWidthDelta", "Scan3dPeakContrastMin", "Scan3dPeakReflectanceWindowSize", "Scan3dPeakMedianFilterSize",
                        "Scan3dPeakFusionDistanceMax", "Scan3dPeakFusionRange", "Scan3dPeakFusionReflectance", "Scan3dPeakFusionScatter",
                        "Scan3dPeakFusionFilterMode", "Scan3dPeakFusionSelectionMode", "Scan3dPeakSelectionMode"]

    # now setup cameras
    for camera_name in gData.cameras.keys():
        if main_camera_user_name != camera_name:
            if gData.cameras[camera_name].dig_id:
                dig_id = gData.cameras[camera_name].dig_id

                MdigControlFeature(dig_id, M_FEATURE_VALUE, MIL_TEXT(
                    "SourceSelector"), MIL. M_TYPE_STRING, MIL_TEXT("Source0"),)

                MdigControlFeature(dig_id, M_FEATURE_VALUE, MIL_TEXT("Scan3dMotionInputType"),
                                   M_TYPE_STRING,
                                   MIL_TEXT("Step"),
                                   )

                MdigControlFeature(
                    dig_id,
                    M_FEATURE_VALUE,
                    MIL_TEXT("Scan3dMotionStepWorld"),
                    M_TYPE_DOUBLE,
                    effectiveStepWorld,
                )
                MdigControlFeature(
                    dig_id,
                    M_FEATURE_VALUE,
                    MIL_TEXT("TimerSelector"),
                    M_TYPE_STRING,
                    MIL_TEXT("Timer0"),
                )
                MdigControlFeature(
                    dig_id,
                    M_FEATURE_VALUE,
                    MIL_TEXT("TimerTriggerSource"),
                    M_TYPE_STRING,
                    MIL_TEXT("Off"),
                )

                MdigControlFeature(
                    dig_id,
                    M_FEATURE_VALUE,
                    MIL_TEXT("LineSelector"),
                    M_TYPE_STRING,
                    MIL_TEXT("Line4"),
                )
                MdigControlFeature(
                    dig_id,
                    M_FEATURE_VALUE,
                    MIL_TEXT("LineSource"),
                    M_TYPE_STRING,
                    MIL_TEXT("Input0"),
                )

                MdigControlFeature(
                    dig_id,
                    M_FEATURE_VALUE,
                    MIL_TEXT("LineSelector"),
                    M_TYPE_STRING,
                    MIL_TEXT("Line5"),
                )
                MdigControlFeature(
                    dig_id,
                    M_FEATURE_VALUE,
                    MIL_TEXT("LineSource"),
                    M_TYPE_STRING,
                    MIL_TEXT("Input1"),
                )

                # laser multiplexing off : timer is not used
                # laser multiplexing custom : timer rising edge with delay value
                # laser multiplexing neighbour : if delay is 0 : timer rising edge delay 0 : if delay is non zero : timer falling edge delay value
                TimerActivation = "RisingEdge"
                TimerDuration = str(125)
                TimerDelay = str(0)
                if gData.laser_multiplexing_mode == "Custom" and gData.cameras[camera_name].pdata["LaserDelayCustom"] >= 0:
                    TimerDelay = str(gData.cameras[camera_name].pdata["LaserDelayCustom"])
                elif gData.laser_multiplexing_mode == "Neighbour" and gData.cameras[camera_name].pdata["LaserDelay"] > 0:
                    TimerDelay = str(gData.cameras[camera_name].pdata["LaserDelay"])
                    TimerActivation = "FallingEdge"

                MdigControlFeature(
                    dig_id,
                    M_FEATURE_VALUE,
                    MIL_TEXT("TimerSelector"),
                    M_TYPE_STRING,
                    MIL_TEXT("Timer0"),
                )
                MdigControlFeature(
                    dig_id,
                    M_FEATURE_VALUE,
                    MIL_TEXT("TimerTriggerSource"),
                    M_TYPE_STRING,
                    MIL_TEXT("Line0"),
                )
                MdigControlFeature(
                    dig_id,
                    M_FEATURE_VALUE,
                    MIL_TEXT("TimerTriggerActivation"),
                    M_TYPE_STRING,
                    MIL_TEXT(TimerActivation),
                )
                MdigControlFeature(
                    dig_id,
                    M_FEATURE_VALUE,
                    MIL_TEXT("TimerDuration"),
                    M_TYPE_STRING,
                    MIL_TEXT(TimerDuration),
                )
                MdigControlFeature(
                    dig_id,
                    M_FEATURE_VALUE,
                    MIL_TEXT("TimerDelay"),
                    M_TYPE_STRING,
                    MIL_TEXT(TimerDelay),
                )

                TrigActivation = "RisingEdge"
                TrigSource = "Line0"
                if gData.laser_multiplexing_mode != "Off":
                    TrigSource = "Timer0Start"

                MdigControlFeature(
                    dig_id,
                    M_FEATURE_VALUE,
                    MIL_TEXT("TriggerSelector"),
                    M_TYPE_STRING,
                    MIL_TEXT("LineStart"),
                )
                MdigControlFeature(
                    dig_id,
                    M_FEATURE_VALUE,
                    MIL_TEXT("TriggerSource"),
                    M_TYPE_STRING,
                    MIL_TEXT(TrigSource),
                )
                MdigControlFeature(
                    dig_id,
                    M_FEATURE_VALUE,
                    MIL_TEXT("TriggerMode"),
                    M_TYPE_STRING,
                    MIL_TEXT("On"),
                )
                MdigControlFeature(
                    dig_id,
                    M_FEATURE_VALUE,
                    MIL_TEXT("TriggerActivation"),
                    M_TYPE_STRING,
                    MIL_TEXT(TrigActivation),
                )

                for feature in features_to_copy:
                    accessmode = MdigInquireFeature(
                        main_dig_id,
                        M_FEATURE_ACCESS_MODE,
                        MIL_TEXT(feature),
                        M_TYPE_INT64,
                        None,)

                    if M_FEATURE_IS_READABLE(accessmode) and M_FEATURE_IS_AVAILABLE(accessmode):
                        value = MdigInquireFeature(
                            main_dig_id,
                            M_FEATURE_VALUE,
                            MIL_TEXT(feature),
                            M_TYPE_STRING,
                            None,
                        )

                        accessmode = MdigInquireFeature(
                            dig_id,
                            M_FEATURE_ACCESS_MODE,
                            MIL_TEXT(feature),
                            M_TYPE_INT64,
                            None,)
                        if M_FEATURE_IS_WRITABLE(accessmode) and M_FEATURE_IS_AVAILABLE(accessmode):
                            MdigControlFeature(
                                dig_id,
                                M_FEATURE_VALUE,
                                MIL_TEXT(feature),
                                M_TYPE_STRING,
                                value,
                            )


def set_laser_multiplexing(value):

    if gData.main_camera == STRING_NOT_DETECTED:
        return

    gData.laser_multiplexing_mode = value

    gData.cameras[gData.main_camera].pdata["LaserMode"] = value

    for camera_name in gData.cameras.keys():

        if (camera_name != gData.main_camera):
            gData.cameras[gData.main_camera].pdata["LaserMode"] = ""

        if value == "Off":
            gData.cameras[camera_name].pdata["LaserDelay"] = 0
            gData.cameras[camera_name].pdata["LaserDelayCustom"] = 0
        elif value == "Neighbour":
            LaserDelay = 0
            if gData.cameras[camera_name].pdata["Index"] % 2 == 0:  # even
                LaserDelay = 0
            else:
                LaserDelay = 25
            gData.cameras[camera_name].pdata["LaserDelay"] = LaserDelay
            gData.cameras[camera_name].pdata["LaserDelayCustom"] = 0
        else:
            gData.cameras[camera_name].pdata["LaserDelay"] = 0


def save_camera_settings_in_camera(camera):

    for camera_name in gData.cameras.keys():
        cam = gData.cameras[camera_name]
        if cam.dig_id:
            MdigControlFeature(cam.dig_id, M_FEATURE_VALUE, MIL_TEXT(
                "UserSetSelector"), M_TYPE_STRING, MIL_TEXT(STRING_USERSET_CONTAINING_CONFIG))
            MdigControlFeature(cam.dig_id, M_FEATURE_VALUE, MIL_TEXT(
                "UserSetDescription"), M_TYPE_STRING, MIL_TEXT(STRING_USERSET_DESCRIPTION))

            try:
                j = json.dumps(cam.pdata)
                print(j)
                MdigControlFeature(
                    cam.dig_id,
                    M_FEATURE_VALUE,
                    MIL_TEXT("DeviceUserData"),
                    M_TYPE_STRING,
                    MIL_TEXT(j),
                )
            except ValueError as e:
                print(e)
            MdigControlFeature(cam.dig_id, M_FEATURE_EXECUTE, MIL_TEXT(
                "UserSetSave"), M_DEFAULT, M_NULL)        


def load_camera_settings(camera):

    # now setup cameras
    for camera_name in gData.cameras.keys():
        cam = gData.cameras[camera_name]
        #cam = gData.cameras[camera]
        if cam.dig_id:

            MdigControlFeature(cam.dig_id, M_FEATURE_VALUE, MIL_TEXT(
                "UserSetSelector"), M_TYPE_STRING, cam.pdata["UserSet"])
            description = MdigInquireFeature(cam.dig_id, M_FEATURE_VALUE, MIL_TEXT(
                "UserSetDescription"), M_TYPE_STRING, )

            # only load user-set if description string is set.
            if description == STRING_USERSET_DESCRIPTION:
                MdigControlFeature(cam.dig_id, M_FEATURE_EXECUTE, MIL_TEXT(
                    "UserSetLoad"), M_DEFAULT, M_NULL)

            j = MdigInquireFeature(
                cam.dig_id,
                M_FEATURE_VALUE,
                MIL_TEXT("DeviceUserData"),
                M_TYPE_STRING,
                None
            )
            try:
                data = json.loads(j)
                #cam.pdata.update(data)
                cam.pdata["Distance"] = data["Distance"]
                gData.distanceX =  cam.pdata["Distance"]
                cam.pdata["TranslationX"] = data["TranslationX"]
                cam.pdata["TranslationY"] = data["TranslationY"]
                cam.pdata["TranslationZ"] = data["TranslationZ"]
                cam.pdata["RotationX"] = data["RotationX"]
                cam.pdata["RotationY"] = data["RotationY"]
                cam.pdata["RotationZ"] = data["RotationZ"]

            except ValueError as e:
                print(e)

                    
def update_camera_UserData(camera):

    for camera_name in gData.cameras.keys():
        cam = gData.cameras[camera_name]
        if cam.dig_id:
            try:
                j = json.dumps(cam.pdata)
                print(j)
                MdigControlFeature(
                    cam.dig_id,
                    M_FEATURE_VALUE,
                    MIL_TEXT("DeviceUserData"),
                    M_TYPE_STRING,
                    MIL_TEXT(j),
                )
            except ValueError as e:
                print(e)