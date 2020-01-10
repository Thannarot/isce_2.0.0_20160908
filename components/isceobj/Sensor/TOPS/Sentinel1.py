#!/usr/bin/env python3 

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# copyright: 2014 to the present, california institute of technology.
# all rights reserved. united states government sponsorship acknowledged.
# any commercial use must be negotiated with the office of technology transfer
# at the california institute of technology.
# 
# this software may be subject to u.s. export control laws. by accepting this
# software, the user agrees to comply with all applicable u.s. export laws and
# regulations. user has the responsibility to obtain export licenses,  or other
# export authority as may be required before exporting such information to
# foreign countries or providing access to foreign persons.
# 
# installation and use of this software is restricted by a license agreement
# between the licensee and the california institute of technology. it is the
# user's responsibility to abide by the terms of the license agreement.
#
# Author: Piyush Agram
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~



import xml.etree.ElementTree as ET
import datetime
import isceobj
from .BurstSLC import BurstSLC
from isceobj.Util import Poly1D, Poly2D
from isceobj.Planet.Planet import Planet
from isceobj.Orbit.Orbit import StateVector, Orbit
from isceobj.Orbit.OrbitExtender import OrbitExtender
from isceobj.Planet.AstronomicalHandbook import Const
from iscesys.Component.Component import Component
from iscesys.Component.ProductManager import ProductManager
from iscesys.DateTimeUtil.DateTimeUtil import DateTimeUtil as DTUtil
import os
import glob
import numpy as np
import shelve

XML_LIST = Component.Parameter('xml',
        public_name = 'xml',
        default = [],
        container = list,
        type = str,
        doc = 'List of input XML files to stitch together')

TIFF_LIST = Component.Parameter('tiff',
        public_name = 'tiff',
        default = [],
        container = list,
        type = str,
        doc = 'List of input TIFF files to stitch together')

MANIFEST = Component.Parameter('manifest',
        public_name = 'manifest',
        default = None,
        type = str,
        doc = 'Manifest file with IPF version')

SAFE_LIST = Component.Parameter('safe',
        public_name = 'safe',
        default = [],
        container = list,
        type = str,
        doc = 'List of safe directories')

SWATH_NUMBER = Component.Parameter('swathNumber',
        public_name = 'swath number',
        default = None,
        type = int,
        mandatory = True,
        doc = 'Swath number to process')

POLARIZATION = Component.Parameter('polarization',
        public_name = 'polarization',
        default = 'vv',
        type = str,
        mandatory = True,
        doc = 'Polarization')

ORBIT_FILE = Component.Parameter('orbitFile',
        public_name = 'orbit file',
        default = None,
        type = str,
        doc = 'External orbit file with state vectors')

AUX_FILE = Component.Parameter('auxFile',
        public_name = 'auxiliary file',
        default = None,
        type = str,
        doc = 'External auxiliary file to use for antenna pattern')

ORBIT_DIR = Component.Parameter('orbitDir',
        public_name = 'orbit directory',
        default = None,
        type = str,
        doc = 'Directory to search for orbit files')

AUX_DIR = Component.Parameter('auxDir',
        public_name = 'auxiliary data directory',
        default = None,
        type = str,
        doc = 'Directory to search for auxiliary data')

OUTPUT = Component.Parameter('output',
        public_name = 'output directory',
        default = None,
        type = str,
        doc = 'Directory where bursts get unpacked')

ROI = Component.Parameter('regionOfInterest',
        public_name = 'region of interest',
        default = [],
        container = list,
        type = float,
        doc = 'User defined area to crop in SNWE')

####List of facilities
PRODUCT = Component.Facility('product',
        public_name='product',
        module = 'isceobj.Sensor.TOPS',
        factory='createTOPSSwathSLCProduct',
        args = (),
        mandatory = True,
        doc = 'TOPS SLC Swath product populated by the reader')


