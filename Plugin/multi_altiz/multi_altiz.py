#!/usr/bin/env python3
# -*- coding: utf-8 -*-
##########################################################################
#
#
#  File name: multi_altiz.py
#
#   Synopsis:  This program is used by Capture Works as a plug-in.
#              It performs Multi-AltiZ configuration, alignment, transforms
#              and merge of all acquisitions into a single point-cloud.
#
#  Copyright © Matrox Electronic Systems Ltd., 1992-YYYY.
#  All Rights Reserved

import ctypes
from mil import *
import json
import os
import sys

sys.path.append(os.path.dirname(os.path.realpath(__file__)))

from common import *
from config import *
from camera_controls import *
from grab import *


plugin_name = "MultiAltiZPlugin"
plugin_image = "multi_altiz.png"
plugin_description = (
    "This plugin grabs from multiple Altizs and merges grabbed frames.\n"
    "It does not correct any rotation around the X-axis and the Z-axis.\n"
    "Grab must be performed on MAIN CAMERA only.\n"
    "Note: Default User set = User Set 3.\n"
    "Detailed steps:\n\n"
    "1. Position your cameras, making sure there's no pitch or yaw .\n"
    "2. Place your calibration tool on your conveyor.\n"
    "3. On the main camera, extend Multi Altiz Plugin tab.\n"
    "    There you can set the Distance value.\n"
    "4. Enable Alignment and execute the plugin.\n"
    "5. Start moving the conveyor.\n\n"
    "Documentation on how to use the plugin can be found here:\n"
    "C:\ProgramData\Matrox Imaging\CaptureWorksPlugins\multi_altiz\Documentation"
)

def plugin(function_id):
    mil_function = MIL_ID(function_id)
    routing = MIL_INT(0)

    # read param value
    MfuncParamValue(mil_function, 1, ctypes.byref(routing))

    r = int(routing.value)
    if r == RoutingFunctions.GET_DESCRIPTION:
        get_description(function_id)
    elif r == RoutingFunctions.DIG_IS_SUPPORTED:
        digitizer_is_supported(function_id)
    elif r == RoutingFunctions.ALLOCATE:
        allocate(function_id)
    elif r == RoutingFunctions.FREE:
        free(function_id)
    elif r == RoutingFunctions.GET_UNIQUE_ID:
        get_unique_id(function_id)
    elif r == RoutingFunctions.GET_JSON:
        get_json(function_id)
    elif r == RoutingFunctions.PREPROCESS_FRAME:
        preprocess_frame(function_id)
    elif r == RoutingFunctions.LICENSE_IS_VALID:
        license_is_valid(function_id)
    elif r == RoutingFunctions.SET_VALUE:
        set_value(function_id)
    elif r == RoutingFunctions.GET_VALUE:
        get_value(function_id)
    elif r == RoutingFunctions.GET_IMG_PATH:
        get_image_path(function_id)
    elif r == RoutingFunctions.IS_GRAB_CAPABLE:
        is_grab_capable(function_id)
    elif r == RoutingFunctions.CW_BUTTON_CLICKED:
        dispatch_cw_button_clicked(function_id)



def get_description(function_id):
    """Gets description of plugin"""
    mil_function = MIL_ID(function_id)
    max_size = MIL_INT(0)
    text_out = ctypes.c_char_p(0)

    MfuncParamValue(mil_function, 2, ctypes.byref(max_size))
    MfuncParamValue(mil_function, 3, ctypes.byref(text_out))

    description = plugin_description.encode("utf-8")
    ctypes.memmove(text_out, description, len(description) + 1)


def digitizer_is_supported(function_id):
    mil_function = MIL_ID(function_id)
    dig_id = MIL_ID(0)
    return_value = ctypes.c_void_p(0)

    # read registered values
    MfuncParamValue(mil_function, 2, ctypes.byref(dig_id))
    MfuncParamValue(mil_function, 3, ctypes.byref(return_value))

    this_camera_model = MdigInquireFeature(
        dig_id, M_FEATURE_VALUE, "DeviceModelName", M_TYPE_STRING, None
    )
    this_camera_vendor = MdigInquireFeature(
        dig_id, M_FEATURE_VALUE, "DeviceVendorName", M_TYPE_STRING, None
    )

    dig_is_supported = 0
    if is_camera_supported(this_camera_vendor, this_camera_model):
        dig_is_supported = 1

    return_value_ptr = ctypes.cast(return_value, ctypes.POINTER(ctypes.c_longlong))
    return_value_ptr[0] = dig_is_supported


