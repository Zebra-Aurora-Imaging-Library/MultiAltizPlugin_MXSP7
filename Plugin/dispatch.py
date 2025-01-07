#!/usr/bin/env python3
# -*- coding: utf-8 -*-

def plugin(function_id):
    mil_function = MIL.MIL_ID(function_id)
    routing = MIL.MIL_INT(0)

    # read param value
    MIL.MfuncParamValue(mil_function, 1, ctypes.byref(routing))

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
    elif r == RoutingFunctions.DUMP_SETTINGS:
        dump_plugin_settings(function_id)
    elif r == RoutingFunctions.IS_GRAB_CAPABLE:
        is_grab_capable(function_id)
    elif r == RoutingFunctions.CW_BUTTON_CLICKED:
        dispatch_cw_button_clicked(function_id)
