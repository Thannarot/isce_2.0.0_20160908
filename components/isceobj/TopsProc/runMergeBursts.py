#
# Author: Piyush Agram
# Copyright 2016
#


import numpy as np 
import os
import isceobj
import datetime
import logging
from isceobj.Util.ImageUtil import ImageLib as IML
from isceobj.Util.decorators import use_api


def mergeBursts(frame, fileList, outfile,
        method='top'):
    '''
    Merge burst products into single file.
    Simple numpy based stitching
    '''

    ###Check against metadata
    if frame.numberOfBursts != len(fileList):
        print('Warning : Number of burst products does not appear to match number of bursts in metadata')


    t0 = frame.bursts[0].sensingStart
    dt = frame.bursts[0].azimuthTimeInterval
    width = frame.bursts[0].numberOfSamples

    #######
    tstart = frame.bursts[0].sensingStart 
    tend = frame.bursts[-1].sensingStop
    nLines = int( np.round((tend - tstart).total_seconds() / dt)) + 1
    print('Expected total nLines: ', nLines)


    img = isceobj.createImage()
    img.load( fileList[0] + '.xml')
    bands = img.bands
    scheme = img.scheme
    npType = IML.NUMPY_type(img.dataType)

    azMasterOff = []
    for index in range(frame.numberOfBursts):
        burst = frame.bursts[index]
        soff = burst.sensingStart + datetime.timedelta(seconds = (burst.firstValidLine*dt)) 
        start = int(np.round((soff - tstart).total_seconds() / dt))
        end = start + burst.numValidLines

        azMasterOff.append([start,end])

        print('Burst: ', index, [start,end])

        if index == 0:
            linecount = start

    outMap = IML.memmap(outfile, mode='write', nchannels=bands,
            nxx=width, nyy=nLines, scheme=scheme, dataType=npType)

    for index in range(frame.numberOfBursts):
        curBurst = frame.bursts[index]
        curLimit = azMasterOff[index]

        curMap = IML.mmapFromISCE(fileList[index], logging)

        #####If middle burst
        if index > 0:
            topBurst = frame.bursts[index-1]
            topLimit = azMasterOff[index-1]
            topMap = IML.mmapFromISCE(fileList[index-1], logging)

            olap = topLimit[1] - curLimit[0]

            if olap <= 0:
                raise Exception('No Burst Overlap')


            for bb in range(bands):
                topData =  topMap.bands[bb][topBurst.firstValidLine: topBurst.firstValidLine + topBurst.numValidLines,:]

                curData =  curMap.bands[bb][curBurst.firstValidLine: curBurst.firstValidLine + curBurst.numValidLines,:]

                im1 = topData[-olap:,:]
                im2 = curData[:olap,:]

                if method=='avg':
                    data = 0.5*(im1 + im2)
                elif method == 'top':
                    data = im1
                elif method == 'bot':
                    data = im2
                else:
                    raise Exception('Method should be top/bot/avg')

                outMap.bands[bb][linecount:linecount+olap,:] = data

            tlim = olap
        else:
            tlim = 0

        linecount += tlim
            
        if index != (frame.numberOfBursts-1):
            botBurst = frame.bursts[index+1]
            botLimit = azMasterOff[index+1]
            
            olap = curLimit[1] - botLimit[0]

            if olap < 0:
                raise Exception('No Burst Overlap')

            blim = botLimit[0] - curLimit[0]
        else:
            blim = curBurst.numValidLines
       
        lineout = blim - tlim
        
        for bb in range(bands):
            curData =  curMap.bands[bb][curBurst.firstValidLine: curBurst.firstValidLine + curBurst.numValidLines,:]
            outMap.bands[bb][linecount:linecount+lineout,:] = curData[tlim:blim,:] 

        linecount += lineout
        curMap = None
        topMap = None

    IML.renderISCEXML(outfile, bands,
            nLines, width,
            img.dataType, scheme)

    oimg = isceobj.createImage()
    oimg.load(outfile + '.xml')
    oimg.imageType = img.imageType
    oimg.renderHdr()
    try:
        outMap.bands[0].base.base.flush()
    except:
        pass

