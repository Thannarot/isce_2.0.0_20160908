#
# Author: Piyush Agram
# Copyright 2016
#

import logging
import isceobj
import mroipac
from mroipac.baseline.Baseline import Baseline
logger = logging.getLogger('isce.topsinsar.runPreprocessor')

def runPreprocessor(self):
    '''Extract images.
    '''

    catalog = isceobj.Catalog.createCatalog(self._insar.procDoc.name)

    master = extract_slc(self.master)
    self._insar.masterSlcProduct = master

    catalog.addInputsFrom(self.master.product, 'master.sensor')
    catalog.addItem('burstWidth', self.master.product.bursts[0].numberOfSamples, 'master')
    catalog.addItem('burstLength', self.master.product.bursts[0].numberOfLines, 'master')

    slave = extract_slc(self.slave)
    self._insar.slaveSlcProduct = slave




    catalog.addInputsFrom(self.slave.product, 'slave.sensor')
    catalog.addItem('burstWidth', self.slave.product.bursts[0].numberOfSamples, 'slave')
    catalog.addItem('burstLength', self.slave.product.bursts[0].numberOfLines, 'slave')

    catalog.printToLog(logger, "runPreprocessor")
    self._insar.procDoc.addAllFromCatalog(catalog)

def extract_slc(sensor):
    sensor.configure()
    sensor.extractImage()
   
    return sensor.output

