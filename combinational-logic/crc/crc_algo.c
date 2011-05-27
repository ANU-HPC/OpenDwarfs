#include <stdio.h>
#include <stdlib.h>
#include <time.h>
#include <unistd.h>
#include <string.h>
#include <math.h>


#ifdef __APPLE__
#include <OpenCL/opencl.h>
#else
#include <CL/opencl.h>
#endif

#define CHKERR(err, str) \
	if (err != CL_SUCCESS) \
	{ \
		fprintf(stderr, "CL Error %d: %s\n", err, str); \
		exit(1); \
	}

#define USEGPU 1
#define DATA_SIZE 100000000
#define MIN(a,b) a < b ? a : b

const char *KernelSourceFile = "crc_algo_kernel.cl";
cl_platform_id platform_id;
cl_device_id device_id;
cl_context context;
cl_command_queue commands;
cl_program program;
cl_kernel kernel_compute;
	
cl_mem dev_input;
cl_mem dev_table;
cl_mem dev_output;


void usage()
{
	printf("graphCreator [hsivp]\n");
	printf("h		 - print this help message\n");
	printf("s <seed>  - set the seed for the vertex\n");
	printf("i <file>  - take input from file instead of randomly generating code\n");
	printf("v		 - verify parallel code with serial implementation of crc\n");
	printf("p <int>   - change the last 8 bits of the crc polynomial\n");
}

unsigned char serialCRC(unsigned char* h_num, size_t size, unsigned char crc)
{
	unsigned int i;
	unsigned char num = h_num[0];
	for(i = 1; i < size + 1; i++)
	{
		unsigned char crcCalc = h_num[i];
		unsigned int k;
		if(i == size)
			crcCalc = 0;
		for(k = 0; k < 8; k++)
		{
			//If the k-th bit is 1
			if((num >> (7-k)) % 2 == 1)
			{
				num ^= crc >> (k + 1);
				crcCalc ^= crc << (7-k);
			}
		}
		num = crcCalc;
	}

	return num;
}

int getNextChunk(long N, FILE* fp, char* h_num, size_t maxSize, size_t* read, int* pad_o)
{
	int i;
	if(fp != NULL)
	{
		size_t read = fread(h_num, 1, N, fp);
		if(read < N)
		{
			int pad = N - read;
			for(i = N - 1; i >= pad; i--)
			{	
				h_num[i] = h_num[i-pad];
			}
			for(i = 0; i < pad; i++)
			{
				h_num[i] = 0;
			}
			if(pad_o != NULL)
				*pad_o = pad;
			return 0;
		}
	}
	else
	{
		*read += N;
		
		for(i = 0; i < N; i++)
		{
			h_num[i] = rand();
		}
		if(*read > maxSize)
		{
			int pad = *read - maxSize;
			for(i = N - 1; i >= pad; i--)
			{
				h_num[i] = h_num[i-pad];
			}
			for(i = 0; i < pad; i++)
			{
				h_num[i] = 0;
			}
			if(pad_o != NULL)
				*pad_o = pad;
			return 0;	
		}
		if(*read == maxSize)
			return 0;
	}
	return 1;
}

void computeTables(unsigned char* tables, int numTables, unsigned char crc)
{
	int level = 0;
	int i;
	for(i = 0; i < 256; i++)
	{
		unsigned char val = i;
		tables[i] = serialCRC(&val, 1, crc);
	}
	for(level = 1; level < numTables; level++)
	{
		for(i = 0; i < 256; i++)
		{
			unsigned char iter = i;
			unsigned char val = tables[(level-1)*256 + i];
			tables[level * 256 + i] = tables[(level-1)*256 + val];
		}
	}
}

