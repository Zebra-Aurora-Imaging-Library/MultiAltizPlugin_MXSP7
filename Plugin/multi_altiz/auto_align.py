from re import M
import mil as MIL
import math
import sys
import ctypes

#Version 1.0.2(beta)

#***************************************************************************
# Example description.
#***************************************************************************
def PrintHeader():

   print("[EXAMPLE NAME]\n")
   print("MultiAltizAlignment\n\n")
   print("[SYNOPSIS]\n")
   print("This example show how  to automatcly align point cloud aquired by \n")
   print("multiple Altiz using cylinder object.\n")



   print(("[MODULES USED]\n"))
   print(("Modules used: application, system, display,\n"))
   print(("calibration, geometric model finder.\n\n"))

   # Wait for a key to be pressed.
   print(("Press <Enter> to continue.\n\n"))



#-----------------------------------------------------------------------------
# Constants.
#-----------------------------------------------------------------------------

# Number of models. 
NUMBER_OF_MODELS                = 18

# Model radius. 
MODEL_RADIUS                    = 20.0

# Model max number of occurrences. 
MODEL_MAX_OCCURRENCES           = 30

# Smoothness value. 
SMOOTHNESS_VALUE_1              = 90.0

# Sagitta tolerance. 
SAGITTA_TOLERANCE_1             = 50.0

# Minimum scale factor value. 
MIN_SCALE_FACTOR_VALUE_1        = 0.9

# Length segment. 
MODEL_LENGTH                    = 500

MAX_ITERATION = 200
DECIMATION_STEP = 4
DIV_180_PI = 57.295779513082320866997945294156;


class SAxis:
    def __init__(self, X0, Y0, Z0, X1, Y1, Z1):
        self.Vx = X1 - X0
        self.Vy = Y1 - Y0
        self.Vz = Z1 - Z0
        Length = math.sqrt(self.Vx * self.Vx + self.Vy * self.Vy + self.Vz * self.Vz)
        self.Vx /= Length
        self.Vy /= Length
        self.Vz /= Length
        self.X = 0.5 * (X0 + X1)
        self.Y = 0.5 * (Y0 + Y1)
        self.Z = 0.5 * (Z0 + Z1)
        self.Xpos = X0
        self.Ypos = Y0
        self.Zpos = Z0

class Pose:
    def __init__(self, X, Y):
        self.X = X
        self.Y = Y
        
class SBGR32Color:
    def __init__(self, B=0, G=0, R=0, A=0):
        self.B = B
        self.G = G
        self.R = R
        self.A = A


