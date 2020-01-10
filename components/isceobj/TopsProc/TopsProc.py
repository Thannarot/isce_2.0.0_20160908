#
# Author: Piyush Agram
# Copyright 2016
#

import os
import logging
import logging.config
from iscesys.Component.Component import Component
from iscesys.DateTimeUtil.DateTimeUtil import DateTimeUtil as DTU
from iscesys.Compatibility import Compatibility


MASTER_SLC_PRODUCT = Component.Parameter('masterSlcProduct',
                                public_name='master slc product',
                                default='master',
                                type=str,
                                mandatory=False,
                                doc='Directory name of the master SLC product')


SLAVE_SLC_PRODUCT = Component.Parameter('slaveSlcProduct',
                                public_name='slave slc product',
                                default='slave',
                                type=str,
                                mandatory=False,
                                doc='Directory name of the slave SLC product')

COMMON_BURST_START_MASTER_INDEX  = Component.Parameter('commonBurstStartMasterIndex',
                                public_name = 'common burst start master index',
                                default = None,
                                type = int,
                                mandatory = False,
                                doc = 'Master burst start index for common bursts')

COMMON_BURST_START_SLAVE_INDEX = Component.Parameter('commonBurstStartSlaveIndex',
                                public_name = 'common burst start slave index',
                                default = None,
                                type = int,
                                mandatory = False,
                                doc = 'Slave burst start index for common bursts')

NUMBER_COMMON_BURSTS = Component.Parameter('numberOfCommonBursts',
                                public_name = 'number of common bursts',
                                default = None,
                                type = int,
                                mandatory = False,
                                doc = 'Number of common bursts between slave and master')


DEM_FILENAME = Component.Parameter('demFilename',
                                public_name='dem image name',
                                default = None,
                                type = str,
                                mandatory = False,
                                doc = 'Name of the dem file')

GEOMETRY_DIRNAME = Component.Parameter('geometryDirname',
                                public_name='geometry directory name',
                                default='geom_master',
                                type=str,
                                mandatory=False, 
                                doc = 'Geometry directory')

ESD_DIRNAME = Component.Parameter('esdDirname',
                                public_name = 'ESD directory name',
                                default = 'ESD',
                                type = str,
                                mandatory = False,
                                doc = 'ESD directory')


COARSE_OFFSETS_DIRECTORY = Component.Parameter('coarseOffsetsDirname',
                                public_name = 'coarse offsets directory name',
                                default = 'coarse_offsets',
                                type = str,
                                mandatory = False,
                                doc = 'coarse offsets directory name')

COARSE_COREG_DIRECTORY = Component.Parameter('coarseCoregDirname',
                                public_name = 'coarse coreg directory name',
                                default = 'coarse_coreg',
                                type = str,
                                mandatory = False,
                                doc = 'coarse coregistered slc directory name')

COARSE_IFG_DIRECTORY = Component.Parameter('coarseIfgDirname',
                                public_name = 'coarse interferogram directory name',
                                default = 'coarse_interferogram',
                                type = str,
                                mandatory = False,
                                doc = 'Coarse interferogram directory')


FINE_OFFSETS_DIRECTORY = Component.Parameter('fineOffsetsDirname',
                                public_name = 'fine offsets directory name',
                                default = 'fine_offsets',
                                type = str,
                                mandatory = False,
                                doc = 'fine offsets directory name')

FINE_COREG_DIRECTORY = Component.Parameter('fineCoregDirname',
                                public_name = 'fine coreg directory name',
                                default = 'fine_coreg',
                                type = str,
                                mandatory = False,
                                doc = 'fine coregistered slc directory name')

FINE_IFG_DIRECTORY = Component.Parameter('fineIfgDirname',
                                public_name = 'fine interferogram directory name',
                                default = 'fine_interferogram',
                                type = str,
                                mandatory = False,
                                doc = 'Fine interferogram directory')

MERGED_DIRECTORY = Component.Parameter('mergedDirname',
                                public_name = 'merged products directory name',
                                default = 'merged',
                                type = str,
                                mandatory = False,
                                doc = 'Merged product directory')

