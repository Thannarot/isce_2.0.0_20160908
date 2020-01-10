#
# Author: Piyush Agram
# Copyright 2016
#

import logging
import isceobj
import mroipac
logger = logging.getLogger('isce.topsinsar.runPreprocessor')

def runComputeBaseline(self):
    
    from isceobj.Planet.Planet import Planet
    import numpy as np

    master = self._insar.loadProduct( self._insar.masterSlcProduct + '.xml')
    slave = self._insar.loadProduct( self._insar.slaveSlcProduct + '.xml')

    burstOffset, minBurst, maxBurst = master.getCommonBurstLimits(slave)

    self._insar.commonBurstStartMasterIndex = minBurst
    self._insar.commonBurstStartSlaveIndex  = minBurst + burstOffset
    self._insar.numberOfCommonBursts = maxBurst - minBurst


    catalog = isceobj.Catalog.createCatalog(self._insar.procDoc.name)
    catalog.addItem('Number of bursts in master', master.numberOfBursts, 'baseline')
    catalog.addItem('First common burst in master', minBurst, 'baseline')
    catalog.addItem('Last common burst in master', maxBurst, 'baseline')
    catalog.addItem('Number of bursts in slave', slave.numberOfBursts, 'baseline')
    catalog.addItem('First common burst in slave', minBurst + burstOffset, 'baseline')
    catalog.addItem('Last common burst in slave', maxBurst + burstOffset, 'baseline')
    catalog.addItem('Number of common bursts', maxBurst - minBurst, 'baseline')

    refElp = Planet(pname='Earth').ellipsoid

    Bpar = []
    Bperp = []

    for boff in [0, self._insar.numberOfCommonBursts-1]:
        ###Baselines at top of common bursts
        mBurst = master.bursts[self._insar.commonBurstStartMasterIndex + boff]
        sBurst = slave.bursts[self._insar.commonBurstStartSlaveIndex + boff]

        ###Target at mid range 
        tmid = mBurst.sensingMid
        rng = mBurst.midRange
        masterSV = mBurst.orbit.interpolate(tmid, method='hermite')
        target = mBurst.orbit.rdr2geo(tmid, rng)

        slvTime, slvrng = sBurst.orbit.geo2rdr(target)
        slaveSV = sBurst.orbit.interpolateOrbit(slvTime, method='hermite')

        targxyz = np.array(refElp.LLH(target[0], target[1], target[2]).ecef().tolist())
        mxyz = np.array(masterSV.getPosition())
        mvel = np.array(masterSV.getVelocity())
        sxyz = np.array(slaveSV.getPosition())

        aa = np.linalg.norm(sxyz-mxyz)
        costheta = (rng*rng + aa*aa - slvrng*slvrng)/(2.*rng*aa)

        Bpar.append(aa*costheta)

        perp = aa * np.sqrt(1 - costheta*costheta)
        direction = np.sign(np.dot( np.cross(targxyz-mxyz, sxyz-mxyz), mvel))
        Bperp.append(direction*perp)    


    catalog.addItem('Bpar at midrange for first common burst', Bpar[0], 'baseline')
    catalog.addItem('Bperp at midrange for first common burst', Bperp[0], 'baseline')
    catalog.addItem('Bpar at midrange for last common burst', Bpar[1], 'baseline')
    catalog.addItem('Bperp at midrange for last common burst', Bperp[1], 'baseline')

    catalog.printToLog(logger, "runComputeBaseline")
    self._insar.procDoc.addAllFromCatalog(catalog)

