#
# Author: Piyush Agram
# Copyright 2016
#

import numpy as np
import os
import isceobj
import logging

logger = logging.getLogger('isce.topsinsar.esd')

def runESD(self):
    '''
    Estimate azimuth misregistration.
    '''

    catalog = isceobj.Catalog.createCatalog(self._insar.procDoc.name)

    master = self._insar.loadProduct( self._insar.masterSlcProduct + '.xml' )

    minBurst, maxBurst = self._insar.commonMasterBurstLimits
    slaveBurstStart, slaveBurstEnd = self._insar.commonSlaveBurstLimits

    esddir = self._insar.esdDirname
    alks = self.esdAzimuthLooks
    rlks = self.esdRangeLooks

    maxBurst = maxBurst - 1

    combIntName = os.path.join(esddir, 'combined.int')
    combFreqName = os.path.join(esddir, 'combined_freq.bin')
    combCorName = os.path.join(esddir, 'combined.cor')
    combOffName = os.path.join(esddir, 'combined.off')


    for ff in [combIntName, combFreqName, combCorName, combOffName]:
        if os.path.exists(ff):
            os.remove(ff)


    val = []
    lineCount = 0
    for ii in range(minBurst, maxBurst):
        intname = os.path.join(esddir, 'overlap_%02d.%dalks_%drlks.int'%(ii+1, alks,rlks))
        freqname = os.path.join(esddir, 'freq_%02d.%dalks_%drlks.bin'%(ii+1,alks,rlks))
        corname = os.path.join(esddir, 'overlap_%02d.%dalks_%drlks.cor'%(ii+1, alks, rlks))


        img = isceobj.createImage()
        img.load(intname + '.xml')
        width = img.getWidth()
        length = img.getLength()

        ifg = np.fromfile(intname, dtype=np.complex64).reshape((-1,width))
        freq = np.fromfile(freqname, dtype=np.float32).reshape((-1,width))
        cor = np.fromfile(corname, dtype=np.float32).reshape((-1,width))

        with open(combIntName, 'ab') as fid:
            ifg.tofile(fid)

        with open(combFreqName, 'ab') as fid:
            freq.tofile(fid)

        with open(combCorName, 'ab') as fid:
            cor.tofile(fid)

        off = np.angle(ifg) / freq

        with open(combOffName, 'ab') as fid:
            off.astype(np.float32).tofile(fid)

        lineCount += length


        mask = (np.abs(ifg) > 0) * (cor > self.esdCoherenceThreshold)

        vali = off[mask]
        val = np.hstack((val, vali))

    

    img = isceobj.createIntImage()
    img.filename = combIntName
    img.setWidth(width)
    img.setAccessMode('READ')
    img.renderHdr()

    for fname in [combFreqName, combCorName, combOffName]:
        img = isceobj.createImage()
        img.bands = 1
        img.scheme = 'BIP'
        img.dataType = 'FLOAT'
        img.filename = fname
        img.setWidth(width)
        img.setAccessMode('READ')
        img.renderHdr()

    if val.size == 0 :
        raise Exception('Coherence threshold too strict. No points left for reliable ESD estimate') 

    medianval = np.median(val)
    meanval = np.mean(val)
    stdval = np.std(val)

    hist, bins = np.histogram(val, 50, normed=1)
    center = 0.5*(bins[:-1] + bins[1:])


    debugplot = True
    try:
        import matplotlib as mpl
        mpl.use('Agg')
        import matplotlib.pyplot as plt
    except:
        print('Matplotlib could not be imported. Skipping debug plot...')
        debugplot = False

    if debugplot:
        ####Plotting
        plt.figure()
        plt.bar(center, hist, align='center', width = 0.7*(bins[1] - bins[0]))
        plt.xlabel('Azimuth shift in pixels')
        plt.savefig( os.path.join(esddir, 'ESDmisregistration.png'))
        plt.close()


    catalog.addItem('Median', medianval, 'esd')
    catalog.addItem('Mean', meanval, 'esd')
    catalog.addItem('Std', stdval, 'esd')
    catalog.addItem('coherence threshold', self.esdCoherenceThreshold, 'esd')
    catalog.addItem('number of coherent points', val.size, 'esd')

    catalog.printToLog(logger, "runESD")
    self._insar.procDoc.addAllFromCatalog(catalog)

    self._insar.slaveTimingCorrection = medianval * master.bursts[0].azimuthTimeInterval 

    return