OVERLAPS_SUBDIRECTORY = Component.Parameter('overlapsSubDirname',
                                public_name = 'overlaps subdirectory name',
                                default = 'overlaps',
                                type = str,
                                mandatory = False,
                                doc = 'Overlap region processing directory')

SLAVE_RANGE_CORRECTION = Component.Parameter('slaveRangeCorrection',
                                public_name = 'slave range correction',
                                default = 0.0,
                                type = float,
                                mandatory = False,
                                doc = 'Range correction in m to apply to slave')

SLAVE_TIMING_CORRECTION = Component.Parameter('slaveTimingCorrection',
                                public_name = 'slave timing correction',
                                default = 0.0,
                                type = float,
                                mandatory = False,
                                doc = 'Timing correction in secs to apply to slave')

APPLY_WATER_MASK = Component.Parameter(
    'applyWaterMask',
    public_name='apply water mask',
    default=True,
    type=bool,
    mandatory=False,
    doc='Flag to apply water mask to images before unwrapping.'
)

WATER_MASK_FILENAME = Component.Parameter(
    'waterMaskFileName',
    public_name='water mask file name',
    default='waterMask.msk',
    type=str,
    mandatory=False,
    doc='Filename of the water body mask image in radar coordinate cropped to the interferogram size.'
)


MERGED_IFG_NAME = Component.Parameter(
    'mergedIfgname',
    public_name='merged interferogram name',
    default='topophase.flat',
    type=str,
    mandatory=False,
    doc='Filename of the merged interferogram.'
)


MERGED_LOS_NAME = Component.Parameter(
        'mergedLosName',
        public_name = 'merged los name',
        default = 'los.rdr',
        type = str,
        mandatory = False,
        doc = 'Merged los file name')


COHERENCE_FILENAME = Component.Parameter('coherenceFilename',
                                         public_name='coherence name',
                                         default='phsig.cor',
                                         type=str,
                                         mandatory=False,
                                         doc='Coherence file name')

CORRELATION_FILENAME = Component.Parameter('correlationFilename',
                                        public_name='correlation name',
                                        default='topophase.cor',
                                        type=str,
                                        mandatory=False,
                                        doc='Correlation file name')

FILTERED_INT_FILENAME = Component.Parameter('filtFilename',
                                        public_name = 'filtered interferogram name',
                                        default = 'filt_topophase.flat',
                                        type = str,
                                        mandatory = False,
                                        doc = 'Filtered interferogram filename')


UNWRAPPED_INT_FILENAME = Component.Parameter('unwrappedIntFilename',
                                             public_name='unwrapped interferogram filename',
                                             default='filt_topophase.unw',
                                             type=str,
                                             mandatory=False,
                                             doc='')

UNWRAPPED_2STAGE_FILENAME = Component.Parameter('unwrapped2StageFilename',
                                             public_name='unwrapped 2Stage filename',
                                             default='filt_topophase_2stage.unw',
                                             type=str,
                                             mandatory=False,
                                             doc='Output File name of 2Stage unwrapper')

CONNECTED_COMPONENTS_FILENAME = Component.Parameter(
    'connectedComponentsFilename',
    public_name='connected component filename',
    default=None,
    type=str,
    mandatory=False,
    doc=''
)

DEM_CROP_FILENAME = Component.Parameter('demCropFilename',
                                        public_name='dem crop file name',
                                        default='dem.crop',
                                        type=str,
                                        mandatory=False,
                                        doc='')


GEOCODE_LIST = Component.Parameter('geocode_list',
    public_name='geocode list',
    default=[COHERENCE_FILENAME,
             CORRELATION_FILENAME,
             UNWRAPPED_INT_FILENAME,
             MERGED_LOS_NAME,
             MERGED_IFG_NAME,
             FILTERED_INT_FILENAME,
             UNWRAPPED_2STAGE_FILENAME,
             ],
    container=list,
    type=str,
    mandatory=False,
    doc='List of files to geocode'
)
UNMASKED_PREFIX = Component.Parameter('unmaskedPrefix',
                                   public_name='unmasked filename prefix',
                                   default='unmasked',
                                   type=str,
                                   mandatory=False,
                                   doc='Prefix prepended to the image filenames that have not been water masked')



