#!/usr/bin/env python
from opendwarf_miner_utils import *

from sys import argv,exit
selected_applications = None

oclgrind = os.getenv('OCLGRIND_BIN', 'oclgrind')

if len(argv) == 2:
    selected_applications = str(argv[1])
    print("Running Oclgrind on application:"+selected_applications)

#Benchmark parameters:
kmeans = {'name':'kmeans',
          'alias':'kmeans',
          'default':'-i ../test/mapreduce/kmeans/65536_34f.txt',
          'tiny':'-g -f 30 -p 256',     #< 32K, object increments of 1KiB
          'small':'-g -f 30 -p 2048',   #< 256K, object increments of 8KiB
          'medium':'-g -f 30 -p 65600', #< 8196K, object increments of 256KiB
          'large':'-g -f 30 -p 131072', #> 8196K, object increments of 2048KiB
          'full name':'K-Means Clustering'}
kmeans_coarse_iteration_profile = {
        'name':'kmeans_profiling_outer_loop',
        'alias':'kmeans',
        'default':'-i ../test/mapreduce/kmeans/65536_34f.txt',
        'tiny':'-g -f 30 -p 256',     # 1KiB
        'small':'-g -f 30 -p 2048',   # 8KiB
        'medium':'-g -f 30 -p 65600', # 256KiB
        'large':'-g -f 30 -p 131072', # 2048KiB
        'full name':'K-Means Clustering'}
lud = {'name':'lud',
       'alias':'lud',
       'default':'-i ../test/dense-linear-algebra/lud/3072.dat',
       'tiny':'-s 80',#25KiB < 32KiB
       'small':'-s 240',#225KiB < 256KiB
       'medium':'-s 1440',#8100KiB < 8196KiB
       'large':'-s 4096', #65536KiB > 8196KiB
       'full name':'Lower Upper Decomposition'}
lud_coarse_iteration_profile = {
       'name':'lud_profiling_outer_loop',
       'alias':'lud',
       'default':'-i ../test/dense-linear-algebra/lud/3072.dat',
       'tiny':'-s 80',#25KiB < 32KiB
       'small':'-s 240',#225KiB < 256KiB
       'medium':'-s 1440',#8100KiB < 8196KiB
       'large':'-s 4096', #65536KiB > 8196KiB
       'full name':'Lower Upper Decomposition'}
csr = {'name':'csr',
       'alias':'csr',
       'default':'-i ../test/sparse-linear-algebra/SPMV/csr_65536.txt',
       'tiny':'-i ../test/sparse-linear-algebra/SPMV/tiny',#generated with ./createcsr -n 736 -d 5000, all matrices have 0.5% density (99.5% sparse) 31.6KiB < 32KiB
       'small':'-i ../test/sparse-linear-algebra/SPMV/small',#2416, 254.8KiB
       'medium':'-i ../test/sparse-linear-algebra/SPMV/medium',#14336, 8195.5KiB
       'large':'-i ../test/sparse-linear-algebra/SPMV/large',#16384, 10677.8KiB
       'full name':'Compressed Sparse Row'}
fft = {'name':'openclfft',
       'alias':'openclfft',
       'default':'128',
       'tiny':'2048', #32KiB
       'small':'16384 ',#256KiB
       'medium':'524288', #8192KiB
       'large':'2097152', #32768KiB
       'full name':'Fast Fourier Transform'}
dwt = {'name':'dwt2d',
       'alias':'dwt2d',
       'default':'-l 3 ../test/spectral-methods/dwt2d/airplane.ppm -w airplane', #writes out the dwt2d wavelet coefficients in a visual form to pgm format
       'tiny':'-l 3 ../test/spectral-methods/dwt2d/72x54-gum.ppm tiny-gum-coefficients', #32KiB
       'small':'-l 3 ../test/spectral-methods/dwt2d/200x150-gum.ppm small-gum-coefficients',#256KiB
       'medium':'-l 3 ../test/spectral-methods/dwt2d/1152x864-gum.ppm medium-gum-coefficients', #8192KiB
       'large':'-l 3 ../test/spectral-methods/dwt2d/3648x2736-gum.ppm large-gum-coefficients', #32768KiB
       'full name':'2D Discrete Wavelet Transform'}