#****************************************************************************
#Use 3D rectangle finder and line fit to get Ry and Tz.
#****************************************************************************
def Fixturing(MilSystem,  MilPointCloud, RotYTransZ):

    MilLinePointClouds = MIL.MbufAllocContainer(MIL.M_DEFAULT_HOST, MIL.M_PROC + MIL.M_DISP, MIL.M_DEFAULT)
    MilFitResult = MIL.M3dmetAllocResult(MIL.M_DEFAULT_HOST, MIL.M_FIT_RESULT, MIL.M_DEFAULT)
    MilLine = MIL.M3dgeoAlloc(MIL.M_DEFAULT_HOST, MIL.M_GEOMETRY, MIL.M_DEFAULT)
    MilStatResult = MIL.M3dimAllocResult(MIL.M_DEFAULT_HOST, MIL.M_STATISTICS_RESULT, MIL.M_DEFAULT);
    Angle=0.0;

    #Must have for 3d model finder.
    if(MIL.MbufInquireContainer(MilPointCloud, MIL.M_COMPONENT_NORMALS_MIL, MIL.M_COMPONENT_ID, MIL.M_NULL) == MIL.M_NULL):
        MIL.M3dimNormals(MIL.M_NORMALS_CONTEXT_ORGANIZED, MilPointCloud, MilPointCloud, MIL.M_DEFAULT)

    ModContext = MIL.M3dmodAlloc(MilSystem, MIL.M_FIND_RECTANGULAR_PLANE_CONTEXT, MIL.M_DEFAULT);
    ModResult = MIL.M3dmodAllocResult(MilSystem, MIL.M_FIND_RECTANGULAR_PLANE_RESULT, MIL.M_DEFAULT);

    MIL.M3dmodDefine(ModContext, MIL.M_ADD, MIL.M_RECTANGLE_RANGE, 10, 10, 400, 400, MIL.M_DEFAULT, MIL.M_DEFAULT, MIL.M_DEFAULT);
    MIL.M3dmodControl(ModContext, 0, MIL.M_NUMBER, MIL.M_ALL);
    #MIL.M3dmodControl(ModContext, 0, MIL.M_ACCEPTANCE, 70);

    MIL.M3dmodPreprocess(ModContext, MIL.M_DEFAULT);
    MIL.M3dmodFind(ModContext, MilPointCloud, ModResult, MIL.M_DEFAULT);

    # Get number of plane found.
    NbPlanes = MIL.M3dmodGetResult(ModResult, MIL.M_DEFAULT, MIL.M_NUMBER+MIL.M_TYPE_MIL_INT)

    if NbPlanes > 0:
        Planes = []
        CentreZ = []
        SizeX = []
        SizeY = []
       
        print("RECTANGLE NUMB:", NbPlanes)
        Header = "Size X (mm)  Size Y (mm) "
        Format = "%6.2f      %6.2f     "
        print(Header)
        print('-' * len(Header))

        for i in range(NbPlanes):
            Planes.append(MIL.M3dgeoAlloc(MilSystem, MIL.M_GEOMETRY, MIL.M_DEFAULT))
            MIL.M3dmodCopyResult(ModResult, i, Planes[i], MIL.M_DEFAULT, MIL.M_PLANE, MIL.M_DEFAULT)
            SelectedPlaneZ = MIL.M3dmodGetResult(ModResult, i, MIL.M_CENTER_Z)
            SizeX.append(MIL.M3dmodGetResult(ModResult, i, MIL.M_SIZE_X, MIL.M_NULL))
            SizeY.append(MIL.M3dmodGetResult(ModResult, i, MIL.M_SIZE_Y, MIL.M_NULL))
                        
            print(Format % (SizeX[i], SizeY[i]))
            CentreZ.append(SelectedPlaneZ)
    
        # Recherche du plan le plus haut de la scène.
        Highest_plan = min(CentreZ)
        IndexHeight = CentreZ.index(Highest_plan)


        print("A plane is fit to the point cloud.\n\n")

        #NormalZ[IndexHeight] = MIL.M3dmodGetResult(ModResult, IndexHeight, MIL.M_NORMAL_Z, MIL.M_NULL);
        
        BoxContext = MIL.M3dgeoAlloc(MilSystem, MIL.M_GEOMETRY, MIL.M_DEFAULT )
        MIL.M3dmodCopyResult(ModResult, IndexHeight, BoxContext, MIL.M_DEFAULT, MIL.M_BOUNDING_BOX, MIL.M_DEFAULT)
        MIL.M3dgeoBox(BoxContext, MIL.M_CENTER_AND_DIMENSION + MIL.M_ORIENTATION_UNCHANGED, MIL.M_UNCHANGED, MIL.M_UNCHANGED, MIL.M_UNCHANGED, MIL.M_UNCHANGED, MIL.M_UNCHANGED, 0.5, MIL.M_DEFAULT)
        MIL.M3dimScale(BoxContext, BoxContext, 2.0, 2.0, 2.0, MIL.M_GEOMETRY_CENTER, MIL.M_DEFAULT, MIL.M_DEFAULT, MIL.M_DEFAULT)
        MIL.M3dimCrop(MilPointCloud, MilPointCloud, BoxContext, MIL.M_NULL, MIL.M_SAME, MIL.M_DEFAULT)
        
        MIL.MbufCopy(MilPointCloud, MilLinePointClouds);
        MIL.MbufConvert3d(MilLinePointClouds, MilLinePointClouds, MIL.M_NULL, MIL.M_DEFAULT, MIL.M_DEFAULT);
        MIL.M3dimRemovePoints(MilLinePointClouds, MilLinePointClouds, MIL.M_INVALID_POINTS_ONLY, MIL.M_DEFAULT);

        RangeID = MIL.MbufInquireContainer(MilLinePointClouds, MIL.M_COMPONENT_RANGE, MIL.M_COMPONENT_ID, MIL.M_NULL);
        YBuf = MIL.MbufChildColor(RangeID, 1, );
        MIL.MbufClear(YBuf, 0.0);
        print("Fit line...\n\n")

        MIL.M3dmetFit(MIL.M_DEFAULT, MilLinePointClouds, MIL.M_LINE, MilFitResult, 1, MIL.M_DEFAULT);
        MIL.M3dmetCopyResult(MilFitResult, MilLine, MIL.M_FITTED_GEOMETRY, MIL.M_DEFAULT);
  
        # Determine Ry.
        Xpos = MIL.M3dmetGetResult(MilFitResult, MIL.M_AXIS_X, MIL.M_NULL);
        Zpos = MIL.M3dmetGetResult(MilFitResult, MIL.M_AXIS_Z, MIL.M_NULL);
        Angle = math.atan(Zpos / Xpos) *DIV_180_PI;
        MIL.M3dimRotate(MilLinePointClouds, MilLinePointClouds, MIL.M_ROTATION_Y, Angle, MIL.M_DEFAULT, MIL.M_DEFAULT, MIL.M_DEFAULT, MIL.M_DEFAULT, MIL.M_DEFAULT, MIL.M_DEFAULT, MIL.M_DEFAULT);
        MIL.M3dimRotate(MilPointCloud, MilPointCloud, MIL.M_ROTATION_Y, Angle, MIL.M_DEFAULT, MIL.M_DEFAULT, MIL.M_DEFAULT, MIL.M_DEFAULT, MIL.M_DEFAULT, MIL.M_DEFAULT, MIL.M_DEFAULT);
        # Determine Tz.
        MIL.M3dmetFit(MIL.M_DEFAULT, MilLinePointClouds, MIL.M_LINE, MilFitResult, 1, MIL.M_DEFAULT)
        MIL.M3dmetCopyResult(MilFitResult, MilLine, MIL.M_FITTED_GEOMETRY, MIL.M_DEFAULT)
        CentreZPlane = MIL.M3dmetGetResult(MilFitResult, MIL.M_CENTER_Z, MIL.M_NULL)
        MIL.M3dimTranslate(MilPointCloud, MilPointCloud, 0, 0, -CentreZPlane, MIL.M_DEFAULT)

        RotYTransZ.append(Angle)
        RotYTransZ.append(-CentreZPlane)
        print("The point cloud is fixtured to the fit plane.\n\n")
        
        MIL.MbufFree(YBuf)
        for i in range(NbPlanes):
            MIL.M3dgeoFree(Planes[i])
        MIL.M3dmodFree(ModResult)
        MIL.M3dmodFree(ModContext)
        MIL.M3dimFree(MilStatResult)
        MIL.M3dmetFree(MilFitResult)
        MIL.M3dgeoFree(BoxContext)
        MIL.M3dgeoFree(MilLine)

        MIL.MbufFree(MilLinePointClouds)

    else:
        MIL.M3dmodFree(ModResult)
        MIL.M3dmodFree(ModContext)
        MIL.M3dimFree(MilStatResult)
        MIL.M3dmetFree(MilFitResult)
        MIL.M3dgeoFree(MilLine)

        MIL.MbufFree(MilLinePointClouds)

    return NbPlanes