def allocate(function_id):
    mil_function = MIL_ID(function_id)
    m_dig_id = MIL_ID(0)

    # read values (dig_id, max_size, text_out)
    MfuncParamValue(mil_function, 2, ctypes.byref(m_dig_id))
    dig_id = int(m_dig_id.value)

    camera_user_name = MdigInquire(m_dig_id, M_GC_USER_NAME, None)

    addcamera(dig_id, camera_user_name)
    load_camera_settings(camera_user_name)
    auto_detect_camera_topology(camera_user_name)
    program_cameras(gData.main_camera)

    return

def free(function_id):
    mil_function = MIL_ID(function_id)
    m_dig_id = MIL_ID(0)
    MfuncParamValue(mil_function, 2, ctypes.byref(m_dig_id))
    camera_user_name = MdigInquire(m_dig_id, M_GC_USER_NAME, None)
    if camera_user_name in gData.cameras:
        gData.cameras[camera_user_name].sys_id = 0
        gData.cameras[camera_user_name].dig_id = 0
        gData.cameras[camera_user_name].pdata["Status"] = STRING_NOT_ALLOCATED
        gData.cameras[camera_user_name].pdata["Index"] = 0
        gData.cameras[camera_user_name].topology_in = ""
        gData.cameras[camera_user_name].topology_out = ""
        gData.cameras[camera_user_name].mil_grab_container.clear()

    auto_detect_camera_topology(camera_user_name)
    return get_updated_json(camera_user_name)

def addcamera(dig_id, camera_user_name):
    global gData

    if (dig_id == 0) and (camera_user_name in gData.cameras):
        return

    gData.cameras[camera_user_name] = CWCameraData(dig_id)

def get_unique_id(function_id):
    mil_function = MIL_ID(function_id)
    dig_id = MIL_ID(0)
    max_size = MIL_INT(0)
    text_out = ctypes.c_char_p(0)

    # read values (dig_id, max_size, text_out)
    MfuncParamValue(mil_function, 2, ctypes.byref(dig_id))
    MfuncParamValue(mil_function, 3, ctypes.byref(max_size))
    MfuncParamValue(mil_function, 4, ctypes.byref(text_out))

    camera_user_name = MdigInquire(dig_id, M_GC_USER_NAME, None)
    dig_num = int(dig_id.value)

    unique_id = ("Multi AltiZ Plugin{" + str(dig_num) + "}").encode("utf-8")
    ctypes.memmove(text_out, unique_id, len(unique_id) + 1)

def license_is_valid(function_id):
    """Checks if MIL licenses required to run the plugin are valid"""
    mil_function = MIL_ID(function_id)
    dig_id = MIL_ID(0)
    text_out = ctypes.c_char_p(0)

    # read registered values
    MfuncParamValue(mil_function, 2, ctypes.byref(text_out))

    # check license(s):
    licenses = MappInquire(M_DEFAULT, M_LICENSE_MODULES, None)
    valid_mil_lite = (licenses & M_LICENSE_LITE) != 0
    valid_mil_im = (licenses & M_LICENSE_IM) != 0
    returned_str = ""

    if valid_mil_lite and valid_mil_im:
        returned_str = "valid".encode("utf-8")
    else:
        returned_str = "License check failed. This plugins requires the following: Image Processing module license".encode(
            "utf-8"
        )

    ctypes.memmove(text_out, returned_str, len(returned_str) + 1)