class Sentinel1(Component):
    """
    Sentinel-1A TOPS reader
    """

    family = 's1atops'
    logging = 'isce.sensor.S1A_TOPS'

    parameter_list = (XML_LIST,
                      TIFF_LIST,
                      MANIFEST,
                      SAFE_LIST,
                      ORBIT_FILE,
                      AUX_FILE,
                      ORBIT_DIR,
                      AUX_DIR,
                      OUTPUT,
                      ROI,
                      SWATH_NUMBER,
                      POLARIZATION)

    facility_list = (PRODUCT,)

    def __init__(self, name=''):
        super().__init__(family=self.__class__.family, name=name) 


        ###Variables never meant to be controlled by user
        self._xml_root=None
        self._burstWidth = None    ###Common width
        self._burstLength = None   ###Common length
        self._numSlices = None     ###Number of slides
        self._parsed = False       ###If products have been parsed already
        self._tiffSrc = []

        ####Specifically used only for IPF 002.36
        ####Scotch tape fix
        self._elevationAngleVsTau = []  ###For storing time samples
        self._Geap = None    ###IQ antenna pattern
        self._delta_theta = None  ###Elevation angle increment

        return

    def validateUserInputs(self):
        '''
        Validate inputs provided by user.
        Populate tiff and xml list using SAFE folder names.
        '''
        import fnmatch
        import zipfile

        if len(self.xml) == 0:
            if self.swathNumber is None:
                raise Exception('Desired swath number is not provided')

            if len(self.safe) == 0:
                raise Exception('SAFE directory is not provided')
            elif self.swathNumber not in [1,2,3]:
                raise Exception('Swath number must be one out of [1,2,3]')
        

        elif len(self.tiff) != 0:
            if len(self.xml) != len(self.tiff):
                raise Exception('Number of TIFF and XML files dont match')


        ####First find annotation file
        ####Dont need swath number when driving with xml and tiff file
        if len(self.xml) == 0:
            swathid = 's1?-iw%d'%(self.swathNumber)

        polid = self.polarization

        if len(self.xml) == 0:
            match = None
            for dirname in self.safe:
                match = None

                if dirname.endswith('.zip'):
                    pattern = os.path.join('*SAFE','annotation', swathid) + '-slc-' + polid + '*.xml'
                    zf = zipfile.ZipFile(dirname, 'r')
                    match = fnmatch.filter(zf.namelist(), pattern)
                    zf.close()

                    if (len(match) == 0):
                        raise Exception('No annotation xml file found in zip file: {0}'.format(dirname))

                    ####Add /vsizip at the start to make it a zip file
                    self.xml.append('/vsizip/'+os.path.join(dirname, match[0]) )

                else:
                    pattern = os.path.join('annotation',swathid)+'-slc-'+polid+'*.xml'
                    match = glob.glob( os.path.join(dirname, pattern))

                    if (len(match) == 0):
                        raise Exception('No annotation xml file found in {0}'.format(dirname))
            
                    self.xml.append(match[0])

        if len(self.xml) == 0:
            raise Exception('No annotation files found')

        print('Input XML files: ', self.xml)

        ####Find TIFF file
        if (len(self.tiff) == 0) and (len(self.safe) != 0 ):
            for dirname in self.safe:
                match = None

                if dirname.endswith('.zip'):
                    pattern = os.path.join('*SAFE','measurement', swathid) + '-slc-' + polid + '*.tiff'
                    zf = zipfile.ZipFile(dirname, 'r')
                    match = fnmatch.filter(zf.namelist(), pattern)
                    zf.close()

                    if (len(match) == 0):
                        raise Exception('No tiff file found in zip file: {0}'.format(dirname))

                    ####Add /vsizip at the start to make it a zip file
                    self.tiff.append('/vsizip/' + os.path.join(dirname, match[0]) )


                else:
                    pattern = os.path.join('measurement', swathid) + '-slc-' + polid + '*.tiff'
                    match = glob.glob(os.path.join(dirname, pattern))

                    if len(match) == 0 :
                        raise Exception('No tiff file found in directory: {0}'.format(dirname))

                    self.tiff.append(match[0])

        print('Input TIFF files: ', self.tiff)


        if len(self.tiff) != 0 :
            if len(self.tiff) != len(self.xml):
                raise Exception('Number of XML and TIFF files dont match')


        ####Find manifest files
        if len(self.safe) != 0:
            manifests = []
            for dirname in self.safe:
                if dirname.endswith('.zip'):
                    pattern='*SAFE/manifest.safe'
                    zf = zipfile.ZipFile(dirname, 'r')
                    match = fnmatch.filter(zf.namelist(), pattern)
                    zf.close()
                    manifests.append('/vsizip/' + os.path.join(dirname, match[0]))
                else:
                    manifests.append(os.path.join(dirname, 'manifest.safe'))
    
            print('Manifest files: ', manifests)
            self.manifest = manifests[0]


        ####Check bbox
        roi = self.regionOfInterest
        if len(roi) != 0:
            if len(roi) != 4:
                raise Exception('4 floats in SNWE format expected for bbox/ROI')

            if (roi[0] >= roi[1]) or (roi[2] >= roi[3]):
                raise Exception('Error in bbox definition: SNWE expected')

        return


    def parse(self):
        '''
        Parser for S1A IW data.
        This is meant to only read in the metadata and does not read any imagery.
        Can be used only with the annotation xml files if needed.
        '''
    
        ####Check user inputs
        self.validateUserInputs()

        self._numSlices = len(self.xml)

        if self._numSlices > 1:
            self._parseMultiSlice()
        else:
            self._parseOneSlice()

        ###Set the parsed flag to True
        self._parsed = True
        return


    def _parseOneSlice(self):
        '''
        '''
        if self.xml[0].startswith('/vsizip'):
            import zipfile
            parts = self.xml[0].split(os.path.sep)

            if parts[2] == '':
                parts[2] = os.path.sep

            zipname = os.path.join(*(parts[2:-3]))
            fname = os.path.join(*(parts[-3:]))

            zf = zipfile.ZipFile(zipname, 'r')
            xmlstr = zf.read(fname)
            zf.close()
        else:
            with open(self.xml[0],'r') as fid:
                xmlstr = fid.read()


        self._xml_root = ET.fromstring(xmlstr)
        numberBursts = self.getNumberOfBurstsFromAnnotation()

        ####Create empty burst SLCs
        for kk in range(numberBursts):
            slc = BurstSLC()
            slc.configure()
            slc.burstNumber = kk+1
            self.product.bursts.append(slc)
        
        self.product.numberOfBursts = numberBursts

        ####Populate processing software info
        if self.manifest is not None:
            self.populateIPFVersion()

        ####Populate common metadata
        self.populateCommonMetadata()

        ####Populate specific metadata
        self.populateBurstSpecificMetadata()

        ####Populate orbit information
        ###Try and locate an orbit file
        if self.orbitFile is None:
            if self.orbitDir is not None:
                self.orbitFile = s1_findOrbitFile(self.orbitDir,
                        self.product.bursts[0].sensingStart,
                        self.product.bursts[-1].sensingStop,
                        mission = self.product.mission)
        
        ####Read in the orbits
        if self.orbitFile:
            orb = self.extractPreciseOrbit()
        else:
            orb = self.extractOrbitFromAnnotation()

        for burst in self.product.bursts:
            if self.orbitFile:
                burst.orbit.setOrbitSource(os.path.basename(self.orbitFile))
            else:
                burst.orbit.setOrbitSource('Annotation')

            for sv in orb:
                burst.orbit.addStateVector(sv)


            ####Determine pass direction using Vz
            VV = burst.orbit.interpolateOrbit(burst.sensingMid, method='hermite').getVelocity()
            if VV[2] >= 0:
                burst.passDirection = 'ASCENDING'
            else:
                burst.passDirection = 'DESCENDING'


        ####If user provided a region of interest
        if len(self.regionOfInterest) != 0:
            self.crop(self.regionOfInterest)

        return

    def _parseMultiSlice(self):
        '''
        Responsible for parsing multiple slices meant to be stitched.
        '''
        
        slices = []
        relTimes = []
        burstWidths = []
        burstLengths = []

        for kk in range(self._numSlices):

            ###Create a new reader for one slice only
            aslice = Sentinel1()
            aslice.configure()

            ####Populate all the fields for reader
            aslice.xml = [self.xml[kk]]
            aslice.tiff = [self.tiff[kk]]
            aslice.manifest = self.manifest
            aslice.output = self.output
            aslice.orbitFile = self.orbitFile
            aslice.orbitDir = self.orbitDir
            aslice.regionOfInterest = self.regionOfInterest
            aslice.swathNumber = self.swathNumber
            aslice.parse()

            ####If there are any bursts left after cropping
            if aslice.product.numberOfBursts != 0:
                slices.append(aslice)
                relTimes.append((aslice.product.bursts[0].sensingStart - slices[0].product.bursts[0].sensingStart).total_seconds())
                burstWidths.append(aslice.product.bursts[0].numberOfSamples)
                burstLengths.append(aslice.product.bursts[0].numberOfLines)


        ####Update number of slices
        self._numSlices = len(slices)

        if self._numSlices == 0 :
            raise Exception('There is no imagery to extract. Check region of interest and inputs.')


        ####Estimate burstinterval
        reft0 = slices[0].product.bursts[0].sensingStart
        if len(slices[0].product.bursts) > 1:
            burstStartInterval = slices[0].product.bursts[1].sensingStart - reft0
        elif len(slices) > 1:
            burstStartInterval = slices[1].product.bursts[0].sensingStart - reft0
        else:
            raise Exception('Atleast 2 bursts must be present in the cropped region for TOPS processing.')


        self.burstWidth = max(burstWidths)
        self.burstLength = max(burstLengths)
        
        if self._numSlices == 1:  #If only one remains after crop
            self.product = slices[0].product
            self.product.numberOfBursts = len(self.product.bursts)
            self._tiffSrc = (self.product.numberOfBursts) * (slices[0].tiff)
            self._elevationAngleVsTau = slices[0]._elevationAngleVsTau
            return

        ####If there are multiple slices to combine
        print('Stitching {0} slices together'.format(self._numSlices))

        ###Sort slices by start times
        indices = np.argsort(relTimes)

        ####Start with the first slice
        firstSlice = slices[indices[0]]
        
        t0 = firstSlice.product.bursts[0].sensingStart

        for index in indices:
            aslice = slices[index]

            offset = np.int(np.rint((aslice.product.bursts[0].sensingStart - t0).total_seconds() / burstStartInterval.total_seconds()))

            for kk in range(aslice.product.numberOfBursts):
                #####Overwrite previous copy if one exists
                if (offset+kk) < len(self.product.bursts):
                    self.product.bursts[offset+kk] = aslice.product.bursts[kk]

                    ####Keep track of tiff src files
                    if len(self.tiff):
                        self._tiffSrc[offset+kk] = aslice.tiff[0]

                    if aslice.product.processingSoftwareVersion == '002.36':
                        self._elevationAngleVsTau[offset+kk] = aslice._elevationAngleVsTau[kk]

                elif (offset+kk) == len(self.product.bursts):
                    self.product.bursts.append(aslice.product.bursts[kk])
                    if len(self.tiff):
                        self._tiffSrc.append(aslice.tiff[0])

                    if aslice.product.processingSoftwareVersion == '002.36':
                       self._elevationAngleVsTau.append(aslice._elevationAngleVsTau[kk])
                else:
                    print('Offset indices = ', indices)
                    raise Exception('There appears to be a gap between slices. Cannot stitch them successfully.')

        self.product.numberOfBursts = len(self.product.bursts)
        self.product.processingSoftwareVersion = firstSlice.product.processingSoftwareVersion
        self.product.ascendingNodeTime = firstSlice.product.ascendingNodeTime
        return


    def getxmlattr(self, path, key):
        try:
            res = self._xml_root.find(path).attrib[key]
        except:
            raise Exception('Cannot find attribute %s at %s'%(key, path))

        return res

    def getxmlvalue(self, path):
        try:
            res = self._xml_root.find(path).text
        except:
            raise Exception('Tag= %s not found'%(path))

        if res is None:
            raise Exception('Tag = %s not found'%(path))

        return res

    def getxmlelement(self, path):
        try:
            res = self._xml_root.find(path)
        except:
            raise Exception('Cannot find path %s'%(path))

        if res is None:
            raise Exception('Cannot find path %s'%(path))

        return res

    def convertToDateTime(self, string):
        dt = datetime.datetime.strptime(string,"%Y-%m-%dT%H:%M:%S.%f")
        return dt

    def getNumberOfBurstsFromAnnotation(self):
        return int(self.getxmlattr('swathTiming/burstList', 'count'))
        
    
    def populateCommonMetadata(self):
        """
            Create metadata objects from the metadata files
        """
        ####Set each parameter one - by - one
        mission = self.getxmlvalue('adsHeader/missionId')
        swath = self.getxmlvalue('adsHeader/swath')
        polarization = self.getxmlvalue('adsHeader/polarisation')
        orbitnumber = int(self.getxmlvalue('adsHeader/absoluteOrbitNumber'))
        frequency = float(self.getxmlvalue('generalAnnotation/productInformation/radarFrequency'))
        passDirection = self.getxmlvalue('generalAnnotation/productInformation/pass')

        rangeSampleRate = float(self.getxmlvalue('generalAnnotation/productInformation/rangeSamplingRate'))
        rangePixelSize = Const.c/(2.0*rangeSampleRate)
        azimuthPixelSize = float(self.getxmlvalue('imageAnnotation/imageInformation/azimuthPixelSpacing'))
        azimuthTimeInterval = float(self.getxmlvalue('imageAnnotation/imageInformation/azimuthTimeInterval'))

        lines = int(self.getxmlvalue('swathTiming/linesPerBurst'))
        samples = int(self.getxmlvalue('swathTiming/samplesPerBurst'))
        
        slantRangeTime = float(self.getxmlvalue('imageAnnotation/imageInformation/slantRangeTime'))
        startingRange = float(self.getxmlvalue('imageAnnotation/imageInformation/slantRangeTime'))*Const.c/2.0
        incidenceAngle = float(self.getxmlvalue('imageAnnotation/imageInformation/incidenceAngleMidSwath'))
        steeringRate = np.radians(float( self.getxmlvalue('generalAnnotation/productInformation/azimuthSteeringRate')))


        prf = float(self.getxmlvalue('generalAnnotation/downlinkInformationList/downlinkInformation/prf'))
        terrainHeight = float(self.getxmlvalue('generalAnnotation/terrainHeightList/terrainHeight/value'))

        ####Sentinel is always right looking
        lookSide = -1

        ###Read ascending node for phase calibration
        ascTime = self.convertToDateTime(self.getxmlvalue('imageAnnotation/imageInformation/ascendingNodeTime'))


        ####Product parameters
        self.product.ascendingNodeTime = ascTime
        self.product.mission = mission
        self.product.spacecraftName = 'Sentinel-1'

        for index, burst in enumerate(self.product.bursts):
            burst.numberOfSamples = samples
            burst.numberOfLines = lines
            burst.startingRange = startingRange
            burst.trackNumber = (orbitnumber-73)%175 + 1  ###Appears to be standard for S1A
            burst.orbitNumber = orbitnumber 
            burst.frameNumber = 1  #S1A doesnt appear to have a frame system
            burst.polarization = polarization
            burst.swathNumber = int(swath.strip()[-1])
            burst.passDirection = passDirection
            burst.radarWavelength = Const.c / frequency
            burst.rangePixelSize = rangePixelSize
            burst.azimuthTimeInterval = azimuthTimeInterval
            burst.azimuthSteeringRate = steeringRate
            burst.prf = prf
            burst.terrainHeight = terrainHeight
            burst.rangeSamplingRate = rangeSampleRate

        return


    def populateBurstSpecificMetadata(self):
        '''
        Extract burst specific metadata from the xml file.
        '''
        
        burstList = self.getxmlelement('swathTiming/burstList')
        for index, burst in enumerate(burstList.getchildren()):
            bb = self.product.bursts[index]
            bb.sensingStart = self.convertToDateTime(burst.find('azimuthTime').text)
            deltaT = datetime.timedelta(seconds=(bb.numberOfLines - 1)*bb.azimuthTimeInterval)
            bb.sensingStop = bb.sensingStart + deltaT

            bb.burstStartUTC = self.convertToDateTime(burst.find('sensingTime').text)
            deltaT = datetime.timedelta(seconds=(bb.numberOfLines-1)/bb.prf)
            bb.burstStopUTC = bb.burstStartUTC + deltaT

            firstValidSample = [int(val) for val in burst.find('firstValidSample').text.split()]
            lastValidSample = [int(val) for val in burst.find('lastValidSample').text.split()]

            first=False
            last=False
            count=0
            for ii, val in enumerate(firstValidSample):
                if (val >= 0) and (not first):
                    first = True
                    bb.firstValidLine = ii

                if (val < 0) and (first) and (not last):
                    last = True
                    bb.numValidLines = ii - bb.firstValidLine
           
            lastLine = bb.firstValidLine + bb.numValidLines - 1

            bb.firstValidSample = max(firstValidSample[bb.firstValidLine], firstValidSample[lastLine])
            lastSample = min(lastValidSample[bb.firstValidLine], lastValidSample[lastLine])

            bb.numValidSamples = lastSample - bb.firstValidSample

        ####Read in fm rates separately
        fmrateList = self.getxmlelement('generalAnnotation/azimuthFmRateList')
        fmRates = []
        for index, burst in enumerate(fmrateList.getchildren()):
            r0 = 0.5 * Const.c * float(burst.find('t0').text)
            try:
                c0 = float(burst.find('c0').text)
                c1 = float(burst.find('c1').text)
                c2 = float(burst.find('c2').text)
                coeffs = [c0,c1,c2]
            except AttributeError:
                coeffs = [float(val) for val in burst.find('azimuthFmRatePolynomial').text.split()]

            refTime = self.convertToDateTime(burst.find('azimuthTime').text)
            poly = Poly1D.Poly1D()
            poly.initPoly(order=len(coeffs)-1)
            poly.setMean(r0)
            poly.setNorm(0.5*Const.c)
            poly.setCoeffs(coeffs)

            fmRates.append((refTime, poly))

        for index, burst in enumerate(self.product.bursts):

            dd = [ np.abs((burst.sensingMid - val[0]).total_seconds()) for val in fmRates]

            arg = np.argmin(dd)
            burst.azimuthFMRate = fmRates[arg][1]

