!~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
! copyright: 2010 to the present, california institute of technology.
! all rights reserved. united states government sponsorship acknowledged.
! any commercial use must be negotiated with the office of technology transfer
! at the california institute of technology.
! 
! this software may be subject to u.s. export control laws. by accepting this
! software, the user agrees to comply with all applicable u.s. export laws and
! regulations. user has the responsibility to obtain export licenses,  or other
! export authority as may be required before exporting such information to
! foreign countries or providing access to foreign persons.
! 
! installation and use of this software is restricted by a license agreement
! between the licensee and the california institute of technology. it is the
! user's responsibility to abide by the terms of the license agreement.
!
! Author: Giangi Sacco
!~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~





        subroutine setEllipsoidMajorSemiAxis(varInt)
            use geo2rdrState
            implicit none
            double precision varInt
            majorSemiAxis = varInt
        end subroutine

        subroutine setEllipsoidEccentricitySquared(varInt)
            use geo2rdrState
            implicit none
            double precision varInt
            eccentricitySquared = varInt
        end subroutine

        subroutine setRangePixelSpacing(varInt)
            use geo2rdrState
            implicit none
            real*8 varInt
            drho = varInt
        end subroutine

        subroutine setLookSide(varInt)
            use geo2rdrState
            implicit none
            integer varInt
            ilrl = varInt
        end subroutine

        subroutine setRangeFirstSample(varInt)
            use geo2rdrState
            implicit none
            double precision varInt
            rho0 = varInt
        end subroutine

        subroutine setDopplerAccessor(varInt)
            use geo2rdrState
            implicit none
            type(poly1dType) ::  varInt
            dopAcc = varInt
        end subroutine

        subroutine setPRF(varInt)
            use geo2rdrState
            implicit none
            real*8 varInt
            prf = varInt
        end subroutine

        subroutine setRadarWavelength(varInt)
            use geo2rdrState
            implicit none
            real*8 varInt
            wvl = varInt
        end subroutine

        subroutine setSensingStart(varInt)
            use geo2rdrState
            implicit none
            double precision varInt
            t0 = varInt
        end subroutine

        subroutine setLength(varInt)
            use geo2rdrState
            implicit none
            integer varInt
            length = varInt
        end subroutine

        subroutine setWidth(varInt)
            use geo2rdrState
            implicit none
            integer varInt
            width = varInt
        end subroutine

        subroutine setDemWidth(varInt)
            use geo2rdrState
            implicit none
            integer varInt
            demwidth = varInt
        end subroutine

        subroutine setDemLength(varInt)
            use geo2rdrState
            implicit none
            integer varInt
            demlength = varInt
        end subroutine

        subroutine setOrbit(corb)
            use geo2rdrState
            implicit none
            type(orbitType):: corb
            orbit = corb
        end subroutine

        subroutine setNumberRangeLooks(varInt)
            use geo2rdrState
            implicit none
            integer :: varInt
            Nrnglooks = varInt
        end subroutine

        subroutine setNumberAzimuthLooks(varInt)
            use geo2rdrState
            implicit none
            integer :: varInt
            Nazlooks = varInt
        end subroutine

        subroutine setBistaticFlag(varInt)
            use geo2rdrState
            implicit none
            integer :: varInt

            if (varInt .eq. 0) then
                bistatic = .False.
            else
                bistatic = .True.
            endif
        end subroutine

        subroutine setOrbitMethod(varInt)
            use geo2rdrState
            implicit none
            integer :: varInt

            orbitMethod = varInt
        end subroutine