def set_value(function_id):
    mil_function = MIL_ID(function_id)
    m_dig_id = MIL_ID(0)
    text = ctypes.c_char_p(0)
    text_out = ctypes.c_char_p(0)

    MfuncParamValue(mil_function, 2, ctypes.byref(m_dig_id))
    MfuncParamValue(mil_function, 3, ctypes.byref(text))
    MfuncParamValue(mil_function, 4, ctypes.byref(text_out))
    json_return_str = ""

    dig_id = int(m_dig_id.value)
    camera_user_name = MdigInquire(m_dig_id, M_GC_USER_NAME, None)

    p_text = text.value.decode("utf-8")
    values = p_text.split(":")
    param = values[1]
    value = values[2]

    do_program_cameras = True

    if param == "SecondaryCameras":
        gData.selected_camera = value
        do_program_cameras = False
        json_return_str = get_updated_json(value)
    elif (
        param == "TranslationX"
        or param == "TranslationY"
        or param == "TranslationZ"
        or param == "RotationX"
        or param == "RotationY"
        or param == "RotationZ"
    ):
        sel = gData.selected_camera
        gData.cameras[sel].pdata[param] = float(value)
        do_program_cameras = True
    elif param == "RefreshCameras":
        do_program_cameras = True
    elif param == "SaveCameraSettings":
        do_program_cameras = False
        if value == 'True':
            gData.autosave = True
        else:
            gData.autosave = False
    elif param == "ViewMode":
        do_program_cameras = False
        if value == 'AllCameras':
            gData.display_all_cameras = True
        else:
            gData.display_all_cameras = False
    elif param == "AutoDetectTopology":
        sel = gData.selected_camera
        auto_detect_camera_topology(camera_user_name)
        do_program_cameras = True
    elif param == "SetupLaserMultiplexing":
        set_laser_multiplexing(value)
        do_program_cameras = True
    elif param == "ExposureDelay":
        sel = gData.selected_camera
        gData.cameras[sel].pdata["LaserDelayCustom"] = int(value)
        do_program_cameras = True
    elif param == "Operation":
        if value == 'True':
            gData.do_alignment = True
            gData.color = True
        else:
            gData.do_alignment = False
        do_program_cameras = True
    elif param == "ColorData":
        if value == 'True':
            gData.color = True
        else:
            gData.color = False
        do_program_cameras = True
    elif param == "Distance":
        gData.distanceX = float(value)
        gData.selected_camera = camera_user_name
        gData.cameras[camera_user_name].pdata["Distance"] = float(value)
        do_program_cameras = True
    else:
        # do not reprogram if changing a selector or any of the secondary cameras.
        selectorcount = MdigInquireFeature(
            m_dig_id, M_SUBFEATURE_COUNT, param, M_TYPE_INT64, None)
        if selectorcount > 0:
            do_program_cameras = False
        elif camera_user_name != gData.main_camera:
            do_program_cameras = False

    if do_program_cameras == True:
        gData.do_reprogram = True
        auto_detect_camera_topology(camera_user_name)
        program_cameras(gData.main_camera)
        if param == "RefreshCameras":
            save_camera_settings_in_camera(gData.main_camera)
        json_return_str = get_updated_json(gData.selected_camera)

    ctypes.memmove(text_out, json_return_str, len(json_return_str) + 1)
    return


def get_value(function_id):
    mil_function = MIL_ID(function_id)
    m_dig_id = MIL_ID(0)
    p_feature_name = ctypes.c_char_p(0)
    text_out = ctypes.c_char_p(0)
    ret_str = ""  # returned string data

    MfuncParamValue(mil_function, 2, ctypes.byref(m_dig_id))
    MfuncParamValue(mil_function, 3, ctypes.byref(p_feature_name))
    MfuncParamValue(mil_function, 4, ctypes.byref(text_out))

    dig_id = int(m_dig_id.value)
    feat_name = p_feature_name.value.decode("utf-8")
    # check data in requested feature_name:

    ctypes.memmove(text_out, ret_str, len(ret_str) + 1)
    return


def get_image_path(function_id):
    """Gets image path for plugin description"""
    mil_function = MIL_ID(function_id)
    max_size = MIL_INT(0)
    text_out = ctypes.c_char_p(0)

    MfuncParamValue(mil_function, 2, ctypes.byref(max_size))
    MfuncParamValue(mil_function, 3, ctypes.byref(text_out))

    img_folder = os.path.dirname(os.path.realpath(__file__))
    full_path = (os.path.join(img_folder, plugin_image)).encode("utf-8")
    ctypes.memmove(text_out, full_path, len(full_path) + 1)