@use_api
def multilook(intName, outname=None, alks=5, rlks=15):

    if outname is None:
        cmd = 'looks.py -i {0} -a {1} -r {2}'.format(intName,alks,rlks)
    else:
        cmd = 'looks.py -i {0} -o {1} -a {2} -r {3}'.format(intName, outname, alks, rlks)
    
    flag = os.system(cmd)

    if flag:
        raise Exception('Failed to multilook %s'%(intName))

    spl = os.path.splitext(intName)
    return '{0}.{1}alks_{2}rlks{3}'.format(spl[0],alks,rlks,spl[1])


def runMergeBursts(self):
    '''
    Merge burst products to make it look like stripmap.
    Currently will merge interferogram, lat, lon, z and los.
    '''

    ifg = self._insar.loadProduct( self._insar.fineIfgDirname + '.xml')

    minBurst, maxBurst = self._insar.commonMasterBurstLimits

    ####Geometry products
    latList = [os.path.join(self._insar.geometryDirname, 'lat_%02d.rdr'%(x+1)) for x in range(minBurst, maxBurst)]
    lonList = [os.path.join(self._insar.geometryDirname, 'lon_%02d.rdr'%(x+1)) for x in range(minBurst, maxBurst)]
    hgtList = [os.path.join(self._insar.geometryDirname, 'hgt_%02d.rdr'%(x+1)) for x in range(minBurst, maxBurst)]
    losList = [os.path.join(self._insar.geometryDirname, 'los_%02d.rdr'%(x+1)) for x in range(minBurst, maxBurst)]

    ####Interferogram
    intList = [x.image.filename for x in ifg.bursts]
    corList = [os.path.join(self._insar.fineIfgDirname, 'burst_%02d.cor'%(x+1)) for x in range(minBurst, maxBurst)]

    mergedir = self._insar.mergedDirname
    if not os.path.isdir(mergedir):
        os.makedirs(mergedir)

    
    suffix = '.full'
    if (self.numberRangeLooks == 1) and (self.numberAzimuthLooks==1):
        suffix=''

    ####Merge interferograms
    mergeBursts(ifg, intList, os.path.join(mergedir, self._insar.mergedIfgname+suffix))
    mergeBursts(ifg, corList, os.path.join(mergedir, self._insar.correlationFilename+suffix))

    ###Merge LOS
    mergeBursts(ifg, losList, os.path.join(mergedir, self._insar.mergedLosName+suffix))

    ###Merge lat, lon, z
    mergeBursts(ifg, latList, os.path.join(mergedir, 'lat.rdr'+suffix))
    mergeBursts(ifg, lonList, os.path.join(mergedir, 'lon.rdr'+suffix))
    mergeBursts(ifg, hgtList, os.path.join(mergedir, 'z.rdr'+suffix))


    if suffix not in ['',None]:
        print('Skipping multi-looking ....')
        multilook(os.path.join(mergedir, self._insar.mergedIfgname+suffix),
              outname = os.path.join(mergedir, self._insar.mergedIfgname),
              alks = self.numberAzimuthLooks, rlks=self.numberRangeLooks)

        multilook(os.path.join(mergedir, self._insar.correlationFilename+suffix),
              outname = os.path.join(mergedir, self._insar.correlationFilename),
              alks = self.numberAzimuthLooks, rlks=self.numberRangeLooks)

        multilook(os.path.join(mergedir, self._insar.mergedLosName+suffix),
              outname = os.path.join(mergedir, self._insar.mergedLosName),
              alks = self.numberAzimuthLooks, rlks=self.numberRangeLooks)

if __name__ == '__main__' :
    '''
    Merge products burst-by-burst.
    '''

    main()
