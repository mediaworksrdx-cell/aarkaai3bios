#!/usr/bin/env bash
set -ex
export CUDACXX=/opt/pytorch/lib/python3.13/site-packages/nvidia/cu13/bin/nvcc
export CUDA_HOME=/opt/pytorch/lib/python3.13/site-packages/nvidia/cu13
export PATH=/opt/pytorch/lib/python3.13/site-packages/nvidia/cu13/bin:$PATH
export LD_LIBRARY_PATH=/opt/pytorch/lib/python3.13/site-packages/nvidia/cu13/lib:$LD_LIBRARY_PATH
export CMAKE_ARGS="-DGGML_CUDA=on"
python3.13 -m pip install --force-reinstall --no-cache-dir llama-cpp-python==0.3.31