#-----------------------------------------------------------------------------
# Create depth map.
#-----------------------------------------------------------------------------
def CreateDepthMap(MilSystem, MilPointCloud):

   # Calculate the size required for the depth map.
   DepthMapSizeX = 0
   DepthMapSizeY = 0
   # Set the pixel size aspect ratio to be unity.
   PixelAspectRatio = 1.0

   MilMapSizeContext = MIL.M3dimAlloc(MilSystem, MIL.M_CALCULATE_MAP_SIZE_CONTEXT, MIL.M_DEFAULT);

   MIL.M3dimControl(MilMapSizeContext, MIL.M_CALCULATE_MODE, MIL.M_ORGANIZED);
   MIL.M3dimControl(MilMapSizeContext, MIL.M_PIXEL_ASPECT_RATIO, PixelAspectRatio);
   DepthMapSizeX, DepthMapSizeY = MIL.M3dimCalculateMapSize(MilMapSizeContext, MilPointCloud, MIL.M_NULL, MIL.M_DEFAULT);
   MilDepthMap = MIL.MbufAlloc2d(MilSystem, DepthMapSizeX, DepthMapSizeY + 5, MIL.M_UNSIGNED + 8, MIL.M_IMAGE | MIL.M_PROC | MIL.M_DISP, );

   # Calibrate the depth map based on the given point cloud.
   MIL.M3dimCalibrateDepthMap(MilPointCloud, MilDepthMap, MIL.M_NULL, MIL.M_NULL, PixelAspectRatio, MIL.M_DEFAULT, MIL.M_DEFAULT);

   # Control the options of the fill gap context to yield better results.
   FillGapsContext = MIL.M3dimAlloc(MilSystem, MIL.M_FILL_GAPS_CONTEXT, MIL.M_DEFAULT);
   MIL.M3dimControl(FillGapsContext, MIL.M_FILL_THRESHOLD_X, 2);
   MIL.M3dimControl(FillGapsContext, MIL.M_FILL_THRESHOLD_Y, 2);
   MIL.M3dimControl(FillGapsContext, MIL.M_INPUT_UNITS, MIL.M_PIXEL);

   # Project the point cloud in a point based mode.
   MIL.M3dimProject(MilPointCloud, MilDepthMap, MIL.M_NULL, MIL.M_POINT_BASED, MIL.M_DEFAULT, MIL.M_DEFAULT, MIL.M_DEFAULT);
   MIL.M3dimFillGaps(FillGapsContext, MilDepthMap, MIL.M_NULL, MIL.M_DEFAULT);

   MIL.M3dimFree(FillGapsContext)
   MIL.M3dimFree(MilMapSizeContext)
   return MilDepthMap;

