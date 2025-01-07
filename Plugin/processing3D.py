#!/usr/bin/env python3
# -*- coding: utf-8 -*-
##########################################################################
#
#
#  File name: processing3D.py included by multi_altiz.py
#
#   Synopsis:  This program is used by Matrox Capture Works as a plug-in.
#              It performs Multi-AltiZ configuration, alignment, transforms
#              and merge of all acquisitions into a single point-cloud.
#
#  Copyright © Matrox Electronic Systems Ltd., 1992-YYYY.
#  All Rights Reserved

from mil import *
from auto_align import *

# returns a new container containing a point-cloud of the merge containers
def transform_and_merge_containers(containers, gdata):

    camera_name = next(iter(gdata.cameras))
    cam = gdata.cameras[camera_name]
    print("ça passe numero zero\n\n")
    if gdata.color == True:
        Colors = GetDistinctColors(cam.pdata["TotalNumberOfCameras"])
        #Colors = GetDistinctColors(3)
        print("ça passe numero zero bis\n\n")
    iteration = 0
    for container, transforms_R_T in containers.items():
        alignment_matrice = M3dgeoAlloc(
            M_DEFAULT_HOST, M_TRANSFORMATION_MATRIX, M_DEFAULT
        )
        M3dgeoMatrixSetTransform(
            alignment_matrice,
            M_ROTATION_Y,
            transforms_R_T[1],
            M_DEFAULT,
            M_DEFAULT,
            M_DEFAULT,
            M_DEFAULT
        )
        M3dgeoMatrixSetTransform(
            alignment_matrice,
            M_TRANSLATION,
            transforms_R_T[3],
            transforms_R_T[4],
            transforms_R_T[5],
            M_DEFAULT,
            M_COMPOSE_WITH_CURRENT
        )
        MbufConvert3d(
            container,
            container,
            M_NULL,
            M_DEFAULT,
            M_DEFAULT
        )
        print("ça passe numero UNO\n\n")
        print("Rotation Altiz %d: %.4f \t %.4f \t %.4f \n" % (iteration, transforms_R_T[0], transforms_R_T[1], transforms_R_T[2]))
        print("Translation Altiz %d: %.4f \t %.4f \t %.4f \n\n" % (iteration, transforms_R_T[3], transforms_R_T[4], transforms_R_T[5])) 
        if gdata.color == True:
            ColorCloud(container, M_RGB888(Colors[iteration].R, Colors[iteration].G, Colors[iteration].B));
            print("ça passe numero dos\n\n")
            iteration = iteration + 1
        M3dimMatrixTransform(
            container,
            container,
            alignment_matrice,
            M_DEFAULT
        )
        print("ça passe numero tres\n\n")
        M3dgeoFree(alignment_matrice)

    new_merged_container = merge_point_clouds(list(containers.keys()))
    print("ça passe numero quatro\n\n")
    return new_merged_container


def merge_point_clouds(list_of_containers_to_merge):
    """Merges all point clouds"""

    grid_size = 0.0
    mil_stat_result = M3dimAllocResult(
        M_DEFAULT_HOST, M_STATISTICS_RESULT, M_DEFAULT, None
    )
    M3dimStat(
        M_STAT_CONTEXT_DISTANCE_TO_NEAREST_NEIGHBOR,
        list_of_containers_to_merge[0],
        mil_stat_result,
        M_DEFAULT,
    )

    # Nearest neighbour distances gives a measure of the point cloud density
    grid_size = M3dimGetResult(
        mil_stat_result, M_MIN_DISTANCE_TO_NEAREST_NEIGHBOR, None
    )

    # Use the measured point cloud density as a guide for subsampling
    Merge_subsample_context = M3dimAlloc(
        M_DEFAULT_HOST, M_SUBSAMPLE_CONTEXT, M_DEFAULT, None
    )
    M3dimControl(
        Merge_subsample_context, M_SUBSAMPLE_MODE, M_SUBSAMPLE_DECIMATE
    )
    M3dimControl(
        Merge_subsample_context, M_ORGANIZATION_TYPE, M_ORGANIZED
    )
    M3dimControl(Merge_subsample_context,  M_STEP_SIZE_X, 4)
    M3dimControl(Merge_subsample_context,  M_STEP_SIZE_Y, 4)
    

    # Allocate the point cloud for the final stitched clouds.
    mil_system = MbufInquire(
        list_of_containers_to_merge[0], M_OWNER_SYSTEM, None
    )
    Merged_point_cloud = MbufAllocContainer(
        mil_system, M_PROC + M_DISP, M_DEFAULT, None
    )

    M3dimMerge(
        list_of_containers_to_merge,
        Merged_point_cloud,
        len(list_of_containers_to_merge),
        Merge_subsample_context,
        M_DEFAULT,
    )

    M3dimFree(mil_stat_result)

    return Merged_point_cloud

# #****************************************************************************
# # Color the container.
# #****************************************************************************
# def ColorCloud(MilPointCloud, Col):

#    SizeX = MbufInquireContainer(MilPointCloud, M_COMPONENT_RANGE, M_SIZE_X, M_NULL)
#    SizeY = MbufInquireContainer(MilPointCloud, M_COMPONENT_RANGE, M_SIZE_Y, M_NULL)
#    MilRefelectance = MbufInquireContainer(MilPointCloud, M_COMPONENT_REFLECTANCE, M_COMPONENT_ID, M_NULL);
#    if MilRefelectance:
#       MbufFreeComponent(MilPointCloud, M_COMPONENT_REFLECTANCE, M_DEFAULT);
#    ReflectanceId = MbufAllocComponent(MilPointCloud, 3, SizeX, SizeY, 8 + M_UNSIGNED, M_IMAGE, M_COMPONENT_REFLECTANCE)
#    MbufClear(ReflectanceId, Col)