unsigned char computeCRCGPU(unsigned char* h_num, unsigned long N, unsigned char crc, unsigned char* tables, unsigned long numTables)
{
	// Write our data set into the input array in device memory
	int err = clEnqueueWriteBuffer(commands, dev_input, CL_TRUE, 0, sizeof(char)*N, h_num, 0, NULL, NULL);
	CHKERR(err, "Failed to write to source array!");

	// Set the arguments to our compute kernel
	err = 0;
	err = clSetKernelArg(kernel_compute, 0, sizeof(cl_mem), &dev_input);
	err |= clSetKernelArg(kernel_compute, 1, sizeof(cl_mem), &dev_table);
	err |= clSetKernelArg(kernel_compute, 2, sizeof(unsigned int), &numTables);
	err |= clSetKernelArg(kernel_compute, 3, sizeof(cl_mem), &dev_output);
	err |= clSetKernelArg(kernel_compute, 4, sizeof(unsigned int), &N);
	CHKERR(err, "Failed to set compute kernel arguments!");

	size_t local_size;
	size_t global_size;
	// Get the maximum work group size for executing the kernel on the device
	err = clGetKernelWorkGroupInfo(kernel_compute, device_id, CL_KERNEL_WORK_GROUP_SIZE, sizeof(size_t), (void *) &local_size, NULL);
	CHKERR(err, "Failed to retrieve kernel_compute work group info!");

	// Wait for the command commands to get serviced before reading back results
	clFinish(commands);
	
	// Execute the kernel over the entire range of our 1d input data set
	// using the maximum number of work group items for this device
	global_size = N;
	local_size = MIN(local_size, N);
	err = clEnqueueNDRangeKernel(commands, kernel_compute, 1, NULL, &global_size, &local_size, 0, NULL, NULL);
	CHKERR(err, "Failed to execute compute kernel!");

	unsigned char* h_answer = malloc(sizeof(*h_answer)*N);
	// Read back the results from the device to verify the output
	err = clEnqueueReadBuffer(commands, dev_output, CL_TRUE, 0, sizeof(char)*N, h_answer, 0, NULL, NULL);
	CHKERR(err, "Failed to read output array!");

	unsigned char answer = 0;
	
	int i;
	for(i = 0; i < N; i++)
		answer ^= h_answer[i];

	return answer;
}


unsigned char computeCRC(unsigned char* h_num, unsigned long N, unsigned char crc, unsigned char* tables, int numTables)
{
	int i;
	unsigned char answer = 0;
	for(i = 0; i < N; i++)
	{
		int val = N - i;
		int k;
		unsigned char temp = h_num[i];
		//for(k = 0; k < val; k++)
		//	temp = tables[temp];
		for(k = 0; k < numTables; k++)
		{
			if((val >> k) % 2 == 1)
				temp = tables[k * 256 + temp];
		}	
		answer ^= temp;
	}
	return answer;
}

void setupGPU()
{
	// Retrieve an OpenCL platform
	int err = clGetPlatformIDs(1, &platform_id, NULL);
	CHKERR(err, "Failed to get a platform!");

	// Connect to a compute device
	err = clGetDeviceIDs(platform_id, USEGPU ? CL_DEVICE_TYPE_GPU : CL_DEVICE_TYPE_CPU, 1, &device_id, NULL);
	CHKERR(err, "Failed to create a device group!");

	// Create a compute context
	context = clCreateContext(0, 1, &device_id, NULL, NULL, &err);
	CHKERR(err, "Failed to create a compute context!");

	// Create a command queue
	commands = clCreateCommandQueue(context, device_id, 0, &err);
	CHKERR(err, "Failed to create a command queue!");

	FILE* kernelFile = NULL;
	kernelFile = fopen(KernelSourceFile, "r");
	if(!kernelFile)
		printf("Error reading file.\n"), exit(0);
	fseek(kernelFile, 0, SEEK_END);
	size_t kernelLength = (size_t) ftell(kernelFile);
	char* kernelSource = (char *) malloc(sizeof(char)*kernelLength+1);
	rewind(kernelFile);
	fread((void *) kernelSource, kernelLength, 1, kernelFile);
	kernelSource[kernelLength] = 0;
	fclose(kernelFile);
	
	// Create the compute program from the source buffer
	program = clCreateProgramWithSource(context, 1, (const char **) &kernelSource, NULL, &err);
	CHKERR(err, "Failed to create a compute program!");

	free(kernelSource);

	// Build the program executable
	err = clBuildProgram(program, 0, NULL, NULL, NULL, NULL);
	if (err == CL_BUILD_PROGRAM_FAILURE)
	{
		char *log;
		size_t logLen;
		err = clGetProgramBuildInfo(program, device_id, CL_PROGRAM_BUILD_LOG, 0, NULL, &logLen);
		log = (char *) malloc(sizeof(char)*logLen);
		err = clGetProgramBuildInfo(program, device_id, CL_PROGRAM_BUILD_LOG, logLen, (void *) log, NULL);
		fprintf(stderr, "CL Error %d: Failed to build program! Log:\n%s", err, log);
		free(log);
		exit(1);
	}
	CHKERR(err, "Failed to build program!");

	// Create the compute kernel in the program we wish to run
	kernel_compute = clCreateKernel(program, "compute", &err);
	CHKERR(err, "Failed to create a compute kernel!");
}

