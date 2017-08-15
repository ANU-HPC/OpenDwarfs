#/usr/bin/env python
from opendwarf_miner_utils import *

#Benchmark parameters:
kmeans = {'name':'kmeans',
          'alias':'kmeans',
          'default':'-i ../test/dense-linear-algebra/kmeans/65536_34f.txt',
          'tiny':'-g -p 26 -f 256',     #< 32K, object increments of 1KiB
          'small':'-g -p 26 -f 2048',   #< 256K, object increments of 8KiB
          'medium':'-g -p 26 -f 65536', #< 8196K, object increments of 256KiB
          'large':'-g -p 26 -f 524288', #> 8196K, object increments of 2048KiB
          'full name':'K-Means Clustering'}
kmeans_coarse_iteration_profile = {
        'name':'kmeans_profiling_outer_loop',
        'alias':'kmeans',
        'default':'-i ../test/dense-linear-algebra/kmeans/65536_34f.txt',
        'tiny':'-g -p 26 -f 256',     # 1KiB
        'small':'-g -p 26 -f 2048',   # 8KiB
        'medium':'-g -p 26 -f 65536', # 256KiB
        'large':'-g -p 26 -f 524288', # 2048KiB
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
       'full name':'Compressed Sparse Row'}
fft = {'name':'clfft',
       'alias':'clfft',
       'default':'--pts 1',
       'full name':'Fast Fourier Transform'}
gem = {'name':'gem',
       'alias':'gem',
       'default':"../test/n-body-methods/gem/nucleosome 80 1 0",
       'full name':'Gemnoui'}
srad = {'name':'srad',
        'alias':'srad',
        'default':'256 256 0 127 0 127 0.5 2',
        'full name':'Speckle Reducing Anisotropic Diffusion'}
cfd = {'name':'cfd',
       'alias':'cfd',
       'default':'../test/unstructured-grids/cfd/fvcorr.domn.097K',
       'full name':'Computational Fluid Dynamics'}
crc = {'name':'crc',
       'alias':'crc',
       'default':'-i ../test/combinational-logic/crc/crc_1000x8192.txt',
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
dense_linear_algebra = [kmeans,lud]
sparse_linear_algebra = [csr]
spectral_methods = [fft]
n_body_methods = [gem]
structured_grid_methods = [srad]
unstructured_grid_methods = [cfd]
combinational_logic = [crc]
graph_traversal = [bfs]
dynamic_programming = [nw,swat]
backtrack_branch_and_bound = [nqueens]
graphical_models = [hmm]
finite_state_machines = [tdm]

#System specific device parameters
cpu_parameters = GenerateDeviceParameters(0,0,0)
gpu_parameters = GenerateDeviceParameters(1,0,1)

#Sample usage of utils:
#RunDwarf(dense_linear_algebra,cpu_parameters)

#Sample Usage with Papi to find L1 Cache performance:
#papi_env=GeneratePAPIParameters("PAPI_L1_TCA", #total L1 cache access
#                                "PAPI_L1_DCM") #L1 data cache misses
#RunApplication(kmeans,cpu_parameters,50,papi_env)
#StoreRun(kmeans,'kmeans_default_l1_cache_misses')

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
selected_papi_envs.extend([x for x in papi_envs if x['name'] == 'gpu_energy_milliwatts'])
selected_papi_envs.extend([x for x in papi_envs if x['name'] == 'time'])
#selected_papi_envs.extend([x for x in papi_envs if x['name'] == 'L1_data_cache_miss_rate'])
#selected_papi_envs.extend([x for x in papi_envs if x['name'] == 'L2_data_cache_miss_rate'])
#selected_papi_envs.extend([x for x in papi_envs if x['name'] == 'L3_total_cache_miss_rate'])

#selected_applications = [kmeans_coarse_iteration_profile]#kmeans]
selected_applications = [lud_coarse_iteration_profile]#kmeans]
#selected_applications.extend(dense_linear_algebra)

selected_repetitions = 300
selected_device = gpu_parameters
selected_problem_sizes = ['tiny','small','medium','large']
#instrument all applications
for application in selected_applications:
    for papi_env in selected_papi_envs:
        for problem_size in selected_problem_sizes:
            all_good = RunApplicationWithArguments(application,
                                                   application[str(problem_size)],
                                                   selected_device,
                                                   selected_repetitions,
                                                   papi_env['parameters'])
            if all_good:
                StoreRun(application,
                        'results/gpu_'+application['name']+'_'+problem_size+'_'+papi_env['name'])
            else:
                import ipdb
                ipdb.set_trace()
                #import sys
                #sys.exit()

##kmeans strider: increase the size of feature space to find to cache spillover sizes
#feature_sizes = [256,2048,65536,524288]
#repeats = 300
#for f in feature_sizes:
#    for o in range (5,48):
#        for papi_env in selected_papi_envs:
#             #'tiny':'-g -p 26 -f 256',     #< 32K, object increments of 1KiB
#             #'small':'-g -p 26 -f 2048',   #< 256K, object increments of 8KiB
#             #'medium':'-g -p 26 -f 65536', #< 8196K, object increments of 256KiB
#             #'large':'-g -p 26 -f 524288', #> 8196K, object increments of 2048KiB
#
#            all_good = RunApplicationWithArguments(kmeans,
#                                                   "-g -p {} -f {} -m 5 -n 5".format(o,f),
#                                                   cpu_parameters,
#                                                   repeats,
#                                                   papi_env['parameters'])
#            if all_good:
#                StoreRun(kmeans,"results/kmeans_{}_objects_{}_features_{}".format(o,f,papi_env['name']))
#            else:
#                import sys
#                sys.exit()

