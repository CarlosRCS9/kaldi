#!/bin/bash

data_folder=/export/b03/carlosc/data/2020/augmented
temp_folder=/export/b03/carlosc/data/temp

for callhome in callhome1 callhome2; do
  for length in 0.5_0.1_0.5 1.0_0.3_0.5 1.5_0.5_0.5; do
    for dimension in 128 400; do
      mkdir -p $temp_folder/callhome/$callhome/augmented_0/$length/$dimension/exp/make_ivectors
      cp $data_folder/callhome/$callhome/augmented_0/$length/$dimension/segments $temp_folder/callhome/$callhome/augmented_0/$length/$dimension/
      cp $data_folder/callhome/$callhome/augmented_0/$length/$dimension/exp/make_ivectors/ivector.txt $temp_folder/callhome/$callhome/augmented_0/$length/$dimension/exp/make_ivectors/
    done
    cp $data_folder/callhome/$callhome/augmented_0/$length/ref.rttm $temp_folder/callhome/$callhome/augmented_0/$length/
  done
done