#-----------------------------------------------------------------------------
# Find circle on  depth map.
#-----------------------------------------------------------------------------
def SimpleCircleSearch( MilSystem, MilDisplay, GraphicList, MilDepthMap):

   PositionDrawColor = MIL.M_COLOR_RED;  # Position symbol draw color. 
   ModelDrawColor = MIL.M_COLOR_GREEN;   # Model draw color.           
   BoxDrawColor = MIL.M_COLOR_BLUE;      # Model box draw color.       
       
   NumResults = 0;                   # Number of results found.      
   Time = 0.0;                       # Bench variable.             

   # Allocate a circle finder context. 
   MilSearchContext = MIL.MmodAlloc(MilSystem, MIL.M_SHAPE_CIRCLE, MIL.M_DEFAULT );

   # Allocate a circle finder result buffer. 
   MilResult = MIL.MmodAllocResult(MilSystem, MIL.M_SHAPE_CIRCLE );

   # Define the model. 
   MIL.MmodDefine(MilSearchContext, MIL.M_CIRCLE, MIL.M_DEFAULT, MODEL_RADIUS,
      MIL.M_DEFAULT, MIL.M_DEFAULT, MIL.M_DEFAULT);

   # Increase the detail level and smoothness for the edge extraction in the search context. 
   MIL.MmodControl(MilSearchContext, MIL.M_CONTEXT, MIL.M_DETAIL_LEVEL, MIL.M_VERY_HIGH);
   MIL.MmodControl(MilSearchContext, MIL.M_CONTEXT, MIL.M_SMOOTHNESS, SMOOTHNESS_VALUE_1);
   MIL.MmodControl(MilSearchContext, MIL.M_ALL, MIL.M_ACCEPTANCE, 70.0);
   MIL.MmodControl(MilSearchContext, MIL.M_ALL, MIL.M_SAGITTA_TOLERANCE, SAGITTA_TOLERANCE_1);

   # Enable large search scale range
   #MIL.MmodControl(MilSearchContext, 0, MIL.M_SCALE_MIN_FACTOR, MIN_SCALE_FACTOR_VALUE_1);
   MIL.MmodControl(MilResult, MIL.M_GENERAL, MIL.M_RESULT_OUTPUT_UNITS, MIL.M_WORLD);
   MIL.MmodControl(MilSearchContext, 0, MIL.M_NUMBER, NUMBER_OF_MODELS);

   # Preprocess the search context. 
   MIL.MmodPreprocess(MilSearchContext, MIL.M_DEFAULT);

   # Find the model. 
   MIL.MmodFind(MilSearchContext, MilDepthMap, MilResult);

   # Get the number of models found. 
   NumResults = MIL.MmodGetResult(MilResult, MIL.M_DEFAULT, MIL.M_NUMBER + MIL.M_TYPE_MIL_INT);
   print("number result in circle finder \n")
   print(NumResults)
   print("\n")
   # If a model was found above the acceptance threshold. 
   if ((NumResults >= 1) and (NumResults <= MODEL_MAX_OCCURRENCES)):
   
      # Get the results of the circle search. 
      XPosition = MIL.MmodGetResult(MilResult, MIL.M_DEFAULT, MIL.M_POSITION_X)
      YPosition = MIL.MmodGetResult(MilResult, MIL.M_DEFAULT, MIL.M_POSITION_Y)
      Radius = MIL.MmodGetResult(MilResult, MIL.M_DEFAULT, MIL.M_RADIUS)
      Score = MIL.MmodGetResult(MilResult, MIL.M_DEFAULT, MIL.M_SCORE)
      for i in range(NumResults):
        print("%-9d%-13.2f%-13.2f%-8.2f%-5.2f%%\n" % (i, XPosition[i], YPosition[i], Radius[i], Score[i]))
      #Free search context.
      MIL.MmodFree(MilSearchContext)
      
   else:
        MIL.MmodFree(MilSearchContext)
        
    
   return MilResult

#-----------------------------------------------------------------------------
# Find segment on  depth map.
#-----------------------------------------------------------------------------
def SegmentSearch(MilSystem, MilDisplay, GraphicList, MilDepthMap):          
      
    NumResults = 0;                   # Number of results found.      
    Time = 0.0;                       # Bench variable.             

    # Allocate a segment finder context. 
    MilSearchContextSegment = MIL.MmodAlloc(MilSystem, MIL.M_SHAPE_SEGMENT, MIL.M_DEFAULT );

    # Allocate a segment finder result buffer. 
    MilResultSegment = MIL.MmodAllocResult(MilSystem, MIL.M_SHAPE_SEGMENT );                

    # Define the model. 
    MIL.MmodDefine(MilSearchContextSegment, MIL.M_SEGMENT, MODEL_LENGTH, MIL.M_DEFAULT,
        MIL.M_DEFAULT, MIL.M_DEFAULT, MIL.M_DEFAULT);

    #Context control.
    MIL.MmodControl(MilSearchContextSegment, MIL.M_CONTEXT, MIL.M_SMOOTHNESS, 90.0);
    MIL.MmodControl(MilSearchContextSegment, MIL.M_ALL, MIL.M_ACCEPTANCE, 70.0);
    MIL.MmodControl(MilSearchContextSegment, MIL.M_ALL, MIL.M_SCALE_MAX_FACTOR, 5);
    MIL.MmodControl(MilSearchContextSegment, MIL.M_ALL, MIL.M_SCALE_MIN_FACTOR, 0.1);
    MIL.MmodControl(MilSearchContextSegment, 0, MIL.M_NUMBER, NUMBER_OF_MODELS);

    MIL.MmodControl(MilResultSegment, MIL.M_GENERAL, MIL.M_RESULT_OUTPUT_UNITS, MIL.M_WORLD);

    #Preprocess the search context. 
    MIL.MmodPreprocess(MilSearchContextSegment, MIL.M_DEFAULT);
    #Reset the timer. 
    MIL.MappTimer(MIL.M_DEFAULT, MIL.M_TIMER_RESET + MIL.M_SYNCHRONOUS, MIL.M_NULL);
    #Find the model. 
    MIL.MmodFind(MilSearchContextSegment, MilDepthMap, MilResultSegment);
    #Read the find time.
    Time = MIL.MappTimer(MIL.M_DEFAULT, MIL.M_TIMER_READ + MIL.M_SYNCHRONOUS);

    #Get the number of models found.
    NumResults = MIL.MmodGetResult(MilResultSegment, MIL.M_DEFAULT, MIL.M_NUMBER + MIL.M_TYPE_MIL_INT);

    # If a model was found above the acceptance threshold. 
    if ((NumResults >= 1) and (NumResults <= MODEL_MAX_OCCURRENCES)):
    
        #Get the results of the SEGMENT search. 
        Score = MIL.MmodGetResult(MilResultSegment, MIL.M_DEFAULT, MIL.M_SCORE);
        Length = MIL.MmodGetResult(MilResultSegment, MIL.M_DEFAULT, MIL.M_LENGTH);

        ##Draw edges, position and box over the occurrences that were found.
        MIL.MgraControl(MIL.M_DEFAULT, MIL.M_COLOR, MIL.M_COLOR_RED);
        MIL.MmodDraw(MIL.M_DEFAULT, MilResultSegment, MilDepthMap, MIL.M_DRAW_POSITION, MIL.M_DEFAULT, MIL.M_DEFAULT);
        MIL.MgraControl(MIL.M_DEFAULT, MIL.M_COLOR, MIL.M_COLOR_GREEN);
        MIL.MmodDraw(MIL.M_DEFAULT, MilResultSegment, MilDepthMap, MIL.M_DRAW_EDGES, MIL.M_DEFAULT, MIL.M_DEFAULT);

    else:
        print("The model was not found or the number of models ")
        print("found is greater than\n")
        print("the specified maximum number of occurrences!\n\n")
        MIL.MmodFree(MilSearchContextSegment)
    return MilResultSegment


