#
# Author: Piyush Agram
# Copyright 2016
#


import numpy as np
import os
import isceobj
import copy
import datetime
import logging
from isceobj.Sensor.TOPS import createTOPSSwathSLCProduct
from isceobj.Util.ImageUtil import ImageLib as IML

logger = logging.getLogger('isce.topsinsar.overlaps')


def subset(inname, outname, sliceline, slicepix):
    '''Subset the input image to output image.
    '''

    inimg = isceobj.createImage()
    inimg.load(inname + '.xml')

    indata = IML.mmapFromISCE(inname, logging).bands[0]

   
    outdata = indata[sliceline, slicepix]
    outdata.tofile(outname)
    inimg.filename = outname
    inimg.setWidth(slicepix.stop - slicepix.start)
    inimg.setLength(sliceline.stop - sliceline.start)
    inimg.setAccessMode('READ')
    inimg.renderHdr()

    indata = None
    return


def runSubsetOverlaps(self):
    '''
    Create geometry files corresponding to burst overlaps.
    '''

    ####Load master metadata
    mFrame = self._insar.loadProduct( self._insar.masterSlcProduct + '.xml')

    ####Output directory for overlap geometry images
    geomdir = self._insar.geometryDirname
    outdir = os.path.join(geomdir, self._insar.overlapsSubDirname)
    submasterdir = os.path.join(self._insar.masterSlcProduct, self._insar.overlapsSubDirname) 


    if os.path.isdir(outdir):
        logger.info('Overlap directory {0} already exists'.format(outdir))
    else:
        os.makedirs(outdir)


    if os.path.isdir(submasterdir):
        logger.info('Submaster Overlap directory {0} already exists'.format(submasterdir))
    else:
        os.makedirs(submasterdir)


    ###Azimuth time interval
    dt = mFrame.bursts[0].azimuthTimeInterval        
    topFrame = createTOPSSwathSLCProduct()
    topFrame.configure()

    bottomFrame = createTOPSSwathSLCProduct()
    bottomFrame.configure()

    catalog = isceobj.Catalog.createCatalog(self._insar.procDoc.name)


    ###For each overlap
    for ii in range(self._insar.numberOfCommonBursts - 1):
        ind = ii + self._insar.commonBurstStartMasterIndex

        topBurst = mFrame.bursts[ind]
        botBurst = mFrame.bursts[ind+1]

        overlap_start_time = botBurst.sensingStart
        overlap_end_time = topBurst.sensingStop
        catalog.addItem('Overlap {0} start time'.format(ind), overlap_start_time, 'subset')
        catalog.addItem('Overlap {0} stop time'.format(ind), overlap_end_time, 'subset')

        nLinesOverlap = int( np.round((overlap_end_time - overlap_start_time).total_seconds() / dt)) + 1
        catalog.addItem('Overlap {0} number of lines'.format(ind), nLinesOverlap, 'subset')

        length = topBurst.numberOfLines
        width = topBurst.numberOfSamples

        topStart = int ( np.round( (botBurst.sensingStart - topBurst.sensingStart).total_seconds()/dt))+ botBurst.firstValidLine       
        overlapLen = topBurst.firstValidLine + topBurst.numValidLines - topStart
      
        catalog.addItem('Overlap {0} number of valid lines'.format(ind), overlapLen, 'subset')

        ###Create slice objects for overlaps
        topslicey = slice(topStart, topStart+overlapLen)
        topslicex = slice(0, width)
    

        botslicey = slice(botBurst.firstValidLine, botBurst.firstValidLine + overlapLen)
        botslicex = slice(0, width)

        for prefix in ['lat','lon','hgt']:
            infile = os.path.join(geomdir, prefix + '_%02d.rdr'%(ind+2))
            outfile = os.path.join(outdir, prefix + '_%02d_%02d.rdr'%(ind+1,ind+2))
       
            subset(infile, outfile, botslicey, botslicex)

       
        masname1 = topBurst.image.filename
        masname2 = botBurst.image.filename

       
        master_outname1 = os.path.join(submasterdir , 'burst_top_%02d_%02d.slc'%(ind+1,ind+2))
        master_outname2 = os.path.join(submasterdir , 'burst_bot_%02d_%02d.slc'%(ind+1,ind+2))


        subset(masname1, master_outname1, topslicey, topslicex)
        subset(masname2, master_outname2, botslicey, botslicex)


        ####TOP frame
        burst = copy.deepcopy(topBurst)
        burst.firstValidLine = 0
        burst.numberOfLines = overlapLen
        burst.numValidLines = overlapLen
        burst.sensingStart = topBurst.sensingStart + datetime.timedelta(0,topStart*dt) # topStart*dt
        burst.sensingStop = topBurst.sensingStart + datetime.timedelta(0,(topStart+overlapLen-1)*dt) # (topStart+overlapLen-1)*dt

        ###Replace file name in image
        burst.image.filename = master_outname1
        burst.image.setLength(overlapLen)
        burst.image.setWidth(width)

        topFrame.bursts.append(burst)

        burst = None


        ####BOTTOM frame
        burst = copy.deepcopy(botBurst)
        burst.firstValidLine = 0
        burst.numberOfLines = overlapLen
        burst.numValidLines = overlapLen
        burst.sensingStart = botBurst.sensingStart + datetime.timedelta(seconds=botBurst.firstValidLine*dt)
        burst.sensingStop = botBurst.sensingStart + datetime.timedelta(seconds=(botBurst.firstValidLine+overlapLen-1)*dt)

        ###Replace file name in image
        burst.image.filename = master_outname2
        burst.image.setLength(overlapLen)
        burst.image.setWidth(width)

        bottomFrame.bursts.append(burst)

        burst = None

        print('Top: ', [x.image.filename for x in topFrame.bursts])
        print('Bottom: ', [x.image.filename for x in bottomFrame.bursts])


    topFrame.numberOfBursts = len(topFrame.bursts)
    bottomFrame.numberOfBursts = len(bottomFrame.bursts)

    catalog.printToLog(logger, "runSubsetOverlaps")
    self._insar.procDoc.addAllFromCatalog(catalog)

    self._insar.saveProduct(topFrame, self._insar.masterSlcTopOverlapProduct + '.xml')
    self._insar.saveProduct(bottomFrame, self._insar.masterSlcBottomOverlapProduct + '.xml')

