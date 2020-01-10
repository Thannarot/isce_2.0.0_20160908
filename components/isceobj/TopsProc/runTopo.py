#
# Author: Piyush Agram
# Copyright 2016
#


import numpy as np 
import argparse
import os
import isceobj
import datetime
import logging

logger = logging.getLogger('isce.topsinsar.topo')

def runTopo(self):
    from zerodop.topozero import createTopozero
    from isceobj.Planet.Planet import Planet

    #####Load the master product
    master = self._insar.loadProduct( self._insar.masterSlcProduct + '.xml')

    ####Catalog for logging
    catalog = isceobj.Catalog.createCatalog(self._insar.procDoc.name)

    ####Load in DEM
    demfilename = self.verifyDEM()
    catalog.addItem('Dem Used', demfilename, 'topo')

    demImage = isceobj.createDemImage()
    demImage.load(demfilename + '.xml')

    boxes = []
    catalog.addItem('Number of common bursts', self._insar.numberOfCommonBursts, 'topo')

    
    ###Check if geometry directory already exists.
    dirname = self._insar.geometryDirname

    if os.path.isdir(dirname):
        logger.info('Geometry directory {0} already exists.'.format(dirname))
    else:
        os.mkdir(dirname)


    ###For each burst
    for index in range(self._insar.numberOfCommonBursts):
        ind = index + self._insar.commonBurstStartMasterIndex
        burst = master.bursts[ind]

        latname = os.path.join(dirname, 'lat_%02d.rdr'%(ind+1))
        lonname = os.path.join(dirname, 'lon_%02d.rdr'%(ind+1))
        hgtname = os.path.join(dirname, 'hgt_%02d.rdr'%(ind+1))
        losname = os.path.join(dirname, 'los_%02d.rdr'%(ind+1))

        #####Run Topo
        planet = Planet(pname='Earth')
        topo = createTopozero()
        topo.slantRangePixelSpacing = burst.rangePixelSize
        topo.prf = 1.0/burst.azimuthTimeInterval
        topo.radarWavelength = burst.radarWavelength
        topo.orbit = burst.orbit
        topo.width = burst.numberOfSamples
        topo.length = burst.numberOfLines
        topo.wireInputPort(name='dem', object=demImage)
        topo.wireInputPort(name='planet', object=planet)
        topo.numberRangeLooks = 1
        topo.numberAzimuthLooks = 1
        topo.lookSide = -1
        topo.sensingStart = burst.sensingStart
        topo.rangeFirstSample = burst.startingRange
        topo.demInterpolationMethod='BIQUINTIC'
        topo.latFilename = latname
        topo.lonFilename = lonname
        topo.heightFilename = hgtname
        topo.losFilename = losname
        topo.topo()

        bbox = [topo.minimumLatitude, topo.maximumLatitude, topo.minimumLongitude, topo.maximumLongitude]
        boxes.append(bbox)

        catalog.addItem('Number of lines for burst {0}'.format(index), burst.numberOfLines, 'topo')
        catalog.addItem('Number of pixels for bursts {0}'.format(index), burst.numberOfSamples, 'topo')
        catalog.addItem('Bounding box for burst {0}'.format(index), bbox, 'topo')

        topo = None

    boxes = np.array(boxes)
    bbox = [np.min(boxes[:,0]), np.max(boxes[:,1]), np.min(boxes[:,2]), np.max(boxes[:,3])]
    catalog.addItem('Overall bounding box', bbox, 'topo')


    catalog.printToLog(logger, "runTopo")
    self._insar.procDoc.addAllFromCatalog(catalog)

    return 