#****************************************************************************
# Get the displacement axis according to the edge of the alignment tool.
#****************************************************************************
def GetAxisFromSegment(MilDepthMap, MilResult):

    NumResults = 0                # Number of results found.      

    #Get the results of the Segment search. 
    EndXPos = MIL.MmodGetResult(MilResult, MIL.M_DEFAULT, MIL.M_END_POS_X)
    EndYPos = MIL.MmodGetResult(MilResult, MIL.M_DEFAULT, MIL.M_END_POS_Y)
    CenterXPosition = MIL.MmodGetResult(MilResult, MIL.M_DEFAULT, MIL.M_CENTER_X)
    CenterYPosition = MIL.MmodGetResult(MilResult, MIL.M_DEFAULT, MIL.M_CENTER_Y)
    NumResults = MIL.MmodGetResult(MilResult, MIL.M_DEFAULT, MIL.M_NUMBER + MIL.M_TYPE_MIL_INT)
    maxIndex = 0;
    if (NumResults >= 2):
        Valid_index =  findValidIndexSimple(EndXPos, CenterXPosition, NumResults);
        maxCenterY = CenterYPosition[Valid_index[0]];
        for i in range(len(Valid_index)):    
            if (CenterYPosition[Valid_index[i]] >= maxCenterY):
                maxCenterY = CenterYPosition[Valid_index[i]];
                maxIndex = Valid_index[i]  
    else:
        maxIndex = 0

    OriginX = []
    OriginY = []
    OriginZ = [0.0]
    EndX = []
    EndY = []
    EndZ = [0.0]

    #Get the index of the greatest score value. 
   
    OriginX.append(float(EndXPos[maxIndex] ));
    OriginY.append(float(EndYPos[maxIndex] ));
    #MIL.McalTransformCoordinate3dList(MilDepthMap, MIL.M_PIXEL_COORDINATE_SYSTEM, MIL.M_RELATIVE_COORDINATE_SYSTEM, 1, OriginX, OriginY, MIL.M_NULL, OriginX, OriginY, OriginZ, MIL.M_DEPTH_MAP);
    
    #Get the index of the smallest score value. 
    EndX.append(float(CenterXPosition[maxIndex] ));
    EndY.append(float(CenterYPosition[maxIndex] ));
    #MIL.McalTransformCoordinate3dList(MilDepthMap, MIL.M_PIXEL_COORDINATE_SYSTEM, MIL.M_RELATIVE_COORDINATE_SYSTEM, 1, EndX, EndY, MIL.M_NULL, EndX, EndY, EndZ, MIL.M_DEPTH_MAP);

    print("X position\t Origin: |%.4f| \tEnd |%.4f| \n" % (OriginX[0], EndX[0]))
    print("Y position\t Origin: |%.4f| \tEnd |%.4f| \n" % (OriginY[0], EndY[0]))
    print("Z position\t Origin: |%.4f| \tEnd |%.4f| \n\n" % (OriginZ[0], EndZ[0]))

    return SAxis( OriginX[0], OriginY[0], OriginZ[0], EndX[0], EndY[0], EndZ[0] )

#-----------------------------------------------------------------------------
# Get alignement matrix relative to first camera.
#-----------------------------------------------------------------------------
def GetMatrixTransform(MilMatrix, SegmentVector, CircleVectorRef, CircleVectorAlign, DistanceX):

    TxCircle = CircleVectorRef.X - CircleVectorAlign.X;
    TyCircle = CircleVectorRef.Y - CircleVectorAlign.Y;
    #MilTransformationMatrix = MIL.M3dgeoAlloc(MIL.M_DEFAULT_HOST, MIL.M_TRANSFORMATION_MATRIX, MIL.M_DEFAULT)

    MIL.M3dgeoMatrixSetTransform(MilMatrix, MIL.M_TRANSLATION, TxCircle, TyCircle, 0, MIL.M_DEFAULT, MIL.M_ASSIGN)
    MIL.M3dgeoMatrixSetTransform(MilMatrix, MIL.M_TRANSLATION, DistanceX * SegmentVector.Vx, DistanceX * SegmentVector.Vy,
                            0, MIL.M_DEFAULT, MIL.M_COMPOSE_WITH_CURRENT);


