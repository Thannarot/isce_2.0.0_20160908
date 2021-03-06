c~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
c copyright: 2010 to the present, california institute of technology.
c all rights reserved. united states government sponsorship acknowledged.
c any commercial use must be negotiated with the office of technology transfer
c at the california institute of technology.
c 
c this software may be subject to u.s. export control laws. by accepting this
c software, the user agrees to comply with all applicable u.s. export laws and
c regulations. user has the responsibility to obtain export licenses,  or other
c export authority as may be required before exporting such information to
c foreign countries or providing access to foreign persons.
c 
c installation and use of this software is restricted by a license agreement
c between the licensee and the california institute of technology. it is the
c user's responsibility to abide by the terms of the license agreement.
c
c Author: Giangi Sacco
c~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~





        subroutine allocate_sch(dim1,dim2)
            use formslcStateSoi
            implicit none
            integer dim1,dim2
            dim1_sch = dim2
            dim2_sch = dim1
            allocate(sch(dim2,dim1)) 
        end

        subroutine deallocate_sch()
            use formslcStateSoi
            deallocate(sch) 
        end

        subroutine allocate_vsch(dim1,dim2)
            use formslcStateSoi
            implicit none
            integer dim1,dim2
            dim1_vsch = dim2
            dim2_vsch = dim1
            allocate(vsch(dim2,dim1))
        end

        subroutine deallocate_vsch()
            use formslcStateSoi
            deallocate(vsch)
        end

        subroutine allocate_time(dim1)
            use formslcStateSoi
            implicit none
            integer dim1
            dim1_time = dim1
            allocate(time(dim1)) 
        end

        subroutine deallocate_time()
            use formslcStateSoi
            deallocate(time) 
        end

        subroutine allocate_dopplerCoefficients(dim1)
            use formslcStateSoi
            implicit none
            integer dim1
            dim1_dopplerCoefficients = dim1
            allocate(dopplerCoefficients(dim1)) 
        end

        subroutine deallocate_dopplerCoefficients()
            use formslcStateSoi
            deallocate(dopplerCoefficients) 
        end

