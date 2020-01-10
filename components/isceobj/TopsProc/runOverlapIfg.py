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
from .runBurstIfg import adjustValidLineSample
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


def runOverlapIfg(self):
    '''Create overlap interferograms.
    '''

    minBurst = self._insar.commonBurstStartMasterIndex
    maxBurst = minBurst + self._insar.numberOfCommonBursts


    nBurst = maxBurst - minBurst

    
    ifgdir = os.path.join( self._insar.coarseIfgDirname, self._insar.overlapsSubDirname )
    if not os.path.exists(ifgdir):
        os.makedirs(ifgdir)

    ####All indexing is w.r.t stack master for overlaps
    maxBurst = maxBurst - 1
   

    ####Load relevant products
    topMaster = self._insar.loadProduct( self._insar.masterSlcTopOverlapProduct + '.xml')
    botMaster = self._insar.loadProduct( self._insar.masterSlcBottomOverlapProduct + '.xml')

    topCoreg = self._insar.loadProduct( self._insar.coregTopOverlapProduct + '.xml')
    botCoreg = self._insar.loadProduct( self._insar.coregBottomOverlapProduct + '.xml')

    coregdir = os.path.join(self._insar.coarseOffsetsDirname, self._insar.overlapsSubDirname)

    topIfg = createTOPSSwathSLCProduct()
    topIfg.configure()

    botIfg = createTOPSSwathSLCProduct()
    botIfg.configure()



    for ii in range(minBurst, maxBurst):

        jj = ii - minBurst


        ####Process the top bursts
        master = topMaster.bursts[jj] 
        slave  = topCoreg.bursts[jj]

        mastername = master.image.filename
        slavename = slave.image.filename
        rdict = {'rangeOff' : os.path.join(coregdir, 'range_top_%02d_%02d.off'%(ii+1,ii+2)),
                 'azimuthOff': os.path.join(coregdir, 'azimuth_top_%02d_%02d.off'%(ii+1,ii+2))}
            
            
        adjustValidLineSample(master,slave)
        
        intname = os.path.join(ifgdir, '%s_top_%02d_%02d.int'%('burst',ii+1,ii+2))
        fact = 4 * np.pi * slave.rangePixelSize / slave.radarWavelength
        intimage = multiply(mastername, slavename, intname,
                    rdict['rangeOff'], fact, master, flatten=True,
                    alks = self.numberAzimuthLooks, rlks=self.numberRangeLooks)

        burst = copy.deepcopy(master)
        burst.image = intimage
        topIfg.bursts.append(burst)



        ####Process the bottom bursts
        master = botMaster.bursts[jj]
        slave = botCoreg.bursts[jj]


        mastername =  master.image.filename
        slavename = slave.image.filename
        rdict = {'rangeOff' : os.path.join(coregdir, 'range_bot_%02d_%02d.off'%(ii+1,ii+2)),
                 'azimuthOff': os.path.join(coregdir, 'azimuth_bot_%02d_%02d.off'%(ii+1,ii+2))}

        adjustValidLineSample(master,slave)
        intname = os.path.join(ifgdir, '%s_bot_%02d_%02d.int'%('burst',ii+1,ii+2))
        fact = 4 * np.pi * slave.rangePixelSize / slave.radarWavelength
        intimage = multiply(mastername, slavename, intname,
                    rdict['rangeOff'], fact, master, flatten=True,
                    alks = self.numberAzimuthLooks, rlks=self.numberRangeLooks)

        burst = copy.deepcopy(master)
        burst.image = intimage
        botIfg.bursts.append(burst)


    topIfg.numberOfBursts = len(topIfg.bursts)
    botIfg.numberOfBursts = len(botIfg.bursts)

    self._insar.saveProduct(topIfg, self._insar.coarseIfgTopOverlapProduct + '.xml')
    self._insar.saveProduct(botIfg, self._insar.coarseIfgBottomOverlapProduct + '.xml')