def is_grab_capable(function_id):
    mil_function = MIL_ID(function_id)
    dig_id = MIL_ID(0)
    return_value = ctypes.c_void_p(0)

    # read registered values
    MfuncParamValue(mil_function, 2, ctypes.byref(dig_id))
    MfuncParamValue(mil_function, 3, ctypes.byref(return_value))

    grab_capable = 1

    return_value_ptr = ctypes.cast(return_value, ctypes.POINTER(ctypes.c_longlong))
    return_value_ptr[0] = grab_capable


def dispatch_cw_button_clicked(function_id):
    mil_function = MIL_ID(function_id)
    dig_id = MIL_ID(0)
    text_out = ctypes.c_char_p(0)
    event = MIL_INT(0)

    MfuncParamValue(mil_function, 2, ctypes.byref(dig_id))
    MfuncParamValue(mil_function, 3, ctypes.byref(text_out))
    MfuncParamValue(mil_function, 4, ctypes.byref(event))

    camera_user_name = MdigInquire(dig_id, M_GC_USER_NAME, None)

    ev = int(event.value)

    # route event type:
    if ev == ButtonEvent.SINGLE_GRAB:
            on_cw_single_grab_clicked(dig_id, camera_user_name)
            gData.grabbing = True
    # elif ev == ButtonEvent.START_CONTINUOUS_GRAB:
    #    on_cw_continuous_grab_clicked(mil_function)
    # elif ev == ButtonEvent.STOP_CONTINUOUS_GRAB:
    #    on_cw_stop_continuous_grab_clicked(mil_function)
    elif ev == ButtonEvent.GRAB_ABORT:
        abort_grabs_on_secondary()
        gData.grabbing = False
    # elif ev == ButtonEvent.FILE_ACCESS_DOWNLOAD:
    #    on_cw_file_access(mil_function)
    # elif ev == ButtonEvent.FILE_ACCESS_UPLOAD:
    #    on_cw_file_access(mil_function)
    json_return_str = get_updated_json(camera_user_name)

    ctypes.memmove(text_out, json_return_str, len(json_return_str) + 1)


def is_camera_supported(vendor, model):

    if (vendor == "Matrox" or vendor == "Zebra") and (model == "AltiZ" or model == "AltiZ 4200"):
        return True

    return False


def get_json(function_id):
    mil_function = MIL_ID(function_id)
    json_max_size = MIL_INT(0)
    json_out = ctypes.c_char_p(0)
    json_path = ctypes.c_char_p(0)
    list_ids = ctypes.c_char_p(0)
    mil_dig_id = MIL_ID(0)

    MfuncParamValue(mil_function, 2, ctypes.byref(json_max_size))
    MfuncParamValue(mil_function, 3, ctypes.byref(json_out))
    MfuncParamValue(mil_function, 4, ctypes.byref(json_path))
    MfuncParamValue(mil_function, 5, ctypes.byref(mil_dig_id))
    MfuncParamValue(mil_function, 6, ctypes.byref(list_ids))

    this_camera_name = MdigInquire(mil_dig_id, M_GC_USER_NAME, None)

    # convert json to dict
    final_path = json_path.value.decode("utf-8")

    updated_node_values = get_nodes_dict(this_camera_name)
    with open(final_path) as json_file:
        data = json.load(json_file)

        for p in data["Data"]:
            data["Data"][p]["Nodes"]["MainCamera"]["Value"] = gData.main_camera

            # update camera camera selector with camera names
            idx = 1
            for cam in gData.cameras:
                current_node = "EnumEntrySecondaryCamera_{}".format(idx)
                data["Data"][p]["Nodes"][current_node]["DisplayName"] = cam
                data["Data"][p]["Nodes"][current_node]["Value"] = cam
                data["Data"][p]["Nodes"][current_node]["AccessMode"] = "ReadWrite"
                idx += 1

        # update initial values
        data["Data"][p]["Nodes"]["SecondaryCameras"]["Value"] = this_camera_name
        gData.selected_camera = this_camera_name
        updated_node_values = get_nodes_dict(this_camera_name)
        if updated_node_values != "":
            for key in updated_node_values.keys():
                for key2, value2 in updated_node_values[key].items():
                    data["Data"][p]["Nodes"][key][key2] = value2

    # convert dict to json
    d = json.dumps(data).encode("utf-8")
    ctypes.memmove(json_out, d, len(d) + 1)

