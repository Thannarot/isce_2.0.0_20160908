#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# copyright: 2013 to the present, california institute of technology.
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
# Authors: Kosal Khun, Marco Lavalle
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~



# Comment: Adapted from InsarProc/runPulseTiming.py
import datetime
import isceobj
import logging

from isceobj.Orbit.Orbit import Orbit

logger = logging.getLogger('isce.isceProc.runPulseTiming')


def runPulseTiming(self):
    for sceneid in self._isce.selectedScenes:
        self._isce.orbits[sceneid] = {}
        self._isce.shifts[sceneid] = {}
        for pol in self._isce.selectedPols:
            frame = self._isce.frames[sceneid][pol]
            catalog = isceobj.Catalog.createCatalog(self._isce.procDoc.name)
            sid = self._isce.formatname(sceneid, pol)
            orbit, shift = run(frame, catalog=catalog, sceneid=sid) ##calls pulsetiming
            self._isce.procDoc.addAllFromCatalog(catalog)
            self._isce.orbits[sceneid][pol] = orbit ##add orbits to main object
            self._isce.shifts[sceneid][pol] = shift ##add shifts to main object
        if self.azShiftPixels is None: ##not given by user
            minst = min(self._isce.shifts[sceneid].values())
            for pol, st in self._isce.shifts[sceneid].items():
                self._isce.shifts[sceneid][pol] = minst - st
        else: ##if given, we assume that it applies only to vh and vv
            for pol in ['hh', 'hv']:
                self._isce.shifts[sceneid][pol] = 0
            for pol in ['vh', 'vv']:
                self._isce.shifts[sceneid][pol] = float(self.azShiftPixels)



def run(frame, catalog=None, sceneid='NO_ID'):
    """
    Interpolate orbit.
    """
    logger.info("Pulse Timing: %s" % sceneid)
    numberOfLines = frame.getNumberOfLines()
    prf = frame.getInstrument().getPulseRepetitionFrequency()
    pri = 1.0 / prf
    startTime = frame.getSensingStart()
    orbit = frame.getOrbit()
    pulseOrbit = Orbit()
    startTimeUTC0 = (startTime -
                     datetime.datetime(startTime.year,
                                       startTime.month,startTime.day)
                     )
    timeVec = [pri*i +
               startTimeUTC0.seconds +
               10**-6*startTimeUTC0.microseconds for i in range(numberOfLines)
               ]
    if catalog is not None:
        catalog.addItem("timeVector", timeVec, "runPulseTiming.%s" % sceneid)
    for i in range(numberOfLines):
        dt = i * pri
        time = startTime + datetime.timedelta(seconds=dt)
        sv = orbit.interpolateOrbit(time, method='hermite')
        pulseOrbit.addStateVector(sv)
    shift = timeVec[0] * prf
    return pulseOrbit, shift