gem = {'name':'gemnoui',
       'alias':'gem',
       'default':'../test/n-body-methods/gem/nucleosome 80 1 0',
       'tiny':'../test/n-body-methods/gem/4TUT 80 1 0', #31.3KiB
       'small':'../test/n-body-methods/gem/2D3V 80 1 0', #252.0KiB
       'medium':'../test/n-body-methods/gem/nucleosome 80 1 0', #7498.1KiB
       'large':'../test/n-body-methods/gem/1KX5 80 1 0', #10970.2KiB
       'full name':'Gemnoui'}
srad = {'name':'srad',
        'alias':'srad',
        'default':'256 256 0 127 0 127 0.5 2',
        'tiny':'80 16 0 127 0 127 0.5 1',#30KiB
        'small':'128 80 0 127 0 127 0.5 1',#240KiB
        'medium':'1024 336 0 127 0 127 0.5 1',#8064KiB
        'large':'2048 1024 0 127 0 127 0.5 1',#49152KiB
        'full name':'Speckle Reducing Anisotropic Diffusion'}
cfd = {'name':'cfd',
       'alias':'cfd',
       'default':'../test/unstructured-grids/cfd/fvcorr.domn.097K',
       'tiny':'../test/unstructured-grids/cfd/128.dat',#23.066KiB
       'small':'../test/unstructured-grids/cfd/1284.dat',#253.066KiB
       'medium':'../test/unstructured-grids/cfd/45056.dat',#8096KiB
       'large':'../test/unstructured-grids/cfd/193474.dat',#34776.066KiB
       'full name':'Computational Fluid Dynamics'}
crc = {'name':'crc',
       'alias':'crc',
       'default':'-i ../test/combinational-logic/crc/crc_1000x8192.txt',
       'tiny':'-i ../test/combinational-logic/crc/crc_1000x2000.txt',#31.31KiB
       'small':'-i ../test/combinational-logic/crc/crc_1000x16000.txt',#250.06KiB
       'medium':'-i ../test/combinational-logic/crc/crc_1000x524000.txt',#8187.56KiB
       'large':'-i ../test/combinational-logic/crc/crc_1000x4194304.txt',#65536.06KiB
       'full name':'Cyclic-Redundancy Check'}
bfs = {'name':'bfs',
       'alias':'bfs',
       'default':'../test/graph-traversal/bfs/graph65536.txt',
       'full name':'Breadth-First Search'}
nw = {'name':'needle',
      'alias':'needle',
      'default':"2048 10",
      'full name':'Needleman-Wunsch'}
swat = {'name':'swat',
        'alias':'swat',
        'default':'../test/dynamic-programming/swat/query1K1 ../test/dynamic-programming/swat/sampledb1K1',
        'full name':'Smith-Waterman'}
nqueens = {'name':'nqueens',
           'alias':'nqueens',
           'default':'20',
           'full name':'N-Queens'}
hmm = {'name':'bwa_hmm',
       'alias':'bwa_hmm',
       'default':'-n 30 -v n',
       'full name':'Baum-Welch Algorithm, Hidden Markov Model'}
tdm = {'name':'tdm',
       'alias':'tdm',
       'default':'../test/finite-state-machine/tdm/sim-64-size200.csv ../test/finite-state-machine/tdm/ivl.txt ../test/finite-state-machine/tdm/30-episodes.txt 128',
       'full name':'Temporal Data Mining'}

#Dwarfs as clusters of Benchmarks:
dense_linear_algebra = [lud]
sparse_linear_algebra = [csr]
spectral_methods = [fft,dwt]
n_body_methods = [gem]
structured_grid_methods = [srad]
unstructured_grid_methods = [cfd]
combinational_logic = [crc]
graph_traversal = [bfs]
dynamic_programming = [nw,swat]
backtrack_branch_and_bound = [nqueens]
graphical_models = [hmm]
finite_state_machines = [tdm]
map_reduce = [kmeans]

dwarfs = dense_linear_algebra + sparse_linear_algebra + spectral_methods + n_body_methods + structured_grid_methods + unstructured_grid_methods + combinational_logic + graph_traversal + dynamic_programming + backtrack_branch_and_bound + graphical_models + finite_state_machines + map_reduce