# get values to display in feature browser
def get_nodes_dict(camera):

    if camera not in gData.cameras:
        return ""

    if (gData.main_camera == STRING_NOT_DETECTED and gData.cameras[camera].pdata["TotalNumberOfCameras"] != 1):
        return ""

    selectedcam = gData.cameras[camera]
    access_mode = "ReadWrite"
    distance_access_mode = "ReadWrite"
    
    if selectedcam.dig_id == 0:
        access_mode = "NotAvailable"

    laser_mode = "ReadOnly"
    if gData.laser_multiplexing_mode == "Custom" and gData.main_camera != camera:
        laser_mode = "ReadWrite"
        
    if gData.do_alignment == False:
        distance_access_mode = "ReadOnly"
        
    if gData.do_alignment == True:
        align_access_mode = "WriteOnly"
        if gData.grabbing == True:
            align_instruction = "Acquisition..."
        else:
            align_instruction = "Click on single grab then start motion."
    else:
        align_access_mode = "ReadOnly"
        if gData.grabbing == True:
            align_instruction = "Acquisition..."
        else:
            align_instruction = "Automatic alignment is disabled."

    nodes_subdict = {
        "MainCamera": {KEY_VALUE: gData.main_camera},
        # "SaveCameraSettings": {KEY_VALUE: gData.autosave},
        # "DisplayAllData": {KEY_VALUE: gData.display_all_cameras},
        "ColorData": { KEY_VALUE: str(gData.color)},
        "CameraTopologyIndex": {KEY_VALUE: gData.cameras[camera].pdata["Index"]},
        "CameraStatus": {KEY_VALUE: gData.cameras[camera].pdata["Status"]},
        "INSTRUCTION_MESSAGE": { KEY_VALUE: align_instruction},
        "ExposureDelay": {
            KEY_VALUE: gData.cameras[camera].pdata["LaserDelayCustom"],
            KEY_ACCESS_MODE: laser_mode,
        },
        "Distance": {
            KEY_VALUE: gData.cameras[camera].pdata["Distance"],
            KEY_ACCESS_MODE: distance_access_mode,
        },
        "TranslationX": {
            KEY_VALUE: gData.cameras[camera].pdata["TranslationX"],
            KEY_ACCESS_MODE: access_mode,
        },
        "TranslationY": {
            KEY_VALUE: gData.cameras[camera].pdata["TranslationY"],
            KEY_ACCESS_MODE: access_mode,
        },
        "TranslationZ": {
            KEY_VALUE: gData.cameras[camera].pdata["TranslationZ"],
            KEY_ACCESS_MODE: access_mode,
        },
        "RotationX": {
            KEY_VALUE: gData.cameras[camera].pdata["RotationX"],
            KEY_ACCESS_MODE: access_mode,
        },
        "RotationY": {
            KEY_VALUE: gData.cameras[camera].pdata["RotationY"],
            KEY_ACCESS_MODE: access_mode,
        },
        "RotationZ": {
            KEY_VALUE: gData.cameras[camera].pdata["RotationZ"],
            KEY_ACCESS_MODE: access_mode,
        },
    }

    return nodes_subdict

# returns json with updated values in nodes to be displayed in feature-browser
def get_updated_json(camera):

    nodes = get_nodes_dict(camera)

    # keep cameras selector in sync with data
    nodes["SecondaryCameras"] = {KEY_VALUE: camera}

    min_parent_dict = {"Nodes": nodes}
    json_dict = {
        KEY_SERVICE: Service.EVENT_CALLBACK,
        "Capture Works Plugins{99}": min_parent_dict,
    }
    #save_camera_settings_in_camera(camera)
    json_dumps = json.dumps(json_dict).encode("utf-8")
    return json_dumps


def on_cw_single_grab_clicked(m_dig_id, camera_user_name):
    """called upon user clicked Capture Works SINGLE GRAB button
    (before MdigProcess is called)"""

    if gData.do_reprogram == True:
        gData.do_reprogram = False
        if gData.autosave == True:
            save_camera_settings_in_camera(gData.main_camera)

    cam_info_secondaries = {}

    # populate secondary camera list
    if camera_user_name == gData.main_camera:
        for name, cam in gData.cameras.items():
            if cam.dig_id and name != camera_user_name:
                cam_info_secondaries[cam.dig_id] = { "transforms": get_transforms_R_T(name)}
    print("before process_grabs_on_secondary\n\n")
    perform_grabs_on_secondary(cam_info_secondaries)
    print("after process_grabs_on_secondary\n\n")
    

    return

