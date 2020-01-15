#!/usr/bin/env python
from opendwarf_miner_utils import *

from sys import argv,exit
selected_applications = None

oclgrind = os.environ.get('OCLGRIND_BIN')
if oclgrind is None:
    oclgrind = 'oclgrind'

if len(argv) == 2:
    selected_applications = str(argv[1])
    print("Running Oclgrind on application:"+selected_applications)

exec(open('../opendwarf_application_parameters.py').read())

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
        try:
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
        except:
            print("No kernel of this problem size ", str(problem_size), " ", str(application))

