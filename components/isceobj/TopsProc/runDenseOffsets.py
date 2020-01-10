#
# Author: Joshua Cohen
# Copyright 2016
# Based on Piyush Agram's denseOffsets.py script
#

import os
import isce
import isceobj
import logging

from mroipac.ampcor.DenseAmpcor import DenseAmpcor
from isceobj.Util.decorators import use_api

logger = logging.getLogger('isce.insar.DenseOffsets')

@use_api
def runDenseOffsets(self):
    '''
    Estimate dense offset field between merged master bursts and slave bursts.
    '''

    print('\n============================================================')
    print('Configuring DenseAmpcor object for processing...\n')

    ### Determine appropriate filenames
    mf = 'master.slc'
    sf = 'slave.slc'
    if not ((self.numberRangeLooks == 1) and (self.numberAzimuthLooks==1)):
        mf += '.full'
        sf += '.full'
    master = os.path.join(self._insar.mergedDirname, mf)
    slave = os.path.join(self._insar.mergedDirname, sf)

    ### Load the master object
    m = isceobj.createSlcImage()
    m.load(master + '.xml')
    m.setAccessMode('READ')
    m.createImage()

    ### Load the slave object
    s = isceobj.createSlcImage()
    s.load(slave + '.xml')
    s.setAccessMode('READ')
    s.createImage()
    
    width = m.getWidth()
    length = m.getLength()

    objOffset = DenseAmpcor(name='dense')
    objOffset.configure()

    ### Configure dense Ampcor object
    print('\nMaster frame: %s' % (mf))
    print('Slave frame: %s' % (sf))
    print('Main window size width: %02d' % (self.winwidth))
    print('Main window size height: %02d' % (self.winhgt))
    print('Search window size width: %02d' % (self.srcwidth))
    print('Search window size height: %02d' % (self.srchgt))
    print('Skip sample across: %02d' % (self.skipwidth))
    print('Skip sample down: %02d' % (self.skiphgt))
    print('Field margin: %02d' % (self.margin))
    print('Oversampling factor: %02d' % (self.oversample))
    print('Gross offset across: %02d' % (self.rgshift))
    print('Gross offset down: %02d\n' % (self.azshift))

    objOffset.setWindowSizeWidth(self.winwidth)
    objOffset.setWindowSizeHeight(self.winhgt)
    objOffset.setSearchWindowSizeWidth(self.srcwidth)
    objOffset.setSearchWindowSizeHeight(self.srchgt)
    objOffset.skipSampleAcross = self.skipwidth
    objOffset.skipSampleDown = self.skiphgt
    objOffset.margin = self.margin
    objOffset.oversamplingFactor = self.oversample
    objOffset.setAcrossGrossOffset(self.rgshift)
    objOffset.setDownGrossOffset(self.azshift)
    
    objOffset.setFirstPRF(1.0)
    objOffset.setSecondPRF(1.0)
    if m.dataType.startswith('C'):
        objOffset.setImageDataType1('mag')
    else:
        objOffset.setImageDataType1('real')
    if s.dataType.startswith('C'):
        objOffset.setImageDataType2('mag')
    else:
        objOffset.setImageDataType2('real')

    outprefix = os.path.join(self._insar.mergedDirname, self.offsetfile)
    objOffset.offsetImageName = outprefix + '.bil'
    objOffset.snrImageName = outprefix + '_snr.bil'
    print('Output dense offsets file name: %s' % (objOffset.offsetImageName))
    print('Output SNR file name: %s' % (objOffset.snrImageName))
    print('\n======================================')
    print('Running dense ampcor...')
    print('======================================\n')
    
    objOffset.denseampcor(m, s) ### Where the magic happens...

    ### Store params for later
    self.offset_width = objOffset.offsetCols
    self.offset_length = objOffset.offsetLines
    self.offset_top = objOffset.locationDown[0][0]
    self.offset_left = objOffset.locationAcross[0][0]

    m.finalizeImage()
    s.finalizeImage()


if __name__ == '__main__' :
    '''
    Default routine to plug master.slc.full/slave.slc.full into
    Dense Offsets Ampcor module.
    '''

    main()
