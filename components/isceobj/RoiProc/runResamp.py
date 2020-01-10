#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# copyright: 2012 to the present, california institute of technology.
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
# Author: Brett George
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~



import logging
import stdproc
import isceobj
from isceobj import Constants as CN
from iscesys.ImageUtil.ImageUtil import ImageUtil as IU

logger = logging.getLogger('isce.insar.runResamp')

def runResamp(self):
    logger.info("Resampling interferogram")

    imageSlc1 =  self.insar.formSLC1.slcImage
    imageSlc2 =  self.insar.formSLC2.slcImage
    

    resampName = self.insar.resampImageName
    resampAmp = resampName + '.amp'
    resampInt = resampName + '.int'

    azLooks = self.insar.numberAzimuthLooks
    rLooks = self.insar.numberRangeLooks               

    objSlc1 = isceobj.createSlcImage()
    IU.copyAttributes(imageSlc1, objSlc1)
    objSlc1.setAccessMode('read')
    objSlc1.createImage()

    objSlc2 = isceobj.createSlcImage()
    IU.copyAttributes(imageSlc2,  objSlc2)
    objSlc2.setAccessMode('read')
    objSlc2.createImage()

    #slcWidth = max(imageSlc1.getWidth(), imageSlc2.getWidth())
    slcWidth = imageSlc1.getWidth()
    intWidth = int(slcWidth / rLooks)
    dataType = 'CFLOAT'

    objInt = isceobj.createIntImage()
    objInt.setFilename(resampInt)
    objInt.setWidth(intWidth)
    imageInt = isceobj.createIntImage()
    IU.copyAttributes(objInt, imageInt)

    objInt.setAccessMode('write')

    objInt.createImage()
    objAmp = isceobj.createAmpImage()
    objAmp.setFilename(resampAmp)
    objAmp.setWidth(intWidth)
    imageAmp = isceobj.createAmpImage()
    IU.copyAttributes(objAmp, imageAmp)
    
    objAmp.setAccessMode('write')
    objAmp.createImage()

    self.insar.resampIntImage = imageInt
    self.insar.resampAmpImage = imageAmp

    
    instrument = self.insar.masterFrame.getInstrument()
    
    offsetField = self.insar.refinedOffsetField                
    
    lines = self.insar.numberResampLines
   
    ####Modified to deal with slave PRF correctly
#    dopplerCoeff = self.insar.dopplerCentroid.getDopplerCoefficients(inHz=True)
    dopplerCoeff = self.insar.slaveFrame._dopplerVsPixel
    for num in range(len(dopplerCoeff)):
        dopplerCoeff[num] /= self.insar.slaveFrame.getInstrument().getPulseRepetitionFrequency()

    numFitCoeff = self.insar.numberFitCoefficients
    
#    pixelSpacing = self.insar.slantRangePixelSpacing
    fS = self._insar.getSlaveFrame().getInstrument().getRangeSamplingRate()
    pixelSpacing = CN.SPEED_OF_LIGHT/(2.*fS) 

    objResamp = stdproc.createResamp()
    objResamp.setNumberLines(lines) 
    objResamp.setNumberFitCoefficients(numFitCoeff)
    objResamp.setNumberAzimuthLooks(azLooks)
    objResamp.setNumberRangeLooks(rLooks)
    objResamp.setSlantRangePixelSpacing(pixelSpacing)
    objResamp.setDopplerCentroidCoefficients(dopplerCoeff)

    objResamp.wireInputPort(name='offsets', object=offsetField)
    objResamp.wireInputPort(name='instrument', object=instrument)
    #set the tag used in the outfile. each message is precided by this tag
    #is the writer is not of "file" type the call has no effect
    objResamp.stdWriter = self._writer_set_file_tags("resamp", "log", "err", 
                                               "out")
#    objResamp.flattenWithOffsetFlag = 1
    objResamp.resamp(objSlc1, objSlc2, objInt, objAmp) 
    # Record the inputs and outputs
    from isceobj.Catalog import recordInputsAndOutputs
    recordInputsAndOutputs(self._insar.procDoc, objResamp, "runResamp",
                  logger, "runResamp")
    
    objInt.finalizeImage()
    objAmp.finalizeImage()
    objSlc1.finalizeImage()
    objSlc2.finalizeImage()

    return None
