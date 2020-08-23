#!/bin/bash

folder=batch/20200821/table2

for experiment_folder in $(ls -d $folder/*a/); do
  if [[ $experiment_folder == *'callhome'* ]]; then
   dataset=callhome
  elif [[ $experiment_folder == *'dihard'* ]]; then
    dataset=dihard
  else
    echo 'unknown dataset'
    exit 1
  fi
  python_folder=${experiment_folder%/}
  echo -n $python_folder' '
  python3 update_results_filter_recordings.py $dataset 0.52 $python_folder
done

# for experiment_folder in $(ls -d $folder/*a/); do
#   if [[ $experiment_folder == *'callhome'* ]]; then
#     dataset=callhome
#   elif [[ $experiment_folder == *'dihard'* ]]; then
#     dataset=dihard
#   else
#     echo 'unknown dataset'
#     exit 1
#   fi
#   python_folder=${experiment_folder%/}
#   echo -n $python_folder' '
#   python3 update_results_filter_recordings.py $dataset 0.17 $python_folder
# done

#for experiment_folder in $(ls -d $folder/*a/); do
#  if [[ $experiment_folder == *'callhome'* ]]; then
#    dataset=callhome
#  elif [[ $experiment_folder == *'dihard'* ]]; then
#    dataset=dihard
#  else
#    echo 'unknown dataset'
#    exit 1
#  fi
#  python_folder=${experiment_folder%/}
#  echo -n $python_folder' '
#  python3 update_results_filter_recordings.py $dataset 0.35 $python_folder
#done
