#
# Author: Piyush Agram
# Copyright 2016
#

import isceobj
import stdproc
from stdproc.stdproc import crossmul
import numpy as np
from isceobj.Util.Poly2D import Poly2D
import argparse
import os
import copy
from isceobj.Sensor.TOPS import createTOPSSwathSLCProduct
from mroipac.correlation.correlation import Correlation
from isceobj.Util.decorators import use_api

@use_api
def multiply(masname, slvname, outname, rngname, fact, masterFrame,
        flatten=True, alks=3, rlks=7):


    masImg = isceobj.createSlcImage()
    masImg.load( masname + '.xml')

    width = masImg.getWidth()
    length = masImg.getLength()

    master = np.memmap(masname, dtype=np.complex64, mode='r', shape=(length,width))
    slave = np.memmap(slvname, dtype=np.complex64, mode='r', shape=(length, width))
   
    if os.path.exists(rngname):
        rng2 = np.memmap(rngname, dtype=np.float32, mode='r', shape=(length,width))
    else:
        print('No range offsets provided')
        rng2 = np.zeros((length,width))

    cJ = np.complex64(-1j)
    
    #Zero out anytging outside the valid region:
    ifg = np.memmap(outname, dtype=np.complex64, mode='w+', shape=(length,width))
    firstS = masterFrame.firstValidSample
    lastS = masterFrame.firstValidSample + masterFrame.numValidSamples -1
    firstL = masterFrame.firstValidLine
    lastL = masterFrame.firstValidLine + masterFrame.numValidLines - 1
    for kk in range(firstL,lastL + 1):
        ifg[kk,firstS:lastS + 1] = master[kk,firstS:lastS + 1] * np.conj(slave[kk,firstS:lastS + 1])
        if flatten:
            phs = np.exp(cJ*fact*rng2[kk,firstS:lastS + 1])
            ifg[kk,firstS:lastS + 1] *= phs

    ####
    master=None
    slave=None
    ifg = None

    objInt = isceobj.createIntImage()
    objInt.setFilename(outname)
    objInt.setWidth(width)
    objInt.setAccessMode('READ')
    objInt.createImage()
    objInt.finalizeImage()
    objInt.renderHdr()

    cmd = 'looks.py -i {0} -a {1} -r {2}'.format(outname, alks, rlks)
    flag = os.system(cmd)

    if flag:
        raise Exception('Failed to multilook ifgs')

    return objInt

@use_api
def computeCoherence(slc1name, slc2name, corname):
                          
    slc1 = isceobj.createImage()
    slc1.load( slc1name + '.xml')
    slc1.createImage()


    slc2 = isceobj.createImage()
    slc2.load( slc2name + '.xml')
    slc2.createImage()

    cohImage = isceobj.createOffsetImage()
    cohImage.setFilename(corname)
    cohImage.setWidth(slc1.getWidth())
    cohImage.setAccessMode('write')
    cohImage.createImage()

    cor = Correlation()
    cor.configure()
    cor.wireInputPort(name='slc1', object=slc1)
    cor.wireInputPort(name='slc2', object=slc2)
    cor.wireOutputPort(name='correlation', object=cohImage)
    cor.coregisteredSlcFlag = True
    cor.calculateCorrelation()

    cohImage.finalizeImage()
    slc1.finalizeImage()
    slc2.finalizeImage()
    return


def adjustValidLineSample(master,slave):

    master_lastValidLine = master.firstValidLine + master.numValidLines - 1
    master_lastValidSample = master.firstValidSample + master.numValidSamples - 1
    slave_lastValidLine = slave.firstValidLine + slave.numValidLines - 1
    slave_lastValidSample = slave.firstValidSample + slave.numValidSamples - 1

    igram_lastValidLine = min(master_lastValidLine, slave_lastValidLine)
    igram_lastValidSample = min(master_lastValidSample, slave_lastValidSample)

    master.firstValidLine = max(master.firstValidLine, slave.firstValidLine)
    master.firstValidSample = max(master.firstValidSample, slave.firstValidSample)

    master.numValidLines = igram_lastValidLine - master.firstValidLine + 1
    master.numValidSamples = igram_lastValidSample - master.firstValidSample + 1

def runBurstIfg(self):
    '''Create burst interferograms.
    '''

    minBurst, maxBurst = self._insar.commonMasterBurstLimits
    nBurst = maxBurst - minBurst

    
    ifgdir = self._insar.fineIfgDirname
    if not os.path.exists(ifgdir):
        os.makedirs(ifgdir)

    ####Load relevant products
    master = self._insar.loadProduct( self._insar.masterSlcProduct + '.xml' )
    slave = self._insar.loadProduct( self._insar.fineCoregDirname + '.xml')

    coregdir = self._insar.fineOffsetsDirname

    fineIfg =  createTOPSSwathSLCProduct()
    fineIfg.configure()

    for ii in range(minBurst, maxBurst):

        jj = ii - minBurst


        ####Process the top bursts
        masBurst = master.bursts[ii] 
        slvBurst = slave.bursts[jj]

        mastername = masBurst.image.filename
        slavename = slvBurst.image.filename
        rdict = {'rangeOff' : os.path.join(coregdir, 'range_%02d.off'%(ii+1)),
                 'azimuthOff': os.path.join(coregdir, 'azimuth_%02d.off'%(ii+1))}
            
            
        adjustValidLineSample(masBurst,slvBurst)
        
        intname = os.path.join(ifgdir, '%s_%02d.int'%('burst',ii+1))
        fact = 4 * np.pi * slvBurst.rangePixelSize / slvBurst.radarWavelength
        intimage = multiply(mastername, slavename, intname,
                    rdict['rangeOff'], fact, masBurst, flatten=True,
                    alks = self.numberAzimuthLooks, rlks=self.numberRangeLooks)

        burst = copy.deepcopy(masBurst)
        burst.image = intimage
        fineIfg.bursts.append(burst)

        ####Estimate coherence
        corname =  os.path.join(ifgdir, '%s_%02d.cor'%('burst',ii+1))
        computeCoherence(mastername, slavename, corname) 


    fineIfg.numberOfBursts = len(fineIfg.bursts)
    self._insar.saveProduct(fineIfg, self._insar.fineIfgDirname + '.xml')
