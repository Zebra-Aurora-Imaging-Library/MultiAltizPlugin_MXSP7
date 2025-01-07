#!/usr/bin/env python3
# -*- coding: utf-8 -*-
##########################################################################
#
#
#  File name: grab.py included by multi_altiz.py
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
from processing3D import *
from auto_align import *

# globals to keep information on current grab containers and transforms.
g_cam_info_secondaries = {}

# cam_info_secondaries contains:
#  ["container"] for the grab container
#  ["transforms"] is a list of transforoms in this order: [rz, ry, rx, tx, ty, tz]
def perform_grabs_on_secondary(cam_info_secondaries):

    global g_cam_info_secondaries

    for dig_id, data in cam_info_secondaries.items():
        sys_id = MdigInquire(dig_id, M_OWNER_SYSTEM, None)

        container = MbufAllocContainer(
            sys_id, M_GRAB + M_DISP + M_PROC, M_DEFAULT, None)
        if container:
            g_cam_info_secondaries[dig_id] = {"container": container, "transforms" : data["transforms"]}

            containers = [container]
            MdigProcess(dig_id,containers, 1, M_SEQUENCE + M_COUNT(1), M_ASYNCHRONOUS, processing_function_ptr, M_NULL )


# to be called on the MdigProcess callback of the main digitizer.
# cam_info_main contains
# ["container"]
# ["transforms"] in this order [rz, ry, rx, tx, ty, tz]
def grab_end(main_digitizer_id, booleanAlignment, keep_all_data, cam_info_main, gdata):

    containers_to_merge = {}
    main_container_id = cam_info_main["container"]
    print("before loop wait for secondaries\n\n")

    # wait for secondary cameras to complete
    for dig_id, cam_info in g_cam_info_secondaries.items():
        containers = [cam_info["container"]]
        print("before MdigProces in the loop\n\n")
        MdigProcess( dig_id, containers, 1, M_STOP + M_WAIT, M_DEFAULT, processing_function_ptr, M_NULL,)
        print("after Mdigprocess in loop\n\n")
        
        containers_to_merge[cam_info["container"]] = cam_info["transforms"]
    print("after loop\n\n")

    # we want to keep the data of all the grabs, so change their group ID and copy them in the orignal grab container.
    sourceclone0 = MIL_ID(0)
    if keep_all_data == True:
        sourceclone0 = MbufClone(main_container_id, M_DEFAULT, M_DEFAULT, M_DEFAULT, M_DEFAULT, M_DEFAULT, M_COPY_SOURCE_DATA, )
        containers_to_merge[sourceclone0] = cam_info_main["transforms"]

        groupoffset = 10  # offset the GroupID of each grab container so they do not overlap.
        print("before changeGroupeId1\n\n")
        
        change_group_id(sourceclone0, groupoffset)
        print("after change_group_id1\n\n")

        MbufCopyComponent( sourceclone0, main_container_id, M_COMPONENT_ALL, M_REPLACE, M_DEFAULT, )

        for dig_id, cam_info in g_cam_info_secondaries.items():
            groupoffset += 10
            print("before change_group_id2\n\n")
            change_group_id(cam_info["container"], groupoffset)
            print("after change_group_id2\n\n")

            MbufCopyComponent(cam_info["container"], main_container_id, M_COMPONENT_ALL, M_APPEND, M_DEFAULT, )
    else:
        main_container_id_tmp = int(cam_info_main["container"].value)
        containers_to_merge[main_container_id_tmp] = cam_info_main["transforms"]

    TransformList = []

    if booleanAlignment == True:
        #MdigProcess(main_digitizer_id, [main_container_id], 1, M_STOP + M_WAIT, M_DEFAULT, processing_function_ptr, M_NULL, )
        new_merged_container, TransformList= MultiAltizExample(list(containers_to_merge.keys()), gdata)
    else:
        new_merged_container = transform_and_merge_containers(containers_to_merge, gdata)
        print("ça passe numero cinqo\n\n")

    # copy the merged container back into the original container.
    if keep_all_data == True:
        MbufCopyComponent(
            new_merged_container,
            main_container_id,
            M_COMPONENT_ALL,
            M_APPEND,
            M_DEFAULT,
        )
    else:
        MbufCopyComponent(
            new_merged_container,
            main_container_id,
            M_COMPONENT_ALL,
            M_REPLACE,
            M_DEFAULT,
        )

    MbufFree(new_merged_container)
    if sourceclone0:
        MbufFree(sourceclone0)

    free_ressources()
    return TransformList


def free_ressources():

    # free all the grab containers
    for id, cam_info in g_cam_info_secondaries.items():
        buf_id = cam_info["container"]
        MbufFree(buf_id)

    g_cam_info_secondaries.clear()

# to abort the grabs on the secondary digitizers.
def abort_grabs_on_secondary():
    for cam_id, cam_info in g_cam_info_secondaries.items():
        if cam_info["container"]:
            containers = [cam_info["container"]]
            MdigProcess(
                cam_id,
                containers,
                1,
                M_STOP,
                M_DEFAULT,
                processing_function_ptr,
                M_NULL,
            )
    free_ressources()
    return

# offsets the group Id of all the components of the container.
def change_group_id(container, groupoffset):
    components = MbufInquireContainer(container, M_CONTAINER, M_COMPONENT_LIST, None)
    a = list(components)
    for component in a:
        groupid = MbufInquire(component, M_COMPONENT_GROUP_ID, )
        b = int(component)
        MbufControl(b, M_COMPONENT_GROUP_ID, groupid + groupoffset)


def grab_hook(hook_type, hook_id, hook_data_ptr):
    return 0

processing_function_ptr = MIL_DIG_HOOK_FUNCTION_PTR(grab_hook)