#-----------------------------------------------------------------------------
#Get index of correct segment when more than 1 is found with model finder.
#-----------------------------------------------------------------------------
def findValidIndexSimple(XPosition, CenterXPosition, NumResults):

    validIndex = []
    Vx = 0.0
    for i in range(NumResults):
        Vx = CenterXPosition[i] - XPosition[i]
        if abs(Vx) > 15:
            validIndex.append(i)

    return validIndex


# Get index of correct pair of holes if more than 2 holes are found with model finder.
#(Non altern).  
def findValidIndex(XPosition, NumResults, camNum):

   maxFirst = -math.inf
   maxSecond = -math.inf
   minFirst = math.inf
   minSecond = math.inf
   index1 = -1
   index2 = -1
   #If scan is from camera number 2 get pairs with greater Xpos.
   if (camNum == 2):
   
      for i in range(NumResults):      
         if (XPosition[i] > maxFirst):         
            maxSecond = maxFirst;
            index2 = index1;
            maxFirst = XPosition[i];
            index1 = i;        
         elif (XPosition[i] > maxSecond):
         
            maxSecond = XPosition[i];
            index2 = i;
   
   else:
   
      for j in range(NumResults):      
         if (XPosition[j] < minFirst):         
            minSecond = minFirst
            index2 = index1
            minFirst = XPosition[j]
            index1 = j         
         elif (XPosition[j] < minSecond):
         
            minSecond = XPosition[j]
            index2 = j
         
      
   
   validIndex = []
   validIndex.append(index1)
   validIndex.append(index2)

   return validIndex

def findMinRadiusIndex(Radius, NumResults):
   #if size = 0 means whole array has been traversed
   if (NumResults == 1):
      return 0
   else:
      MinIndex = 0
      MinVal = Radius[0]
      for i in range(1, len(Radius)):
            if (Radius[i] < MinVal):         
               MinIndex = i

      return MinIndex;
   

def findMaxRadiusIndex(Radius, NumResults):
   #if size = 0 means whole array has been traversed
   if (NumResults == 1):
      return 0
   else:
      MaxIndex = 0
      MaxVal = Radius[0]
      for i in range(1, len(Radius)):      
         if (Radius[i] > MaxVal):
         
            MaxIndex = i

      return MaxIndex;


#-----------------------------------------------------------------------------/
# Main.
#-----------------------------------------------------------------------------/

