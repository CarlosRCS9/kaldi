#!/bin/bash

# Copyright 2019 Carlos Castillo
# Apache 2.0.

. ./cmd.sh
. ./path.sh
set -e
stage=0

data_folder=$1
extractor_model=$2

echo $data_folder $extractor_model