int main(int argc, char** argv)
{
	cl_int err;

	unsigned char* h_num;
	unsigned char* h_answer;
	unsigned char* data = NULL;
	unsigned char crc = 0x9B;
	unsigned long N = 1024;
	unsigned char finalCRC;
	unsigned char* h_tables;
	unsigned int run_serial = 0;
	char* file = NULL;
	size_t maxSize = DATA_SIZE;
	size_t read = 0;
	FILE* fp = NULL;
	unsigned int seed = time(NULL);
	srand(seed);
		
	int c;
	while((c = getopt (argc, argv, "vs:i:p:h")) != -1)
	{
		switch(c)
		{
			case 'h':
				usage();
				exit(0);
				break;
			case 'p':
				crc = atoi(optarg);				
				break;
			case 'v':
				run_serial = 1;
				break;
			case 'i':
				file = malloc(sizeof(*file) * strlen(optarg));
				strncpy(file, optarg, sizeof(*file) * strlen(optarg));
				break;
			case 's':
				srand(atoi(optarg));
				seed = atoi(optarg);
				break;
			default:
				abort();
		}	
	}
	

	size_t global_size;
	size_t local_size;

	
	h_num = malloc(sizeof(*h_num) * N);

	setupGPU();
	
	//Generate Tables for the given size of N
	int numTables = floor(log(N)/log(2)) + 1;
	printf("num tables = %d\n", numTables);
	h_tables = malloc(256 * sizeof(char) * numTables);	
	
	// Create the input and output arrays in device memory for our calculation
	dev_input = clCreateBuffer(context, CL_MEM_READ_ONLY, sizeof(char)*N, NULL, &err);
	CHKERR(err, "Failed to allocate device memory!");
	dev_table = clCreateBuffer(context, CL_MEM_READ_WRITE, sizeof(char)*256 * numTables, NULL, &err);
	CHKERR(err, "Failed to allocate device memory!");
	dev_output = clCreateBuffer(context, CL_MEM_WRITE_ONLY, sizeof(char)*N, NULL, &err);
	CHKERR(err, "Failed to allocate device memory!");

	computeTables(h_tables, numTables, crc);
	
	// Write our data set into the input array in device memory
	err = clEnqueueWriteBuffer(commands, dev_table, CL_TRUE, 0, sizeof(char)*256*numTables, h_tables, 0, NULL, NULL);
	CHKERR(err, "Failed to write to source array!");
	
	//Open file if it exists	
	if(file != NULL)
		fp = fopen(file, "rb");

	int readsLeft = getNextChunk(N, fp, h_num, maxSize, &read, NULL);
	int lastcrc = computeCRC(h_num, N, crc, h_tables, numTables);
	while(readsLeft)
	{
		int pad = 0;
		//Get Next Chunk
		readsLeft = getNextChunk(N, fp, h_num, maxSize, &read, &pad);
		if(pad == N)
			break;	

		//XOR result to new numbers	
		h_num[pad] ^= lastcrc;	
		
		//Compute the CRC for this chunk
		lastcrc = computeCRCGPU(h_num, N, crc, h_tables, numTables);			
	}

	printf("Parallel CRC: '%X'\n", lastcrc);
	if(fp != NULL)
		fclose(fp);
	free(h_num);
	free(h_tables);
 
	// Calculate the result if done in serial to verify that we have the correct answer.
	if(run_serial)
	{
		printf("Computing Serial CRC\n");		
		unsigned int count = maxSize;
		if(file == NULL)
		{
			srand(seed);
			h_num = malloc(sizeof(*h_num) * count);
			int i;
			for(i = 0; i < count; i++)
				h_num[i] = rand();
		}
		else
		{
			fp = fopen(file, "rb");
			if(!fp)
			{
				printf("Error reading file\n");
				exit(1);
			}
			h_num = calloc(sizeof(*h_num) * DATA_SIZE, 1);
			size_t read = fread(h_num, 1, DATA_SIZE, fp);
			count = read;// + pad;
		}
		unsigned char crcVal = serialCRC(h_num, count, crc);
		printf("Serial Computation: '%X'\n", crcVal);
		free(h_num);
		if(fp)
			fclose(fp);
	}	

	printf("Done\n");
		
}