def json_handle_single_grab(dig_id, containers):
    json_dict = {}
    json_dict.update({KEY_SERVICE: Service.SINGLE_GRAB})
    #plugin_name = gData[dig_id].m_plugin_name
    plugin_name = "MultiAltiZPlugin"

    for mil_id in containers:
        container_name = "{} Acquisition".format(plugin_name)
        json_dict.update({"container name": container_name})
        json_dict.update({"container id": mil_id})

    return json.dumps(json_dict).encode('utf-8')

def preprocess_frame(function_id):
    """Plugin processing function
    (called inside CaptureWorks registered MdigProcess processing function"""
    mil_function = MIL_ID(function_id)
    m_dig_id = MIL_ID(0)
    original_container_id = MIL_ID(0)
    text_out = ctypes.c_char_p(0)
    # read registered values
    MfuncParamValue(mil_function, 2, ctypes.byref(m_dig_id))
    MfuncParamValue(mil_function, 3, ctypes.byref(text_out))
    MfuncParamValue(mil_function, 4, ctypes.byref(original_container_id))

    camera_user_name = MdigInquire(m_dig_id, M_GC_USER_NAME, None)
    # cam_info_main must contain ["dig_id"] and  ["container"] and ["transforms"]
    buffNumber = MdigInquire(m_dig_id, M_PROCESS_TOTAL_BUFFER_NUM,)
    if (buffNumber <= 1):
        cam_info_main = {"container": original_container_id, "transforms": get_transforms_R_T(camera_user_name)}
        TransformList= []
        print("before grab_end()\n\n")
        
        TransformList = grab_end(m_dig_id, gData.do_alignment, gData.display_all_cameras, cam_info_main, gData)
        print("ça passe numero seis\n\n")
        if gData.do_alignment == True:
                cmpt = 0
                cmpt = len(TransformList) - 1
                for camera_user_name in gData.cameras.keys():
                    camera_data = gData.cameras[camera_user_name]
                    #camera_data.pdata["Distance"] = gData.distanceX
                    camera_data.pdata["TranslationX"] = round(TransformList[cmpt][0],3)
                    camera_data.pdata["TranslationY"] = round(TransformList[cmpt][1],3)
                    camera_data.pdata["TranslationZ"] = round(TransformList[cmpt][2],3)
                    camera_data.pdata["RotationX"] = round(TransformList[cmpt][3],3)
                    camera_data.pdata["RotationY"] = round(TransformList[cmpt][4],3)
                    camera_data.pdata["RotationZ"] = round(TransformList[cmpt][5],3)
                    update_camera_UserData(camera_user_name)
                    cmpt = cmpt - 1
                #gData.do_alignment = False

                gData.grabbing = False
                json_return_str = get_updated_json(camera_user_name)
                ctypes.memmove(text_out, json_return_str, len(json_return_str) + 1)
        
        else:
            gData.grabbing = False
            json_return_str = get_updated_json(camera_user_name)
            ctypes.memmove(text_out, json_return_str, len(json_return_str) + 1)
        


# txyx, rxyz.
def get_transforms_R_T(camera):
    cam = gData.cameras[camera]
    tx = cam.pdata["TranslationX"]
    ty = cam.pdata["TranslationY"]
    tz = cam.pdata["TranslationZ"]
    rx = cam.pdata["RotationX"]
    ry = cam.pdata["RotationY"]
    rz = cam.pdata["RotationZ"]
    return [rz, ry, rx, tx, ty, tz]

def nodes_invalidate(dict_invalidate):
    """Returns a json string to be used by an Event callback
    in CaptureWorks (Nodes Invalidated)"""
    # child_dict = {key: value}
    # parent_dict = {feature: child_dict}

    nodes_dict = {"Nodes": dict_invalidate}
    # nodes_dict = {"Nodes": parent_dict}
    json_dict = {KEY_SERVICE: Service.EVENT_CALLBACK,
                 "Capture Works Plugins{99}": nodes_dict}
    json_dumps = json.dumps(json_dict).encode('utf-8')
    return json_dumps