def MultiAltizExample(containers_to_merge, gdata):

    # Print example description. 
    PrintHeader();
            
    NumOccurences = 0             ## Number of results found.    
    RotYTransZ = []
    MilToAlignPointClouds =[]
    #List to store transformation matrices.
    AxisDirections = []
    AxisCircles = []

    # Allocate objects. 
    MilSystem = MIL.MbufInquireContainer(containers_to_merge[0], MIL. M_CONTAINER, MIL.M_OWNER_SYSTEM, None)
    MilDisplay = MIL.MdispAlloc(MilSystem, MIL.M_DEFAULT, MIL.MIL_TEXT("M_DEFAULT"), MIL.M_WINDOWED,)
    GraphicList = MIL.MgraAllocList(MilSystem, MIL.M_DEFAULT,);
    # Create list of point cloud in reverse because grabEnd() return the last scan first. 
    MilToAlignPointClouds = containers_to_merge[::-1]
    # MIL.MbufSave(MIL.MIL_TEXT("ScanAltiz1.mbufc"),containers_to_merge[0])
    # MIL.MbufSave(MIL.MIL_TEXT("ScanAltiz2.mbufc"),containers_to_merge[1])
    # MIL.MbufSave(MIL.MIL_TEXT("ScanAltiz3.mbufc"),containers_to_merge[2])
    for i in range(len(MilToAlignPointClouds)):
        MIL.MbufConvert3d(MilToAlignPointClouds[i], MilToAlignPointClouds[i], MIL.M_NULL, MIL.M_DEFAULT, MIL.M_DEFAULT);
    
    MilCopyPointCloud = MIL.MbufAllocContainer(MilSystem, MIL.M_PROC + MIL.M_DISP, MIL.M_DEFAULT)

    #Control 2d display settings.
    MIL.MdispControl(MilDisplay, MIL.M_WINDOW_INITIAL_POSITION_X, 800);
    RefCircleXPos = 0.0;
    RefCircleYPos = 0.0;
    for i in range(len(MilToAlignPointClouds)):  
      
        #MilGraphicList = MIL.M_NULL

        MIL.MbufCopy(MilToAlignPointClouds[i], MilCopyPointCloud);
        NumOccurences = Fixturing(MilSystem, MilCopyPointCloud, RotYTransZ)
        
        if NumOccurences < 1:
            MIL.MbufFree(MilCopyPointCloud)
            MIL.MgraFree(GraphicList)
            MIL.MdispFree(MilDisplay)
            sys.exit("No plane was found.\n") 

        #Create depth map for primary scan.
        MilDepthMap = CreateDepthMap(MilSystem, MilCopyPointCloud)

        #Run modelfinder to find circle shape
        MilModResultCircle = SimpleCircleSearch(MilSystem, MilDisplay, GraphicList, MilDepthMap)
        NumOccurences = MIL.MmodGetResult(MilModResultCircle, MIL.M_DEFAULT, MIL.M_NUMBER + MIL.M_TYPE_MIL_INT)
        if NumOccurences < 1:
            MIL.MmodFree(MilModResultCircle)
            MIL.MbufFree(MilDepthMap)
            MIL.MbufFree(MilCopyPointCloud)
            MIL.MgraFree(GraphicList)
            MIL.MdispFree(MilDisplay)
            sys.exit("Not enough circle was found to continue.\n") 

        #Run modelfinder to find circle shape
        MilModResultSegment = SegmentSearch(MilSystem, MilDisplay, GraphicList, MilDepthMap)
        NumOccurences = MIL.MmodGetResult(MilModResultSegment, MIL.M_DEFAULT, MIL.M_NUMBER + MIL.M_TYPE_MIL_INT)
        if NumOccurences < 1:
            MIL.MmodFree(MilModResultSegment)
            MIL.MmodFree(MilModResultCircle)
            MIL.MbufFree(MilDepthMap)
            MIL.MbufFree(MilCopyPointCloud)
            MIL.MgraFree(GraphicList)
            MIL.MdispFree(MilDisplay)
            sys.exit("No segment were found.\n") 
        CircleXPos = MIL.MmodGetResult(MilModResultCircle, 0, MIL.M_POSITION_X,None);
        CircleYPos = MIL.MmodGetResult(MilModResultCircle, 0, MIL.M_POSITION_Y,None);
        CirclePose = Pose(CircleXPos, CircleYPos)

        AxisVectorSegment = GetAxisFromSegment(MilDepthMap, MilModResultSegment)
        AxisDirections.append(AxisVectorSegment)
        AxisCircles.append(CirclePose)
    
    MilTransformMatrix = [MIL.MIL_ID for _ in range(len(MilToAlignPointClouds))]   
    TransformList = [[0.0] * 6 for _ in range(len(MilToAlignPointClouds))]
    for i in range(len(MilToAlignPointClouds)): 
        MilTransformMatrix[i] = MIL.M3dgeoAlloc(MIL.M_DEFAULT_HOST, MIL.M_TRANSFORMATION_MATRIX, MIL.M_DEFAULT)
        GetMatrixTransform(MilTransformMatrix[i], AxisDirections[i], AxisCircles[0], AxisCircles[i], i * gdata.distanceX);

        Tx, Ty, Tz = MIL.M3dgeoMatrixGetTransform(MilTransformMatrix[i], MIL.M_TRANSLATION, None, None, None, MIL.M_NULL, MIL.M_DEFAULT);
        MIL.M3dgeoMatrixSetTransform(MilTransformMatrix[i], MIL.M_ROTATION_Y, RotYTransZ[2 * i], MIL.M_DEFAULT,MIL.M_DEFAULT,MIL.M_DEFAULT, MIL.M_ASSIGN);
        MIL.M3dgeoMatrixSetTransform(MilTransformMatrix[i], MIL.M_TRANSLATION, Tx, Ty, Tz + RotYTransZ[2 * i + 1], MIL.M_DEFAULT, MIL.M_COMPOSE_WITH_CURRENT);

        # Print transformation matrix coefficients.
        TransformList[i][0], TransformList[i][1], TransformList[i][2] = MIL.M3dgeoMatrixGetTransform(MilTransformMatrix[i], MIL.M_TRANSLATION, None, None, None, MIL.M_NULL, MIL.M_DEFAULT);
        TransformList[i][3], TransformList[i][4], TransformList[i][5] = MIL.M3dgeoMatrixGetTransform(MilTransformMatrix[i], MIL.M_ROTATION_ZYX, None, None, None, MIL.M_NULL, MIL.M_DEFAULT);
        print("Rotation Altiz %d: %.4f \t %.4f \t %.4f \n" % (i, TransformList[i][3], TransformList[i][4], TransformList[i][5]))
        print("Translation Altiz %d: %.4f \t %.4f \t %.4f \n\n" % (i, Tx, Ty, Tz)) 
      
    #Matrices = HomogeneousMatrix(MilMatrix)
    if gdata.color == True:
        Colors = GetDistinctColors(len(MilToAlignPointClouds))
        print("ça passe numero uno\n\n")
    #Transform scans.
    for j in range(len(MilToAlignPointClouds)):
        print("ça passe numero dos\n\n")
        if gdata.color == True:
            ColorCloud(MilToAlignPointClouds[j], MIL.M_RGB888(Colors[j].R, Colors[j].G, Colors[j].B))
            print("ça passe numero tres\n\n")
        MIL.M3dimMatrixTransform(MilToAlignPointClouds[j], MilToAlignPointClouds[j], MilTransformMatrix[j], MIL.M_DEFAULT);

    # Use decimation for subsampling.
    MilSubsampleContext = MIL.M3dimAlloc(MilSystem, MIL.M_SUBSAMPLE_CONTEXT, MIL.M_DEFAULT)
    MIL.M3dimControl(MilSubsampleContext, MIL.M_SUBSAMPLE_MODE, MIL.M_SUBSAMPLE_DECIMATE)
    MIL.M3dimControl(MilSubsampleContext, MIL.M_ORGANIZATION_TYPE, MIL.M_ORGANIZED)
    MIL.M3dimControl(MilSubsampleContext, MIL.M_STEP_SIZE_X, 2)
    MIL.M3dimControl(MilSubsampleContext, MIL.M_STEP_SIZE_Y, 2)

    MilMergedPointClouds = MIL.MbufAllocContainer(MilSystem, MIL.M_PROC + MIL.M_DISP, MIL.M_DEFAULT)
    MIL.M3dimMerge(MilToAlignPointClouds, MilMergedPointClouds, len(MilToAlignPointClouds), MilSubsampleContext, MIL.M_DEFAULT)

    #MIL.M3ddispFree(Mil3dDisplay)
    MIL.M3dimFree(MilSubsampleContext)
    for k in range(len(MilToAlignPointClouds)):
        MIL.M3dgeoFree(MilTransformMatrix[k])
    MIL.MmodFree(MilModResultSegment)
    MIL.MmodFree(MilModResultCircle)
    MIL.MbufFree(MilDepthMap)
    MIL.MbufFree(MilCopyPointCloud)
    MIL.MgraFree(GraphicList)
    MIL.MdispFree(MilDisplay)

    return MilMergedPointClouds, TransformList


