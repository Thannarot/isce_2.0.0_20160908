#include "typedef_UWB.h"

#define REL_BEGIN 0  /* fseek relative to beginning of file */
#define REL_CUR   1  /* fseek relative to current position */
#define REL_EOF   2  /* fseek relative to end of file */

#define MIN(a,b)  ( ( (a) < (b) ) ? (a) : (b) )
#define BX  3  /* default averaging box size */
#define SQR(a)  ((a)*(a))

/**
 *
 * @param flag int to indicate if inputs are coregistered slcs / int-amp
 * @param int_file the interferogram file / slc1 file if flag is set
 * @param ifile1 the amplitude file / slc2 file if flag is set
 * @param c_file the output correlation file
 * @param the width of the interferogram and amplitude files
 * @param bx correlation box size (default = 3)
 * @param xmin starting range pixel offset (default=0)
 * @param xmax last range pixel offset (default=width-1)
 * @param ymin starting azimuth row offset (default=0)
 * @param ymax last azimuth row offset (default=nlines-1)
 */
int cchz_wave(int flag, char *intFilename, char *ampFilename, char *corFilename,
              int width,int bx, int xmin, int xmax, int ymin, int ymax)
{
  /* interferogram line buffer, complex input data, row pointers */
  fcomplex *bufcz,*cmpb,*tc;
  fcomplex **cmp;

  double a1,ai1,ai2,ar,ai;
  double *rw;              /* range correlation weights */
  double *azw;             /* azimuth correlation weights */

  float *sm;               /* correlation line buffer */
  float *amp;              /* correlation amplitude buffer */
  fcomplex *ib1,*t1;       /* image intensities buffers */
  fcomplex **i1;           /* pointers to 2 image intensities lines */
  float wt;                /* product of range and azimuth weights */
  fcomplex dt1, dt2;       /* temp variables to go from slcs to int-amp */

  /*number of lines in file:changed to long to better handle > 2 GB files*/
  long nlines=0;
  int xw,yh;               /* width, height of processed region */
  int i,j,k,n;             /* loop counters */
  int icnt;                /* line counter */
  /* might cause other problems long width; interferogram width set to long for
     better handling of large files EJF 2010/03/15 */
  int nrw,nazw;            /* size of filter windows in range, azimuth */

  FILE *int_file,*ifile1,*c_file;

  if (flag)
      fprintf(stderr, "Operating on coregistered SLCs. \n");
  else
      fprintf(stderr, "Operating on ROI_PAC style int and amp files. \n");

  int_file = fopen(intFilename,"r");
  if (int_file == NULL){
      fprintf(stderr,"ERROR: cannot open interferogram file: %s\n",
              intFilename);exit(-1);}

  ifile1 = fopen(ampFilename,"r");
  if (ifile1 == NULL){
      fprintf(stderr,"ERROR: cannot open amplitude image file 1: %s\n",
              ampFilename);exit(-1);}

  c_file = fopen(corFilename,"w");
  if (c_file == NULL){
      fprintf(stderr,"ERROR: cannot create correlation output file: %s\n",
              corFilename);exit(-1);}

  if (bx <=0 ) {
      bx = 3;
  }

  if (xmax <= 0) {
     xmax=width-1;
  }

  fseeko(int_file, (off_t)0L, REL_EOF);    /* determine # lines in the file */

  /* cast to long after division in case long is 32-bits, added (off_t) to make
     sure division is done with "off_t" length integers */
  nlines=(long)(ftello(int_file)/(off_t)(width*sizeof(fcomplex)));

  fprintf(stderr,"#lines in the interferogram file: %ld\n",nlines);
  if(nlines < 0L) {
    fprintf(stderr,"Calculation of number of lines negative! Bailing out.\n");
    exit(-1);
  }
  rewind(int_file);
  if (ymax <= 0) {
     ymax=nlines-1;
  }

  if (ymax > nlines-1){
    ymax = nlines-1;
    fprintf(stderr,"insufficient #lines in the file, ymax: %d\n",ymax);
  }

  if (xmax > width-1) xmax=width-1;    /* check to see if xmax within bounds */
  xw=xmax-xmin+1;                      /* width of array */
  yh=ymax-ymin+1;                      /* height of array */
  fprintf(stdout,
          "processing window, xmin,xmax,ymin,ymax: %5d  %5d  %5d  %5d\n",
          xmin,xmax,ymin,ymax);
  fprintf(stdout,"processing window size, width, height:  %5d  %5d\n",xw,yh);
  fprintf(stdout,"averaging box size: %5d\n",bx);

  bufcz = (fcomplex *)malloc(sizeof(fcomplex)*width);
  cmpb  = (fcomplex *)malloc(sizeof(fcomplex)*width*bx);
  cmp   = (fcomplex **)malloc(sizeof(fcomplex *)*bx);
  if (bufcz==NULL || cmpb==NULL ||  cmp==NULL){
    fprintf(stderr,"failure to allocate space for complex data buffers!\n");
    exit(-1);
  }

  ib1   = (fcomplex *)malloc(sizeof(fcomplex)*width*bx);
  i1    = (fcomplex **)malloc(sizeof(fcomplex *)*bx);
  sm    = (float *)malloc(sizeof(float)*width);
  amp   = (float *)malloc(sizeof(float)*width);

  if (ib1==NULL ||  i1==NULL || sm ==NULL){
    fprintf(stderr,"failure to allocate space for memory buffers!\n");
    exit(-1);
  }

  nrw=bx;
  nazw=bx;
  fprintf(stdout,"# correlation weights (range,azimuth):  %6d %6d\n",nrw,nazw);
  rw = (double *)malloc(nrw*sizeof(double));
  azw = (double *)malloc(nazw*sizeof(double));
  if(rw == NULL || azw == NULL) {
    fprintf(stdout,
            "ERROR: memory allocation for correlation weights failed!\n");
            exit(-1);
  }

  fprintf(stdout,"\nrange correlation weights:\n");
  for(j=0; j < nrw; j++){
/*    rw[j]=exp(-fabs(2.0*(j-nrw/2)/bx)); */
    rw[j]=1.0-fabs(2.0*(double)(j-nrw/2)/(bx+1));
    fprintf(stdout,"index,coefficient: %6d %10.5f\n",j-nrw/2,rw[j]);
  }
  fprintf(stdout,"\nazimuth correlation weights:\n");
  for(j=0; j < nazw; j++){
/*    azw[j]=exp(-fabs(2.0*(j-nazw/2)/bx)); */
    azw[j]=1.0-fabs(2.0*(double)(j-nazw/2)/(bx+1));
    fprintf(stdout,"index,coefficient: %6d %10.5f\n",j-nazw/2,azw[j]);
  }

  for(j=0; j < width; j++){bufcz[j].re=0.0; bufcz[j].im=0.0; sm[j]=0.0; amp[j]=0.0;}
  for(j=0; j < width*bx; j++){ib1[j].re=0.0;ib1[j].im=0.0;}

  for(i=0; i < bx; i++){        /* initialize array pointers */
    cmp[i] = cmpb + i*width;
    i1[i]  = ib1  + i*width;
  }

  for(icnt=0,i=0; i < (ymin+bx/2); i++){
    fwrite((char *)bufcz,sizeof(float),width,c_file);    /* write null lines */
    fwrite((char *)bufcz,sizeof(float),width,c_file);    /* write null lines */
    icnt++;
  }

  /* seek start line of interferogram */
  fseeko(int_file,ymin*width*sizeof(fcomplex), REL_BEGIN);
  /* read  interferogram file */
  fread((char *)cmpb,sizeof(fcomplex),width*(bx-1),int_file);
  /* seek start line of amplitude file  */
  fseeko(ifile1,ymin*width*sizeof(fcomplex), REL_BEGIN);
  /* read  image amplitude file */
  fread((char *)ib1,sizeof(fcomplex),width*(bx-1), ifile1);


  /* PSA - Quick fix for coregistered SLC */
  if (flag)  /* To convert from slcs to int-amp */
  {
      for(i=0; i < (bx-1); i++)
      {
          for(j=0; j < width; j++)
          {
            dt1.re = cmp[i][j].re; dt1.im = cmp[i][j].im;
            dt2.re = i1[i][j].re; dt2.im = i1[i][j].im;

            cmp[i][j].re = (dt1.re * dt2.re) - (dt1.im * dt2.im);
            cmp[i][j].im = (dt1.re * dt2.im) + (dt1.im * dt2.re);
        
            i1[i][j].re = sqrt((double)(dt1.re*dt1.re + dt1.im*dt1.im));
            i1[i][j].im = sqrt((double)(dt2.re*dt2.re + dt2.im*dt2.im));
          }
      }
  }

  for (i=bx/2; i < yh-bx/2; i++){
    if(i%10 == 0) fprintf(stderr,"\rprocessing line: %d", i);

    /* read  interferogram file */
    fread((char *)cmp[bx-1],sizeof(fcomplex),width,int_file);
    /* read  image intensity file 1 */
    fread((char *)i1[bx-1],sizeof(fcomplex),width,ifile1);

    if (flag)  /* To convert from slcs to int-amp */
    {
        for(j=0; j < width; j++)
        {
            dt1.re = cmp[bx-1][j].re; dt1.im = cmp[bx-1][j].im;
            dt2.re = i1[bx-1][j].re; dt2.im = i1[bx-1][j].im;

            cmp[bx-1][j].re = (dt1.re * dt2.re) + (dt1.im * dt2.im);
            cmp[bx-1][j].im = (dt1.im * dt2.re) - (dt1.re * dt2.im);
        
            i1[bx-1][j].re = sqrt((double)(dt1.re*dt1.re + dt1.im*dt1.im));
            i1[bx-1][j].im = sqrt((double)(dt2.re*dt2.re + dt2.im*dt2.im));
        } 
    }

    /* move across the image j=xmin+bx/2 to j=width-bx/2-1 (xmin=0, xw=width)*/
    for (j=xmin+bx/2; j < xw-bx/2; j++){
      ai1=0.0; ai2=0.0; ar=0.0; ai=0.0;

      /* average over the box */
      for (k=0; k < bx; k++){
        for (n=j-bx/2; n < j-bx/2+bx; n++){
          wt=azw[k]*rw[n-j+bx/2];
          ai1 += SQR(i1[k][n].re)*wt;
          ai2 += SQR(i1[k][n].im)*wt;
          ar  += cmp[k][n].re*wt;
          ai  += cmp[k][n].im*wt;
        }
      }

      a1=sqrt(ai1*ai2);
      amp[j]=sqrt((double)i1[bx/2][j].re*(double)i1[bx/2][j].im) ;
      /* renormalized correlation coefficient */
      if (a1 > 0.0) sm[j] = (float)hypot(ar,ai)/a1;
      else sm[j]=0.0;
      sm[j]=MIN(sm[j],1.0);

    }

    fwrite((char *)amp, sizeof(float), width, c_file);
    fwrite((char *)sm, sizeof(float), width, c_file);
    icnt++;
    /* buffer circular shift */
    /* save pointer addresses of the oldest line */
    t1=i1[0]; tc=cmp[0];
    /* shift addresses */
    for (k=1; k < bx; k++){
      i1[k-1]=i1[k]; cmp[k-1]=cmp[k];
    }
    /* new data will overwrite the oldest */
    i1[bx-1]=t1; cmp[bx-1]=tc;
  }

  for(j=0; j < bx/2; j++){
    /* write null lines */
    fwrite((char *)bufcz, sizeof(float), width, c_file);
    fwrite((char *)bufcz, sizeof(float), width, c_file);
    icnt++;
  }

  fprintf(stdout,"\noutput lines: %d\n", icnt);
  fclose(int_file);
  fclose(ifile1);
  fclose(c_file);
  free(rw);
  free(azw);
  free(ib1);
  free(i1);
  free(amp);
  free(sm);
  free(bufcz);
  free(cmp);
  free(cmpb);
  return(0);
}