#System specific device parameters
device_parameters = GenerateDeviceParameters(0,0,0)
device_name = "oclgrind"

##Most common metrics that effect performance as PAPI events:
papi_envs = [
#Time (not a PAPI event, so just use whatever is the default)
             {'name':'time',
              'parameters':''},
#Instructions per cycle (IPC)
#PAPI_TOT_CYC, PAPI_TOT_INS
             {'name':'instructions_per_cycle',
              'parameters':GeneratePAPIParameters('PAPI_TOT_CYC', 'PAPI_TOT_INS')},
#L1 Data Cache Request Rate
#PAPI_TOT_INS, PAPI_L1_DCA
#             {'name':'L1_data_cache_request_rate',
#              'parameters':GeneratePAPIParameters('PAPI_TOT_INS', 'PAPI_L1_DCA')},
#L1 Data Cache Miss Rate
#PAPI_TOT_INS, PAPI_L1_DCM
             {'name':'L1_data_cache_miss_rate',
              'parameters':GeneratePAPIParameters('PAPI_TOT_INS', 'PAPI_L1_DCM')},
#L1 Data Cache Miss Ratio
#PAPI_L1_DCA PAPI_L1_DCM
#             {'name':'L1_data_cache_miss_ratio',
#              'parameters':GeneratePAPIParameters('PAPI_L1_DCA', 'PAPI_L1_DCM')},
#L2 Data Cache Request Rate
#PAPI_TOT_INS PAPI_L2_DCA
             {'name':'L2_data_cache_request_rate',
              'parameters':GeneratePAPIParameters('PAPI_TOT_INS', 'PAPI_L2_DCA')},
#L2 Data Cache Miss Rate
#PAPI_TOT_INS PAPI_L2_DCM
             {'name':'L2_data_cache_miss_rate',
              'parameters':GeneratePAPIParameters('PAPI_TOT_INS', 'PAPI_L2_DCM')},
#L2 Data Cache Miss Ratio
#PAPI_L2_DCA PAPI_L2_DCM
             {'name':'L2_data_cache_miss_ratio',
              'parameters':GeneratePAPIParameters('PAPI_L2_DCA', 'PAPI_L2_DCM')},
#L3 Total Cache Request Rate
#PAPI_TOT_INS PAPI_L3_TCA
             {'name':'L3_total_cache_request_rate',
              'parameters':GeneratePAPIParameters('PAPI_TOT_INS', 'PAPI_L3_TCA')},
#L3 Total Cache Miss Rate
#PAPI_TOT_INS PAPI_L3_TCA
             {'name':'L3_total_cache_miss_rate',
              'parameters':GeneratePAPIParameters('PAPI_TOT_INS', 'PAPI_L3_TCM')},
#L3 Cache (can only use total cache instead of data cache events) Miss Ratio
#PAPI_L3_TCA PAPI_L3_TCM
             {'name':'L3_total_cache_miss_ratio',
              'parameters':GeneratePAPIParameters('PAPI_L3_TCA', 'PAPI_L3_TCM')},
#Translation Lookaside Buffer Misses:
#PAPI_TOT_INS PAPI_TLB_DM 
             {'name':'data_translation_lookaside_buffer_miss_rate',
              'parameters':GeneratePAPIParameters('PAPI_TOT_INS', 'PAPI_TLB_DM')},
#Branch Rate:
#PAPI_TOT_INS PAPI_BR_INS
             {'name':'branch_rate',
              'parameters':GeneratePAPIParameters('PAPI_TOT_INS', 'PAPI_BR_INS')},
#Branch Misprediction Rate:
#PAPI_TOT_INS PAPI_BR_INS
             {'name':'branch_misprediction_rate',
              'parameters':GeneratePAPIParameters('PAPI_TOT_INS', 'PAPI_BR_MSP')},
#Branch Misprediction Ratio:
#PAPI_BR_INS PAPI_BR_MSP
             {'name':'branch_misprediction_ratio',
              'parameters':GeneratePAPIParameters('PAPI_BR_INS', 'PAPI_BR_MSP')},
#RAPL Energy Measurements:
#rapl:::PP0_ENERGY:PACKAGE0, Energy used by all cores in package 0 (units nJ)
             {'name':'cpu_energy_nanojoules',
              'parameters':GeneratePAPIParameters('rapl:::PP0_ENERGY:PACKAGE0', 'rapl:::DRAM_ENERGY:PACKAGE0')},
#nvml Energy Measurements:
#nvml:::GeForce_GTX_1080:power, Power usage readings for the device (units mW) in miliwatts. This is the power draw (+/-5 watts) for the entire board: GPU, memory etc.
#nvml:::GeForce_GTX_1080:temperature, current temperature readings for the device, in degrees C.
             {'name':'gpu_energy_milliwatts',
                     'parameters':GeneratePAPIParameters('nvml:::GeForce_GTX_1080:power', 'nvml:::GeForce_GTX_1080:temperature')},
            ]

