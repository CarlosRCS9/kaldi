#!/bin/bash
# Copyright 2020 Carlos Castillo
# Apache 2.0.

data_folder=data/dihardii/
output_folder=/export/b03/carlosc/data/2020/augmented/dihardii/

for name in development evaluation; do
  echo $data_folder$name/ref.rttm
  echo $output_folder$name
done