class TopsProc(Component):
    """
    This class holds the properties, along with methods (setters and getters)
    to modify and return their values.
    """

    parameter_list = (MASTER_SLC_PRODUCT,
                      SLAVE_SLC_PRODUCT,
                      COMMON_BURST_START_MASTER_INDEX,
                      COMMON_BURST_START_SLAVE_INDEX,
                      NUMBER_COMMON_BURSTS,
                      DEM_FILENAME,
                      GEOMETRY_DIRNAME,
                      COARSE_OFFSETS_DIRECTORY,
                      COARSE_COREG_DIRECTORY,
                      COARSE_IFG_DIRECTORY,
                      FINE_OFFSETS_DIRECTORY,
                      FINE_COREG_DIRECTORY,
                      FINE_IFG_DIRECTORY,
                      OVERLAPS_SUBDIRECTORY,
                      SLAVE_RANGE_CORRECTION,
                      SLAVE_TIMING_CORRECTION,
                      ESD_DIRNAME,
                      APPLY_WATER_MASK,
                      WATER_MASK_FILENAME,
                      MERGED_DIRECTORY,
                      MERGED_IFG_NAME,
                      MERGED_LOS_NAME,
                      COHERENCE_FILENAME,
                      FILTERED_INT_FILENAME,
                      UNWRAPPED_INT_FILENAME,
                      UNWRAPPED_2STAGE_FILENAME,
                      CONNECTED_COMPONENTS_FILENAME,
                      DEM_CROP_FILENAME,
                      GEOCODE_LIST,
                      UNMASKED_PREFIX,
                      CORRELATION_FILENAME)

    facility_list = ()


    family='topscontext'

    def __init__(self, name='', procDoc=None):
        #self.updatePrivate()

        super().__init__(family=self.__class__.family, name=name)
        self.procDoc = procDoc
        return None

    def _init(self):
        """
        Method called after Parameters are configured.
        Determine whether some Parameters still have unresolved
        Parameters as their default values and resolve them.
        """

        #Determine whether the geocode_list still contains Parameters
        #and give those elements the proper value.  This will happen
        #whenever the user doesn't provide as input a geocode_list for
        #this component.

        mergedir  = self.mergedDirname
        for i, x in enumerate(self.geocode_list):
            if isinstance(x, Component.Parameter):
                y = getattr(self, getattr(x, 'attrname'))
                self.geocode_list[i] = os.path.join(mergedir, y)
        return


    def loadProduct(self, xmlname):
        '''
        Load the product using Product Manager.
        '''

        from iscesys.Component.ProductManager import ProductManager as PM

        pm = PM()
        pm.configure()

        obj = pm.loadProduct(xmlname)

        return obj


    def saveProduct(self, obj, xmlname):
        '''
        Save the product to an XML file using Product Manager.
        '''
        
        from iscesys.Component.ProductManager import ProductManager as PM

        pm = PM()
        pm.configure()

        pm.dumpProduct(obj, xmlname)
        
        return None

    @property
    def masterSlcTopOverlapProduct(self):
        return self.masterSlcProduct + '_top'

    @property
    def masterSlcBottomOverlapProduct(self):
        return self.masterSlcProduct + '_bottom'

    @property
    def coregTopOverlapProduct(self):
        return self.coarseCoregDirname + '_top'

    @property
    def coregBottomOverlapProduct(self):
        return self.coarseCoregDirname + '_bottom'

    @property
    def coarseIfgTopOverlapProduct(self):
        return self.coarseIfgDirname + '_top'

    @property
    def coarseIfgBottomOverlapProduct(self):
        return self.coarseIfgDirname + '_bottom'

    @property
    def commonMasterBurstLimits(self):
        return (self.commonBurstStartMasterIndex, self.commonBurstStartMasterIndex + self.numberOfCommonBursts)

    @property
    def commonSlaveBurstLimits(self):
        return (self.commonBurstStartSlaveIndex, self.commonBurstStartSlaveIndex + self.numberOfCommonBursts)