##just get time (no papi events)
#papi_env = papi_envs[0]
##just get the energy
#papi_env = papi_envs[13]
#RunApplication(kmeans,cpu_parameters,5,papi_env['parameters'])
#StoreRun(kmeans,'results/kmeans_'+papi_env['name'])

#so to find the cache performance steps of kmeans on i7 960@dynamic frequency,
#over the range of 1.60GHz-3.20GHz:
#for papi_env in papi_envs:
#    RunApplication(kmeans,cpu_parameters,40,papi_env['parameters'])
#    StoreRun(kmeans,'results/kmeans_8_cores_'+papi_env['name'])

#increasing the maximum number of clusters to find increases the amount of
#computation and thus the run time
#selected_papi_envs = papi_envs
selected_papi_envs = []
#selected_papi_envs.extend([x for x in papi_envs if x['name'] == 'cpu_energy_nanojoules'])
#selected_papi_envs.extend([x for x in papi_envs if x['name'] == 'gpu_energy_milliwatts'])
selected_papi_envs.extend([x for x in papi_envs if x['name'] == 'time'])
#selected_papi_envs.extend([x for x in papi_envs if x['name'] == 'L1_data_cache_miss_rate'])
#selected_papi_envs.extend([x for x in papi_envs if x['name'] == 'L2_data_cache_miss_rate'])
#selected_papi_envs.extend([x for x in papi_envs if x['name'] == 'L3_total_cache_miss_rate'])

if selected_applications == None:
    selected_applications = dwarfs
    #selected_applications = [
    #                         #kmeans,
    #                         #lud,
    #                         #csr,
    #                         #fft,
    #                         dwt,
    #                         #gem,
    #                         #srad,
    #                         #crc,
    #                        ]
else:
    exec("%s = [%s]"%("selected_applications",selected_applications))

#if running the whole list of dwarfs, we need to flatten the list first
#selected_applications = reduce(lambda x,y :x+y ,dwarfs)

selected_repetitions = 1
selected_device = device_parameters

selected_problem_sizes = ['tiny',
                          'small',
                          'medium',
                          'large',
                          ]
#instrument all applications
for application in selected_applications:
    for problem_size in selected_problem_sizes:
        all_good = RunApplicationWithArguments(application,
                                               str(application[str(problem_size)]),
                                               selected_device,
                                               selected_repetitions,
                                               str(oclgrind + " --workload-characterisation "))
        if all_good:
            count = 0
            file_name = "aiwc_" + application['name'] + "_" + problem_size + "_" + str(count) + ".zip"
            from os.path import isfile
            while isfile(file_name):
                count = count + 1
                file_name = "aiwc_" + application + "_" + problem_size + "_" + count + ".zip"

            import glob
            files_to_zip = glob.glob("aiwc_*.csv")
            files_to_zip = files_to_zip + glob.glob("aiwc_*_itb.log")

            import zipfile
            with zipfile.ZipFile(file_name, 'w') as myzip:
                for file_to_zip in files_to_zip:
                    myzip.write(file_to_zip)
            
            from os import remove 
            for file_to_zip in files_to_zip:
                remove(file_to_zip)

            print("Successfully zipped the architecture independent workload characterisation results to {}".format(file_name))
        else:
            import ipdb
            ipdb.set_trace()