#            print('FM rate matching: Burst %d to Poly %d'%(index, arg))



        dcList = self.getxmlelement('dopplerCentroid/dcEstimateList')
        dops = [ ]
        for index, burst in enumerate(dcList.getchildren()):

            r0 = 0.5 * Const.c* float(burst.find('t0').text)
            refTime = self.convertToDateTime(burst.find('azimuthTime').text)
            coeffs = [float(val) for val in burst.find('dataDcPolynomial').text.split()]
            poly = Poly1D.Poly1D()
            poly.initPoly(order=len(coeffs)-1)
            poly.setMean(r0)
            poly.setNorm(0.5*Const.c)
            poly.setCoeffs(coeffs)

            dops.append((refTime, poly))

        for index, burst in enumerate(self.product.bursts):

            dd = [np.abs((burst.sensingMid - val[0]).total_seconds()) for val in dops]
            
            arg = np.argmin(dd)
            burst.doppler = dops[arg][1]

#            print('Doppler matching: Burst %d to Poly %d'%(index, arg))

        ####Specifically for IPF 002.36
        if self.product.processingSoftwareVersion == '002.36':
            eapList = self.getxmlelement('antennaPattern/antennaPatternList')
            eaps = []
            
            for index, burst in enumerate(eapList.getchildren()):
                refTime = self.convertToDateTime(burst.find('azimuthTime').text)
                taus = [float(val) for val in burst.find('slantRangeTime').text.split()]
                angs = [float(val) for val in burst.find('elevationAngle').text.split()]
                eaps.append((refTime, (taus,angs)))

            for index, burst in enumerate(self.product.bursts):
                dd = [np.abs((burst.sensingMid - val[0]).total_seconds()) for val in eaps]
            
                arg = np.argmin(dd)
                self._elevationAngleVsTau.append(eaps[arg][1])



    def populateIPFVersion(self):
        '''
        Get IPF version from the manifest file.
        '''

        try:
            if self.manifest.startswith('/vsizip'):
                import zipfile
                parts = self.manifest.split(os.path.sep)
                if parts[2] == '':
                    parts[2] = os.path.sep
                zipname = os.path.join(*(parts[2:-2]))
                fname = os.path.join(*(parts[-2:]))
                print('MANS: ', zipname, fname)

                zf = zipfile.ZipFile(zipname, 'r')
                xmlstr = zf.read(fname)

            else:
                with open(self.manifest, 'r') as fid:
                    xmlstr = fid.read()

            ####Setup namespace
            nsp = "{http://www.esa.int/safe/sentinel-1.0}"

            root = ET.fromstring(xmlstr)

            elem = root.find('.//metadataObject[@ID="processing"]')

            rdict = elem.find('.//xmlData/' + nsp + 'processing/' + nsp + 'facility').attrib
            self.product.processingFacility = rdict['site'] +', '+ rdict['country']

            rdict = elem.find('.//xmlData/' + nsp + 'processing/' + nsp + 'facility/' + nsp + 'software').attrib

            self.product.processingSystem = rdict['name']
            self.product.processingSoftwareVersion = rdict['version']
            print('Setting IPF version to : ', self.product.processingSoftwareVersion) 

        except:   ###Not a critical error ... continuing
            print('Could not read version number successfully from manifest file: ', self.manifest)
            pass

        return


    def extractOrbitFromAnnotation(self):
        '''
        Extract orbit information from xml node.
        '''
        node = self._xml_root.find('generalAnnotation/orbitList')

        print('Extracting orbit from annotation XML file')
        frameOrbit = Orbit()
        frameOrbit.configure()

        for child in node.getchildren():
            timestamp = self.convertToDateTime(child.find('time').text)
            pos = []
            vel = []
            posnode = child.find('position')
            velnode = child.find('velocity')
            for tag in ['x','y','z']:
                pos.append(float(posnode.find(tag).text))

            for tag in ['x','y','z']:
                vel.append(float(velnode.find(tag).text))

            vec = StateVector()
            vec.setTime(timestamp)
            vec.setPosition(pos)
            vec.setVelocity(vel)
            frameOrbit.addStateVector(vec)


        #####Orbits provided in annotation files are not InSAR-grade
        #####These also need extensions for interpolation to work
        orbExt = OrbitExtender(planet=Planet(pname='Earth'))
        orbExt.configure()
        newOrb = orbExt.extendOrbit(frameOrbit)


        return newOrb
            
    def extractPreciseOrbit(self, margin=40.0):
        '''
        Extract precise orbit from given Orbit file.
        '''
        try:
            fp = open(self.orbitFile,'r')
        except IOError as strerr:
            print("IOError: %s" % strerr)
            return

        _xml_root = ET.ElementTree(file=fp).getroot()
       
        node = _xml_root.find('Data_Block/List_of_OSVs')

        print('Extracting orbit from Orbit File: ', self.orbitFile)
        orb = Orbit()
        orb.configure()

        margin = datetime.timedelta(seconds=margin)
        tstart = self.product.bursts[0].sensingStart - margin
        tend = self.product.bursts[-1].sensingStop + margin

        for child in node.getchildren():
            timestamp = self.convertToDateTime(child.find('UTC').text[4:])

            if (timestamp >= tstart) and (timestamp < tend):

                pos = [] 
                vel = []

                for tag in ['VX','VY','VZ']:
                    vel.append(float(child.find(tag).text))

                for tag in ['X','Y','Z']:
                    pos.append(float(child.find(tag).text))

                vec = StateVector()
                vec.setTime(timestamp)
                vec.setPosition(pos)
                vec.setVelocity(vel)
                orb.addStateVector(vec)

        fp.close()

        return orb

    def extractCalibrationPattern(self):
        '''
        Read the AUX CAL file for elevation angle antenna pattern.
        '''
        burst = self.product.bursts[0]
       
        Geap_IQ = None

        fp = open(self.auxFile,'r')
        xml_root = ET.ElementTree(file=fp).getroot()
        res = xml_root.find('calibrationParamsList/calibrationParams')
        paramsList = xml_root.find('calibrationParamsList')
        for par in (paramsList.getchildren()):
            if (par.find('swath').text.strip() == ('IW'+str(burst.swathNumber))) and (par.find('polarisation').text == burst.polarization):
              self._delta_theta = float(par.find('elevationAntennaPattern/elevationAngleIncrement').text)
              Geap_IQ = [float(val) for val in par.find('elevationAntennaPattern/values').text.split()]
        
        I = np.array(Geap_IQ[0::2])
        Q = np.array(Geap_IQ[1::2])
        self._Geap = I[:]+Q[:]*1j   # Complex vector of Elevation Antenna Pattern
        
        return

    def extractImage(self):
        """
           Use gdal python bindings to extract image
        """
        try:
            from osgeo import gdal
        except ImportError:
            raise Exception('GDAL python bindings not found. Need this for RSAT2/ TandemX / Sentinel1A.')

        if self.output is None:
            raise Exception('No output directory specified')

        if not self._parsed:
            self.parse()

        numberBursts = len(self.product.bursts)
        if (numberBursts == 0):
            raise Exception('No bursts to extract')

        if self.product.processingSoftwareVersion == '002.36':
            '''Range dependent correction needed.'''
       
            if self.auxFile is None:
                self.auxFile = s1_findAuxFile(self.auxDir,self.product.bursts[numberBursts//2].sensingMid,
                        mission = self.product.mission)

            if self.auxFile is None:
                print('******************************')
                print('Warning:  Strongly recommend using auxiliary information')
                print('          when using products generated with IPF 002.36')
                print('******************************')


        ####These get set if stitching multiple slices
        ####Slices can have different burst dimensions
        width = self._burstWidth
        length = self._burstLength

   
        ###If not specified, for single slice, use width and length from first burst
        if width is None:
            width = self.product.bursts[0].numberOfSamples

        if length is None:
            length = self.product.bursts[0].numberOfLines


        if os.path.isdir(self.output):
            print('Output directory exists. Overwriting ...')
#            os.rmdir(self.output)
        else:
            print('Creating directory {0} '.format(self.output))
            os.makedirs(self.output)

        for index, burst in enumerate(self.product.bursts):

            ####tiff for single slice
            if (len(self._tiffSrc) == 0) and (len(self.tiff)==1):
                src = gdal.Open(self.tiff[0], gdal.GA_ReadOnly)
            else: ##tiffSrc for multi slice
                src = gdal.Open(self._tiffSrc[index], gdal.GA_ReadOnly)

            band = src.GetRasterBand(1)

            outfile = os.path.join(self.output, 'burst_%02d'%(index+1) + '.slc')
            originalWidth = burst.numberOfSamples
            originalLength = burst.numberOfLines
            
            ###Write original SLC to file
            fid = open(outfile, 'wb')

            ####Use burstnumber to look into tiff file
            ####burstNumber still refers to original burst in slice
            lineOffset = (burst.burstNumber-1) * burst.numberOfLines

            ###Read whole burst for debugging. Only valid part is used.
            data = band.ReadAsArray(0, lineOffset, burst.numberOfSamples, burst.numberOfLines)

            ###Create output array and copy in valid part only
            ###Easier then appending lines and columns.
            outdata = np.zeros((length,width), dtype=np.complex64)
            outdata[burst.firstValidLine:burst.lastValidLine, burst.firstValidSample:burst.lastValidSample] =  data[burst.firstValidLine:burst.lastValidLine, burst.firstValidSample:burst.lastValidSample]

            ###################################################################################
            #Check if IPF version is 2.36 we need to correct for the Elevation Antenna Pattern 
            if (self.product.processingSoftwareVersion == '002.36') and (self.auxFile is not None):

                print('The IPF version is 2.36. Correcting the Elevation Antenna Pattern ...')

                self.extractCalibrationPattern()

                Geap = self.computeElevationAntennaPatternCorrection(burst, index)

                for i in range(burst.firstValidLine, burst.lastValidLine):
                    outdata[i, burst.firstValidSample:burst.lastValidSample] = outdata[i, burst.firstValidSample:burst.lastValidSample]/Geap[burst.firstValidSample:burst.lastValidSample]
            ########################

            outdata.tofile(fid)
            fid.close()
               
            #Updated width and length to match extraction
            burst.numberOfSamples = width
            burst.numberOfLines = length
            burst.burstNumber = index + 1

            ####Render ISCE XML
            slcImage = isceobj.createSlcImage()
            slcImage.setByteOrder('l')
            slcImage.setFilename(outfile)
            slcImage.setAccessMode('read')
            slcImage.setWidth(burst.numberOfSamples)
            slcImage.setLength(burst.numberOfLines)
            slcImage.setXmin(0)
            slcImage.setXmax(burst.numberOfSamples)
            slcImage.renderHdr()
            burst.image = slcImage 

            ####Release gdal pointers
            band = None
            src = None

        ####Dump the product
        pm = ProductManager()
        pm.configure()

        outxml = self.output
        if outxml.endswith('/'):
            outxml = outxml[:-1]

        pm.dumpProduct(self.product, os.path.join(outxml + '.xml'))

        return

    def computeAzimuthCarrier(self, burst, offset=0.0, position=None):
        '''
        Returns the ramp function as a numpy array.

        Straight from S1A documentation.
        '''

        ####Magnitude of velocity
        Vs = np.linalg.norm(burst.orbit.interpolateOrbit(burst.sensingMid, method='hermite').getVelocity())

        ####Steering rate component
        Ks =   2 * Vs * burst.azimuthSteeringRate / burst.radarWavelength 


        ####If user does not provide specific locations to compute ramp at.
        if position is None:
            rng = np.arange(burst.numberOfSamples) * burst.rangePixelSize + burst.startingRange

            eta =( np.arange(0, burst.numberOfLines) - (burst.numberOfLines//2)) * burst.azimuthTimeInterval +  offset * burst.azimuthTimeInterval

            f_etac = burst.doppler(rng)
            Ka     = burst.azimuthFMRate(rng)

            eta_ref = (burst.doppler(burst.startingRange) / burst.azimuthFMRate(burst.startingRange) ) - (f_etac / Ka)

            Kt = Ks / (1.0 - Ks/Ka)

            carr = np.pi * Kt[None,:] * ((eta[:,None] - eta_ref[None,:])**2)

        else:
            ####If user provides specific locations to compute ramp at.
            ####y and x need to be zero index
            y, x = position

            eta = (y - (burst.numberOfLines//2)) * burst.azimuthTimeInterval + offset * burst.azimuthTimeInterval
            rng = burst.startingRange + x * burst.rangePixelSize 
            f_etac = burst.doppler(rng)
            Ka  = burst.azimuthFMRate(rng)

            eta_ref = (burst.doppler(burst.startingRange) / burst.azimuthFMRate(burst.startingRange)) - (f_etac / Ka)
            
            Kt = Ks / (1.0 - Ks/Ka)

            carr = np.pi * Kt * ((eta - eta_ref)**2)

        return carr

    def computeElevationAntennaPatternCorrection(self,burst,index):
        '''
        Use scipy for antenna pattern interpolation.
        '''
        from scipy.interpolate import interp1d

        eta_anx = self.product.ascendingNodeTime        
        Ns = burst.numberOfSamples
        fs = burst.rangeSamplingRate
        eta_start = burst.sensingStart
        tau0 = 2 * burst.startingRange / Const.c

        tau_sub, theta_sub = self._elevationAngleVsTau[index]
        tau_sub = np.array(tau_sub)
        theta_sub = np.array(theta_sub)

        Nelt = np.shape(self._Geap)[0]
        #########################
        # Vector of elevation angle in antenna frame
        theta_AM = np.arange(-(Nelt-1.)/2,(Nelt-1.)/2+1)*self._delta_theta        
        ########################
        delta_anx = (eta_start - eta_anx).total_seconds()
         
        theta_offnadir = s1_anx2roll(delta_anx)
        theta_eap = theta_AM + theta_offnadir
        ########################
        #interpolate the 2-way complex EAP
        tau = tau0 + np.arange(Ns)/fs
        
        theta = np.interp(tau, tau_sub, theta_sub)
        
        f2 = interp1d(theta_eap,self._Geap)
        Geap_interpolated = f2(theta) 
        phi_EAP = np.angle(Geap_interpolated)
        cJ = np.complex64(1.0j)
        GEAP = np.exp(cJ * phi_EAP)
        return GEAP


    def computeRamp(self, burst, offset=0.0, position=None):
        '''
        Compute the phase ramp.
        '''
        cJ = np.complex64(1.0j)
        carr = self.computeAzimuthCarrier(burst,offset=offset, position=position)
        ramp = np.exp(-cJ * carr)
        return ramp

    def crop(self, bbox):
        '''
        Crop a given slice with a user provided bbox (SNWE).
        '''
    
        from iscesys.Component import createTraitSeq

        def overlap(box1,box2):
            '''
            Overlapping rectangles overlap both horizontally & vertically
            '''
            hoverlaps = True
            voverlaps = True

            if (box1[2] >= box2[3]) or (box1[3] <= box2[2]):
                hoverlaps = False

            if (box1[1] <= box2[0]) or (box1[0] >= box2[1]):
                voverlaps = False

            return hoverlaps and voverlaps


        cropList = createTraitSeq('burst')
        tiffList = []
        eapList = []

        print('Number of Bursts before cropping: ', len(self.product.bursts))

        ###For each burst
        for ind, burst in enumerate(self.product.bursts):
            burstBox = burst.getBbox()

            #####If it overlaps, keep the burst
            if overlap(burstBox, bbox):
                cropList.append(burst)
                if len(self._tiffSrc):
                    tiffList.append(self._tiffSrc[ind])
                if self.product.processingSoftwareVersion == '002.36':
                    eapList.append(self._elevationAngleVsTau[ind])

       
        ####Actual cropping

        self.product.bursts = cropList  #self.product.bursts[minInd:maxInd]
        self.product.numberOfBursts = len(self.product.bursts)

        self._tiffSrc = tiffList
        self._elevationAngleVsTau = eapList
        print('Number of Bursts after cropping: ', len(self.product.bursts))

        return

#################
'''
Sentinel-1A specific utilities.
'''
#################

def s1_findAuxFile(auxDir, timeStamp, mission='S1A'):
    '''
    Find appropriate auxiliary information file based on time stamps.
    '''

    if auxDir is None:
        return

    datefmt = "%Y%m%dT%H%M%S"
        
    match = []

    files = glob.glob(os.path.join(auxDir, mission+'_AUX_CAL_*'))
        
    ###List all orbit files
    for result in files:
        fields = result.split('_')
        taft = datetime.datetime.strptime(fields[-1][1:16], datefmt)
        tbef = datetime.datetime.strptime(fields[-2][1:16], datefmt)
                
        #####Get all files that span the acquisition
        if (tbef <= timeStamp) and (taft >= timeStamp):
            tmid = tbef + 0.5 * (taft - tbef)
            match.append((result, abs((timeStamp-tmid).total_seconds())))

    #####Return the file with the image is aligned best to the middle of the file
    if len(match) != 0:
        bestmatch = min(match, key = lambda x: x[1])
        return os.path.join(bestmatch[0], 'data', mission.lower()+'-aux-cal.xml')

       
    if len(match) == 0:
        print('******************************************')
        print('Warning: Aux file requested but no suitable auxiliary file found.')
        print('******************************************')

    return None

def s1_findOrbitFile(orbitDir, tstart, tstop, mission='S1A'):
    '''
    Find correct orbit file in the orbit directory.
    '''

    datefmt = "%Y%m%dT%H%M%S"
    types = ['POEORB', 'RESORB']
    match = []

    timeStamp = tstart + 0.5 * (tstop - tstart)

    for orbType in types:
        files = glob.glob( os.path.join(orbitDir, mission+'_OPER_AUX_' + orbType + '_OPOD*'))
            
        ###List all orbit files
        for result in files:
            fields = result.split('_')
            taft = datetime.datetime.strptime(fields[-1][0:15], datefmt)
            tbef = datetime.datetime.strptime(fields[-2][1:16], datefmt)
                
            #####Get all files that span the acquisition
            if (tbef <= tstart) and (taft >= tstop):
                tmid = tbef + 0.5 * (taft - tbef)
                match.append((result, abs((timeStamp-tmid).total_seconds())))

        #####Return the file with the image is aligned best to the middle of the file
        if len(match) != 0:
            bestmatch = min(match, key = lambda x: x[1])
            return bestmatch[0]

       
    if len(match) == 0:
        raise Exception('No suitable orbit file found. If you want to process anyway - unset the orbitdir parameter')

    return



def s1_anx2roll(delta_anx):
    '''
    Returns the Platform nominal roll as function of elapsed time from
    ascending node crossing time (ANX).

    Straight from S1A documentation.
    '''
   
    ####Estimate altitude based on time elapsed since ANX
    altitude = s1_anx2Height(delta_anx)

    ####Reference altitude 
    href=711.700 #;km

    ####Reference boresight at reference altitude
    boresight_ref= 29.450 # ; deg

    ####Partial derivative of roll vs altitude
    alpha_roll = 0.0566 # ;deg/km

    ####Estimate nominal roll
    nominal_roll = boresight_ref - alpha_roll* (altitude/1000.0 - href)  #Theta off nadir

    return nominal_roll

def s1_anx2Height(delta_anx):
    '''
    Returns the platform nominal height as function of elapse time from
    ascending node crossing time (ANX).

    Straight from S1A documention.
    '''
  
    ###Average height
    h0 = 707714.8  #;m

    ####Perturbation amplitudes
    h = np.array([8351.5, 8947.0, 23.32, 11.74]) #;m

    ####Perturbation phases
    phi = np.array([3.1495, -1.5655 , -3.1297, 4.7222]) #;radians

    ###Orbital time period in seconds
    Torb = (12*24*60*60)/175.

    ###Angular velocity
    worb = 2*np.pi / Torb

    ####Evaluation of series 
    ht=h0
    for i in range(len(h)):
        ht += h[i] * np.sin((i+1) * worb * delta_anx + phi[i])

    return ht
 




if __name__ == '__main__':

    main()