#-----------------------------------------------------------------------------
# Allocates a 3D display and returns its MIL identifier.
#-----------------------------------------------------------------------------
def Alloc3dDisplayId(MilSystem):

   MIL.MappControl(MIL.M_DEFAULT, MIL.M_ERROR, MIL.M_PRINT_DISABLE)
   MilDisplay3D = MIL.M3ddispAlloc(MilSystem, MIL.M_DEFAULT, "M_DEFAULT", MIL.M_DEFAULT)
   MIL.MappControl(MIL.M_DEFAULT, MIL.M_ERROR, MIL.M_PRINT_ENABLE)

   if not MilDisplay3D:
      print("\n")
      print("The current system does not support the 3D display.\n")
      print("Press any key to continue.\n")
      #MIL.MosGetch()
   
   return MilDisplay3D;

#****************************************************************************
# Gets a certain number of distinct colors.
#****************************************************************************
def GetDistinctColors(NbColors):
    MilPointCloudColors = MIL.MbufAllocColor(MIL.M_DEFAULT_HOST, 3, NbColors, 1, 8 + MIL.M_UNSIGNED, MIL.M_LUT, )
    MIL.MgenLutFunction(MilPointCloudColors, MIL.M_COLORMAP_DISTINCT_256, MIL.M_DEFAULT, MIL.M_DEFAULT, MIL.M_DEFAULT, MIL.M_DEFAULT, MIL.M_DEFAULT, MIL.M_DEFAULT)

    # Initialize an empty list to hold the color data
    ColorData = (ctypes.c_ubyte * (NbColors * 4))()
    
    # Get all the colors at once
    MIL.MbufGetColor(MilPointCloudColors, MIL.M_PACKED + MIL.M_BGR32, MIL.M_ALL_BANDS, ColorData)
    
    # Convert the color data to a list of SBGR32Color instances
    Colors = []
    for i in range(NbColors):
        b = ColorData[i * 4]
        g = ColorData[i * 4 + 1]
        r = ColorData[i * 4 + 2]
        a = ColorData[i * 4 + 3]
        Colors.append(SBGR32Color(B=b, G=g, R=r, A=a))
    
    return Colors


#****************************************************************************
# Color the container.
#****************************************************************************
def ColorCloud(MilPointCloud, Col):

   SizeX = MIL.MbufInquireContainer(MilPointCloud, MIL.M_COMPONENT_RANGE, MIL.M_SIZE_X, MIL.M_NULL)
   SizeY = MIL.MbufInquireContainer(MilPointCloud, MIL.M_COMPONENT_RANGE, MIL.M_SIZE_Y, MIL.M_NULL)
   MilRefelectance = MIL.MbufInquireContainer(MilPointCloud, MIL.M_COMPONENT_REFLECTANCE, MIL.M_COMPONENT_ID, MIL.M_NULL);
   if MilRefelectance:
      MIL.MbufFreeComponent(MilPointCloud, MIL.M_COMPONENT_REFLECTANCE, MIL.M_DEFAULT);
   ReflectanceId = MIL.MbufAllocComponent(MilPointCloud, 3, SizeX, SizeY, 8 + MIL.M_UNSIGNED, MIL.M_IMAGE, MIL.M_COMPONENT_REFLECTANCE)
   MIL.MbufClear(ReflectanceId, Col)



#--------------------------------------------------------------------------
# Check for required files to run the example.    
#--------------------------------------------------------------------------
def CheckForRequiredMILFile(FileName):
   FilePresent = MIL.M_NO
   MIL.MappFileOperation(MIL.M_DEFAULT, FileName, MIL.M_NULL, MIL.M_NULL, MIL.M_FILE_EXISTS, MIL.M_DEFAULT, FilePresent)
   if FilePresent == MIL.M_NO:
      print("The footage needed to run this example is missing.")
      print("You need to obtain and apply a separate specific update to have it.\n")
      print("Press <Enter> to end.\n\n")
   return (FilePresent == MIL.M_YES)
