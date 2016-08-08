#GridToVectors.py
#
# Converts a 2-band raster of U and V values to a vector file to serve as the basis
#  for a network dataset to map connectity within the Arctic.

import sys, os
import numpy as np
import arcpy

#Get relative pathnames
scriptDir = os.path.dirname(sys.argv[0])
rootDir = os.path.dirname(scriptDir)
dataDir = os.path.join(rootDir,"Data")
scratchDir = os.path.join(rootDir,"Scratch")

#Arcpy environment settings
arcpy.CheckOutExtension('spatial')
arcpy.env.overwriteOutput = True
arcpy.env.scratchWorkspace = scratchDir
arcpy.env.outputCoordinateSystem = arcpy.SpatialReference(3408)

#Data folder and file (replace DDD with month)
dataFldr = os.path.join(dataDir,'DailyFiles','2012')
dataFile = os.path.join(dataFldr,'icemotion.grid.daily.2012DDD.n.v3.bin')

#Variables
outWorkspace = os.path.join(dataDir,'icemotion.gdb')
netFC = os.path.join(outWorkspace,"Vectors")

#Static vars
lowerleft = arcpy.Point(-4493750,-4493750)
cellSize = 25000
pi = np.pi
srEASE = arcpy.SpatialReference(3408)

##FUNCTIONS##
def BinToArray(binFN,xDim=361,yDim=361,nGrids=3,valSize=np.int16):
    #Conver the bin file to an array
    with open(moFile,'rb') as inFile:
        arr = np.fromfile(inFile,valSize).reshape((xDim,yDim,nGrids))
    return arr

def WriteArray(arrX,outName):
    import arcpy
    if arcpy.Exists(outName): arcpy.Delete_management(outName)
    arcpy.env.scratchWorkspace = os.path.dirname(outName)
    lowerleft = arcpy.Point(-8987500/2,-8987500/2)
    cellSize = 25000
    outRaster = arcpy.NumPyArrayToRaster(arrX,lowerleft,cellSize)
    outRaster.save(outName)

#Create an array for Feb
for day in range(1,366):
    strDay = str(day).zfill(3)
    dayFile = dataFile.replace("DDD",strDay)
    print "Working on file {}".format(dayFile)

    #Update output filenames for current day
    outUVRasterFN = os.path.join(outWorkspace,"IceUV{}".format(strDay))
    outVectorFN = os.path.join(outWorkspace,"IceNet{}".format(strDay))
    
    #Collect initial environment states
    initMask = arcpy.env.mask

    #Convert the raw bin file to an array (NSIDC ice vector data are 361x361x3 arrays)
    with open(dayFile,'rb') as inFile:
        arrDay = np.fromfile(inFile,np.int16).reshape(361,361,3)
    
    #Extract u/v arrays and reshape to 1D data vectors
    uValues = arrDay[:,:,0].reshape(-1).astype(np.float)
    vValues = arrDay[:,:,1].reshape(-1).astype(np.float)

    #Compute magnitudes (via pythagorean theorem)
    mValues = np.sqrt(np.square(uValues) + np.square(vValues))
        
    #Create a mask from the 3rd band
    maskRaster = arcpy.NumPyArrayToRaster(arrDay[:,:,2],lowerleft,25000,25000,0)
    arcpy.env.mask = maskRaster
    
    #Save u/v/magnitude arrays as 3-band raster
    uRaster = arcpy.NumPyArrayToRaster(uValues.reshape(361,361),lowerleft,cellSize,cellSize)
    vRaster = arcpy.NumPyArrayToRaster(vValues.reshape(361,361),lowerleft,cellSize,cellSize)
    mRaster = arcpy.NumPyArrayToRaster(mValues.reshape(361,361),lowerleft,cellSize,cellSize)
    arcpy.CompositeBands_management((uRaster,vRaster,mRaster),outUVRasterFN)
    arcpy.DefineProjection_management(outUVRasterFN,srEASE)

    #Compute the arctan of above to get the angle, in radians
    thetaRadians = np.arctan2(vValues,uValues)

    #Reclassify to flow direction values
    pi8 = math.pi / 8.0
    fdirVals = np.copy(thetaRadians)
    fdirVals[thetaRadians > (7 * pi8)] = 16     #W
    fdirVals[thetaRadians <= (7 * pi8)] = 32    #NW
    fdirVals[thetaRadians <= (5 * pi8)] = 64    #N
    fdirVals[thetaRadians <= (3 * pi8)] = 128   #NE
    fdirVals[thetaRadians <= (1 * pi8)] = 1     #E
    fdirVals[thetaRadians <= (-1 * pi8)] = 2    #SE
    fdirVals[thetaRadians <= (-3 * pi8)] = 4    #S
    fdirVals[thetaRadians <= (-5 * pi8)] = 8    #SW
    fdirVals[thetaRadians <= (-7 * pi8)] = 16   #W

    #Create the flow direction raster
    fdirArr = fdirVals.reshape(361,361).astype(np.int16)
    fdirRaster = arcpy.NumPyArrayToRaster(fdirArr,lowerleft,25000)

    #Create stream raster from magnitudes
    strmArr = mValues.reshape(361,361).astype(np.int16)
    strmRaster = arcpy.NumPyArrayToRaster(strmArr,lowerleft,25000)

    #Create netfeature class
    arcpy.sa.StreamToFeature(strmRaster,fdirRaster,outVectorFN,"FALSE")

    #Reset environments to initial conditions
    arcpy.env.mask = initMask