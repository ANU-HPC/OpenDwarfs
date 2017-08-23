#include <stdio.h>
#include <unistd.h>
#include <getopt.h>
#include <stdlib.h>
#include <assert.h>
#include <math.h>
#include <malloc.h>
#include <string.h>

#include "../../include/rdtsc.h"
#include "../../include/common_args.h"
#include "../../include/lsb.h"
#include "common.h"

//#define USEGPU 1
int BLOCK_SIZE = 16;
static int do_verify = 0;
#define AOCL_ALIGNMENT 64

static struct option long_options[] = {
	/* name, has_arg, flag, val */
	{"input", 1, NULL, 'i'},
	{"platform", 1, NULL, 'p'},
	{"device", 1, NULL, 'd'},
	{"size", 1, NULL, 's'},
	{"verify", 0, NULL, 'v'},
	{0,0,0,0}
};

	int
main ( int argc, char *argv[] )
{
	int matrix_dim = 0; /* default matrix_dim */
	int opt, option_index=0;
	func_ret_t ret;
	const char *input_file = NULL;
	float *m, *mm;
	stopwatch sw;

	//cl_device_id device_id;
	//cl_context context;
	//cl_command_queue commands;
	cl_program clProgram;
	cl_kernel clKernel_diagonal;
	cl_kernel clKernel_perimeter;
	cl_kernel clKernel_internal;
	cl_int dev_type;

	cl_int errcode;

	FILE *kernelFile;
	char *kernelSource;
	size_t kernelLength;

	cl_mem d_m;

    LSB_Init("lud", 0);

    LSB_Set_Rparam_string("region", "host_side_setup");
    LSB_Res();

	ocd_init(&argc, &argv, NULL);
	ocd_initCL();
    //set the local workgroup sizes
    if (ocd_get_options().workgroup_1d != 0){
        BLOCK_SIZE=ocd_get_options().workgroup_1d;
    }
    printf("BLOCK_SIZE = %i\n",BLOCK_SIZE);

	while ((opt = getopt_long(argc, argv, "::vs:i:", 
					long_options, &option_index)) != -1 ) {
		switch(opt){
			case 'i':
				input_file = optarg;
				break;
			case 'v':
				do_verify = 1;
				break;
			case 's':
				matrix_dim = atoi(optarg);
                break;
			case '?':
				fprintf(stderr, "invalid option\n");
				break;
			case ':':
				fprintf(stderr, "missing argument\n");
				//break;
			default:
				fprintf(stderr, "Usage: %s [-v] [-s matrix_size|-i input_file]\n",
						argv[0]);
				exit(EXIT_FAILURE);
		}
	}

	if ( (optind < argc) || (optind == 1)) {
		fprintf(stderr, "Usage: %s [-v] [-s matrix_size|-i input_file]\n", argv[0]);
		exit(EXIT_FAILURE);
	}
    if(matrix_dim == 0 && input_file){
        fprintf(stderr, "No Usage: %s [-v] [-s matrix_size|-i input_file]\n", argv[0]);
        exit(EXIT_FAILURE);
    }
    if(matrix_dim != 0){
        //create the matrix
        int i, j;
        m = (float*)memalign(AOCL_ALIGNMENT,sizeof(float)*matrix_dim*matrix_dim);
        for (i=0; i < matrix_dim; i++) {
            for (j=0; j < matrix_dim; j++) {
                m[i*matrix_dim+j] = ((float)rand() / (float)RAND_MAX);
            }
        }
    }
    else if (input_file) {
		printf("Reading matrix from file %s\n", input_file);
		ret = create_matrix_from_file(&m, input_file, &matrix_dim);
		if (ret != RET_SUCCESS) {
			m = NULL;
			fprintf(stderr, "error create matrix from file %s\n", input_file);
			exit(EXIT_FAILURE);
		}
	} else {
		printf("No input file specified!\n");
		exit(EXIT_FAILURE);
	}

	if (do_verify){
		printf("Before LUD\n");
		print_matrix(m, matrix_dim);
		matrix_duplicate(m, &mm, matrix_dim);
	}

	size_t max_worksize[3];
	errcode = clGetDeviceInfo(device_id, CL_DEVICE_MAX_WORK_ITEM_SIZES,sizeof(size_t)*3, &max_worksize, NULL);
	CHKERR(errcode, "Failed to get device info!");
	//Start by 16*16, but if not allowed divide by two until MAX_WORK_ITEM_SIZES is less or equal than what we are going to ask for.
	//while(BLOCK_SIZE*BLOCK_SIZE>max_worksize[0])
	//	BLOCK_SIZE = BLOCK_SIZE/2;
    LSB_Rec(0);

    LSB_Set_Rparam_int("matrix_dimension",matrix_dim);

    LSB_Set_Rparam_string("region", "kernel_creation");
    LSB_Res();

	char arg[100];
 	char* kernel_files;
	int num_kernels = 1;
	sprintf(arg,"-D BLOCK_SIZE=%d", (int)BLOCK_SIZE);
	kernel_files = (char*) malloc(sizeof(char*)*num_kernels);
	strcpy(kernel_files,"lud_kernel");

	clProgram = ocdBuildProgramFromFile(context,device_id,kernel_files,arg);

	clKernel_diagonal = clCreateKernel(clProgram, "lud_diagonal", &errcode);
	CHKERR(errcode, "Failed to create kernel!");
	clKernel_perimeter = clCreateKernel(clProgram, "lud_perimeter", &errcode);
	CHKERR(errcode, "Failed to create kernel!");
	clKernel_internal = clCreateKernel(clProgram, "lud_internal", &errcode);
	CHKERR(errcode, "Failed to create kernel!");

    LSB_Rec(0);
    
    LSB_Set_Rparam_string("region", "device_side_buffer_setup");
    LSB_Res();

    d_m = clCreateBuffer(context, CL_MEM_READ_WRITE, matrix_dim*matrix_dim*sizeof(float), NULL, &errcode);
	CHKERR(errcode, "Failed to create buffer!");

    LSB_Rec(0);
    printf("Working kernel memory: %fKiB\n",
                (matrix_dim*matrix_dim*sizeof(float))/1024.0);
	/* beginning of timing point */
	stopwatch_start(&sw);

    LSB_Set_Rparam_string("region", "device_side_h2d_copy");
    LSB_Res();

	errcode = clEnqueueWriteBuffer(commands, d_m, CL_TRUE, 0, matrix_dim*matrix_dim*sizeof(float), (void *) m, 0, NULL, &ocdTempEvent);

	clFinish(commands);
	START_TIMER(ocdTempEvent, OCD_TIMER_H2D, "Matrix Copy", ocdTempTimer)
		END_TIMER(ocdTempTimer)
		CHKERR(errcode, "Failed to enqueue write buffer!");

    LSB_Rec(0);

	int i=0;
	size_t localWorkSize[2];
	size_t globalWorkSize[2];
	//printf("BLOCK_SIZE: %d\n",BLOCK_SIZE);	
	//printf("max Work-item Size: %d\n",(int)max_worksize[0]);	
#ifdef START_POWER
	for( int iter = 0; iter < 1000; iter++)
#endif
#ifdef PROFILE_OUTER_LOOP
    LSB_Set_Rparam_string("region", "lud_loop");
    LSB_Res();
#endif
		for (i=0; i < matrix_dim-BLOCK_SIZE; i += BLOCK_SIZE) {
#ifndef PROFILE_OUTER_LOOP
            LSB_Set_Rparam_string("region", "setting_diagonal_kernel_arguments");
            LSB_Res();
#endif
			errcode = clSetKernelArg(clKernel_diagonal, 0, sizeof(cl_mem), (void *) &d_m);
			errcode |= clSetKernelArg(clKernel_diagonal, 1, sizeof(int), (void *) &matrix_dim);
			errcode |= clSetKernelArg(clKernel_diagonal, 2, sizeof(int), (void *) &i);
			CHKERR(errcode, "Failed to set kernel arguments!");
#ifndef PROFILE_OUTER_LOOP
            LSB_Rec(i);
#endif
			localWorkSize[0] = BLOCK_SIZE;
			globalWorkSize[0] = BLOCK_SIZE;
#ifndef PROFILE_OUTER_LOOP
            LSB_Set_Rparam_string("region", "diagonal_kernel");
            LSB_Res();
#endif
			errcode = clEnqueueNDRangeKernel(commands, clKernel_diagonal, 1, NULL, globalWorkSize, localWorkSize, 0, NULL, &ocdTempEvent);
			clFinish(commands);
#ifndef PROFILE_OUTER_LOOP
            LSB_Rec(i);
#endif
		    //printf("max Work-item Size2: %d\n",(int)max_worksize[0]);	
			START_TIMER(ocdTempEvent, OCD_TIMER_KERNEL, "Diagonal Kernels", ocdTempTimer)
				END_TIMER(ocdTempTimer)
				CHKERR(errcode, "Failed to enqueue kernel!");
#ifndef PROFILE_OUTER_LOOP
            LSB_Set_Rparam_string("region", "setting_perimeter_kernel_arguments");
            LSB_Res();
#endif

			errcode = clSetKernelArg(clKernel_perimeter, 0, sizeof(cl_mem), (void *) &d_m);
			errcode |= clSetKernelArg(clKernel_perimeter, 1, sizeof(int), (void *) &matrix_dim);
			errcode |= clSetKernelArg(clKernel_perimeter, 2, sizeof(int), (void *) &i);
			CHKERR(errcode, "Failed to set kernel arguments!");
#ifndef PROFILE_OUTER_LOOP
            LSB_Rec(i);
#endif
			localWorkSize[0] = BLOCK_SIZE*2;
			globalWorkSize[0] = ((matrix_dim-i)/BLOCK_SIZE-1)*localWorkSize[0];
#ifndef PROFILE_OUTER_LOOP
            LSB_Set_Rparam_string("region", "perimeter_kernel");
            LSB_Res();
#endif
			errcode = clEnqueueNDRangeKernel(commands, clKernel_perimeter, 1, NULL, globalWorkSize, localWorkSize, 0, NULL, &ocdTempEvent);
			clFinish(commands);
#ifndef PROFILE_OUTER_LOOP
            LSB_Rec(i);
#endif
			START_TIMER(ocdTempEvent, OCD_TIMER_KERNEL, "Perimeter Kernel", ocdTempTimer)
				CHKERR(errcode, "Failed to enqueue kernel!");
			END_TIMER(ocdTempTimer)
#ifndef PROFILE_OUTER_LOOP
            LSB_Set_Rparam_string("region", "setting_internal_kernel_arguments");
            LSB_Res();
#endif
				errcode = clSetKernelArg(clKernel_internal, 0, sizeof(cl_mem), (void *) &d_m);
			errcode |= clSetKernelArg(clKernel_internal, 1, sizeof(int), (void *) &matrix_dim);
			errcode |= clSetKernelArg(clKernel_internal, 2, sizeof(int), (void *) &i);
			CHKERR(errcode, "Failed to set kernel arguments!");
#ifndef PROFILE_OUTER_LOOP
            LSB_Rec(i);
#endif
			localWorkSize[0] = BLOCK_SIZE;
			localWorkSize[1] = BLOCK_SIZE;
			globalWorkSize[0] = ((matrix_dim-i)/BLOCK_SIZE-1)*localWorkSize[0];
			globalWorkSize[1] = ((matrix_dim-i)/BLOCK_SIZE-1)*localWorkSize[1];
#ifndef PROFILE_OUTER_LOOP
            LSB_Set_Rparam_string("region", "internal_kernel");
            LSB_Res();
#endif
			errcode = clEnqueueNDRangeKernel(commands, clKernel_internal, 2, NULL, globalWorkSize, localWorkSize, 0, NULL, &ocdTempEvent);
			clFinish(commands);
#ifndef PROFILE_OUTER_LOOP
            LSB_Rec(i);
#endif

            START_TIMER(ocdTempEvent, OCD_TIMER_KERNEL, "Internal Kernel", ocdTempTimer)
                END_TIMER(ocdTempTimer)
                CHKERR(errcode, "Failed to enqueue kernel!");
		}
#ifdef PROFILE_OUTER_LOOP
    LSB_Rec(0);
#endif

    LSB_Set_Rparam_string("region", "setting_final_diagonal_kernel_arguments");
    LSB_Res();

	errcode = clSetKernelArg(clKernel_diagonal, 0, sizeof(cl_mem), (void *) &d_m);
	errcode |= clSetKernelArg(clKernel_diagonal, 1, sizeof(int), (void *) &matrix_dim);
	errcode |= clSetKernelArg(clKernel_diagonal, 2, sizeof(int), (void *) &i);
	CHKERR(errcode, "Failed to set kernel arguments!");
    LSB_Rec(i);


	localWorkSize[0] = BLOCK_SIZE;
	globalWorkSize[0] = BLOCK_SIZE;
    LSB_Set_Rparam_string("region", "final_diagonal_kernel");
    LSB_Res();

	errcode = clEnqueueNDRangeKernel(commands, clKernel_diagonal, 1, NULL, globalWorkSize, localWorkSize, 0, NULL, &ocdTempEvent);
	clFinish(commands);
    LSB_Rec(0);

	START_TIMER(ocdTempEvent, OCD_TIMER_KERNEL, "Diagonal Kernels", ocdTempTimer)
		CHKERR(errcode, "Failed to enqueue kernel!");
	END_TIMER(ocdTempTimer)

    LSB_Set_Rparam_string("region", "device_side_d2h_copy");
    LSB_Res();

		errcode = clEnqueueReadBuffer(commands, d_m, CL_TRUE, 0, matrix_dim*matrix_dim*sizeof(float), (void *) m, 0, NULL, &ocdTempEvent);
	clFinish(commands);
    LSB_Rec(0);

	START_TIMER(ocdTempEvent, OCD_TIMER_D2H, "Matrix copy", ocdTempTimer)
		END_TIMER(ocdTempTimer)
		/* end of timing point */
		stopwatch_stop(&sw);
	printf("Time consumed(ms): %lf\n", 1000*get_interval_by_sec(&sw));

	clReleaseMemObject(d_m);

	if (do_verify){
		printf("After LUD\n");
		print_matrix(m, matrix_dim);
		printf(">>>Verify<<<<\n");
		printf("matrix_dim: %d\n",matrix_dim);
		lud_verify(mm, m, matrix_dim); 
		free(mm);
	}

	clReleaseKernel(clKernel_diagonal);
	clReleaseKernel(clKernel_perimeter);
	clReleaseKernel(clKernel_internal);
	clReleaseProgram(clProgram);
	clReleaseCommandQueue(commands);
	clReleaseContext(context);

    LSB_Finalize();
	free(m);
	ocd_finalize();
	return EXIT_SUCCESS;
}				/* ----------  end of function main  ---------- */