//POD=pod
//POD
//POD=head1 USAGE
//POD
//POD Usage: cchz_wave <interferogram> <ampfile> <correlation> <width> <box> <xmin> <xmax> <ymin> <ymax>
//POD        where the input parameters are :
//POD          interferogram      complex interferogram filename
//POD          ampfile            packed amplitudes a la hz
//POD          correlation        output correlation filename
//POD          width              number of samples/row
//POD          box                correlation average box size (default = 3)
//POD          xmin               starting range pixel offset (default = 0)
//POD          xmax               last range pixel offset (default = width-1)
//POD          ymin               starting azimuth row offset, relative to start (default = 0)
//POD          ymax               last azimuth row offset, relative to start (default = nlines-1)
//POD
//POD=head1 FUNCTION
//POD
//POD FUNCTIONAL DESCRIPTION:  correlation estimation from interferogram
//POD
//POD
//POD
//POD=head1 ROUTINES CALLED
//POD
//POD none
//POD
//POD=head1 CALLED BY
//POD
//POD
//POD=head1 FILES USED
//POD
//POD --complex interferogram c*8/complex, record length: with
//POD --packed amplitudes: c*8/complex where Re == amplitude channel1, Im == amplitude chan 2, record length: with
//POD
//POD=head1 FILES CREATED
//POD
//POD output correlation float/r*4, record length: width
//POD
//POD=head1 DIAGNOSTIC FILES
//POD
//POD
//POD=head1 HISTORY
//POD
//POD Routines written by Charles Werner
//POD
//POD=head1 LAST UPDATE
//POD  Date Changed        Reason Changed
//POD  ------------       ----------------
//POD
//POD POD comments trm Feb 13th '04
//POD Oct. 2, 2006   EJF  changed length of file calculation to use long variable to avoid truncation on > 2GB files
//POD Aug. 21, 2007  EJF  changed file calls to fseeko and ftello to better access large files
//POD Apr. 28, 2009  EJF  modified file length calc. again
//POD=cut
