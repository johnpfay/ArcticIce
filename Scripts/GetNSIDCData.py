#GetNSIDCData.py
#
# Downloads the NSIDC Ice Vector binary files for processing.
# Data are stored on the National Sea Ice Data Center (NSIDC) ftp servers as
# monthly means or as daily data ice motion data
#
# Aug 2015
# John.Fay@duke.edu

import sys, os, urllib, arcpy
import numpy as np

#Get folders
scriptFldr = os.path.dirname(sys.argv[0])
rootFldr = os.path.dirname(scriptFldr)
dataFldr = os.path.join(rootFldr,"Data")

#monthly data sources
monthlyURL = 'ftp://sidads.colorado.edu/pub/DATASETS/nsidc0116_icemotion_vectors_v3/data/north/monthly_clim/'
monthlyFN = 'icemotion.grid.monthlyclim.MM.n.v3.bin'

#daily data sources
dailyURL = 'ftp://sidads.colorado.edu/pub/DATASETS/nsidc0116_icemotion_vectors_v3/data/north/grid/YYYY/'
dailyFN = 'icemotion.grid.daily.YYYYDDD.n.v3.bin'
dailyFldr = os.path.join(dataFldr,"DailyFiles")
if not os.path.exists(dailyFldr): os.mkdir(dailyFldr)


##---FUNCTIONS---
def bin2raster(arrX,outName):

    if arcpy.Exists(outName): arcpy.Delete_management(outName)
    arcpy.env.scratchWorkspace = os.path.dirname(outName)
    lowerleft = arcpy.Point(-8987500/2,-8987500/2)
    cellSize = 25000
    outRaster = arcpy.NumPyArrayToRaster(arrX,lowerleft,cellSize)
    outRaster.save(outName)
    
#Get all the daily files for  given year
year = 2012
strYear = str(year)

#Update the URL and Filename strings for the current year
yearURL = dailyURL.replace("YYYY",strYear)
yearFN = dailyFN.replace("YYYY",strYear)

#Get/create the output folder
yearFldr = os.path.join(dailyFldr,strYear)
if not os.path.exists(yearFldr): os.mkdir(yearFldr)

#Loop through days
for day in range(1,367):
    strDay = str(day).zfill(3)
    
    #Create the FTP address
    dayFN = yearFN.replace("DDD",strDay)
    theURL = yearURL + dayFN
                            
    #Create the outfile
    outFN = os.path.join(yearFldr,dayFN)
    if os.path.exists(outFN):
        print "-->{} exists; skipping".format(dayFN)
        continue
    #Get retrieve the file
    print "Downloading {}".format(outFN),
    response = urllib.urlopen(theURL)
    #Write to the local file
    print "...saving"
    with open(outFN,'wb') as outFile:
        for line in response:
            outFile.write(line)


##---PROCEDURES---

