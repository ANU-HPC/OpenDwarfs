/*
 *  Copyright 2008-2009 NVIDIA Corporation
 *
 *  Licensed under the Apache License, Version 2.0 (the "License");
 *  you may not use this file except in compliance with the License.
 *  You may obtain a copy of the License at
 *
 *      http://www.apache.org/licenses/LICENSE-2.0
 *
 *  Unless required by applicable law or agreed to in writing, software
 *  distributed under the License is distributed on an "AS IS" BASIS,
 *  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 *  See the License for the specific language governing permissions and
 *  limitations under the License.
 */

/*
 *  Compressed Sparse Row matrix (aka CRS)
 * valueType = float, IndexType = unsigned int
 */

typedef struct csr_matrix
{
    unsigned int index_type;
    float value_type;
    unsigned int num_rows, num_cols, num_nonzeros;

    unsigned int * Ap;  //row pointer
    unsigned int * Aj;  //column indices
    float * Ax;  //nonzeros
}
csr_matrix;

unsigned int * int_new_array(const size_t N) 
{ 
    //dispatch on location
    return (unsigned int*) malloc(N * sizeof(unsigned int));
}

float * float_new_array(const size_t N) 
{ 
    //dispatch on location
    return (float*) malloc(N * sizeof(float));
}

/*
 * The standard 5-point finite difference approximation
 * to the Laplacian operator on a regular N-by-N grid.
 */

csr_matrix laplacian_5pt(const unsigned int N)
{

    csr_matrix csr;
    csr.num_rows = N*N;
    csr.num_cols = N*N;
    csr.num_nonzeros = 5*N*N - 4*N; 

    csr.Ap = int_new_array(csr.num_rows+4);

    csr.Aj = int_new_array(csr.num_nonzeros);
    
    csr.Ax = float_new_array(csr.num_nonzeros);

    

    unsigned int nz = 0;
    unsigned int i = 0;
    unsigned int j = 0;
    unsigned int indx = 0;

    for(i = 0; i < N; i++){
        for(j = 0; j < N; j++){
            indx = N*i + j;

            if (i > 0){
                csr.Aj[nz] = indx - N;
                csr.Ax[nz] = -1;
                nz++;
            }

            if (j > 0){
                csr.Aj[nz] = indx - 1;
                csr.Ax[nz] = -1;
                nz++;
            }

            csr.Aj[nz] = indx;
            csr.Ax[nz] = 4;
            nz++;

            if (j < N - 1){
                csr.Aj[nz] = indx + 1;
                csr.Ax[nz] = -1;
                nz++;
            }

            if (i < N - 1){
                csr.Aj[nz] = indx + N;
                csr.Ax[nz] = -1;
                nz++;
            }
            
            csr.Ap[indx + 1] = nz;
        }
    }
    return csr;
}


