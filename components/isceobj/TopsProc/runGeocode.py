#
# Author: Piyush Agram
# Copyright 2016
#
import logging
from zerodop.geozero import createGeozero
from stdproc.rectify.geocode.Geocodable import Geocodable
import isceobj
import iscesys
from iscesys.ImageUtil.ImageUtil import ImageUtil as IU
from isceobj.Planet.Planet import Planet
from isceobj.Orbit.Orbit import Orbit
import os
import datetime

logger = logging.getLogger('isce.topsinsar.runGeocode')
posIndx = 1

def runGeocode(self, prodlist, unwrapflag, bbox, is_offset_mode=False):
    '''Generalized geocoding of all the files listed above.'''
    from isceobj.Catalog import recordInputsAndOutputs
    logger.info("Geocoding Image")
    insar = self._insar

    if isinstance(prodlist,str):
        from isceobj.Util.StringUtils import StringUtils as SU
        tobeGeocoded = SU.listify(prodlist)
    else:
        tobeGeocoded = prodlist

    #remove files that have not been processed
    for toGeo in tobeGeocoded:
        if not os.path.exists(toGeo):
            tobeGeocoded.remove(toGeo)
    print('Number of products to geocode: ', len(tobeGeocoded))

    referenceProduct = insar.loadProduct( insar.fineCoregDirname + '.xml')

    ###Create merged orbit
    orb = Orbit()
    orb.configure()

    burst = referenceProduct.bursts[0]
    #Add first burst orbit to begin with
    for sv in burst.orbit:
         orb.addStateVector(sv)

    ##Add all state vectors
    for bb in referenceProduct.bursts:
        for sv in bb.orbit:
            if (sv.time< orb.minTime) or (sv.time > orb.maxTime):
                orb.addStateVector(sv)

        bb.orbit = orb

    if bbox is None:
        snwe = referenceProduct.getBbox()
    else:
        snwe = list(bbox)
        if len(snwe) != 4:
            raise ValueError('Bounding box should be a list/tuple of length 4')


    ####Get required values from product
    t0 = burst.sensingStart
    dtaz = burst.azimuthTimeInterval
    r0 = burst.startingRange
    dr = burst.rangePixelSize
    wvl = burst.radarWavelength
    planet = Planet(pname='Earth')
    
    ###Setup DEM
    demfilename = self.verifyDEM()
    demImage = isceobj.createDemImage()
    demImage.load(demfilename + '.xml')

    ###Catalog for tracking
    catalog = isceobj.Catalog.createCatalog(insar.procDoc.name)
    catalog.addItem('Dem Used', demfilename, 'geocode')

    #####Geocode one by one
    first = False
    ge = Geocodable()
    for prod in tobeGeocoded:
        objGeo = createGeozero()
        objGeo.configure()

        ####IF statements to check for user configuration
        objGeo.snwe = snwe
        objGeo.demCropFilename = os.path.join(insar.mergedDirname, insar.demCropFilename)
        if is_offset_mode:  ### If using topsOffsetApp, image has been "pre-looked" by the
            objGeo.numberRangeLooks = self.skipwidth    ### skips in runDenseOffsets
            objGeo.numberAzimuthLooks = self.skiphgt
        else:
            objGeo.numberRangeLooks = self.numberRangeLooks
            objGeo.numberAzimuthLooks = self.numberAzimuthLooks
        objGeo.lookSide = -1 #S1A is currently right looking only

        #create the instance of the input image and the appropriate
        #geocode method
        inImage,method = ge.create(prod)
        objGeo.method = method

        objGeo.slantRangePixelSpacing = dr
        objGeo.prf = 1.0 / dtaz
        objGeo.orbit = orb 
        objGeo.width = inImage.getWidth()
        objGeo.length = inImage.getLength()
        objGeo.dopplerCentroidCoeffs = [0.]
        objGeo.radarWavelength = wvl

        if is_offset_mode:  ### If using topsOffsetApp, as above, the "pre-looking" adjusts the range/time start
            objGeo.rangeFirstSample = r0 + (self.offset_left-1) * dr
            objGeo.setSensingStart( t0 + datetime.timedelta(seconds=((self.offset_top-1)*dtaz)))
        else:
            objGeo.rangeFirstSample = r0 + ((self.numberRangeLooks-1)/2.0) * dr
            objGeo.setSensingStart( t0 + datetime.timedelta(seconds=(((self.numberAzimuthLooks-1)/2.0)*dtaz)))
        objGeo.wireInputPort(name='dem', object=demImage)
        objGeo.wireInputPort(name='planet', object=planet)
        objGeo.wireInputPort(name='tobegeocoded', object=inImage)

        objGeo.geocode()

        catalog.addItem('Geocoding: ', inImage.filename, 'geocode')
        catalog.addItem('Output file: ', inImage.filename + '.geo', 'geocode')
        catalog.addItem('Width', inImage.width, 'geocode')
        catalog.addItem('Length', inImage.length, 'geocode')
        catalog.addItem('Range looks', self.numberRangeLooks, 'geocode')
        catalog.addItem('Azimuth looks', self.numberAzimuthLooks, 'geocode')
        catalog.addItem('South' , objGeo.minimumGeoLatitude, 'geocode')
        catalog.addItem('North', objGeo.maximumGeoLatitude, 'geocode')
        catalog.addItem('West', objGeo.minimumGeoLongitude, 'geocode')
        catalog.addItem('East', objGeo.maximumGeoLongitude, 'geocode')

    catalog.printToLog(logger, "runGeocode")
    self._insar.procDoc.addAllFromCatalog(catalog)
