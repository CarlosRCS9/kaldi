#!/bin/bash

base_folder=${1%/}
temp_folder=/export/b03/carlosc/data/temp

for folder in $(ls -d  $base_folder/*/); do
#for folder in $base_folder/128/; do
  folder_location=$( echo $folder | cut -d/ -f 7- )
  output_folder=$temp_folder/$folder_location
  mkdir -p $output_folder'exp'/make_ivectors
  mkdir -p $output_folder'exp'/make_xvectors
  cp $folder'exp'/make_ivectors/ivector.txt $output_folder'exp'/make_ivectors/ivector.txt
  cp $folder'exp'/make_xvectors/xvector.txt $output_folder'exp'/make_xvectors/xvector.txt
  cp $folder'ref.rttm' $output_folder'ref.rttm'
  cp $folder'segments' $output_folder'segments'
  rsync -r -e 'ssh -i /export/b03/carlosc/ccastillo-desktop-rodrigo.pem -p 1100' $temp_folder/ rodrigo@ccastillo.ddnsking.com:/mnt/ST001/data/2020
done
