#!/bin/bash

rtve_2018_dev=/export/corpora5/RTVE/RTVE2018DB/dev2/audio
rtve_2018_test=/export/corpora5/RTVE/RTVE2018DB/test/audio/SD
rtve_2020_dev=/export/corpora5/RTVE/RTVE2020DB/dev/audio
rtve_2020_test=/export/corpora5/RTVE/RTVE2020DB/test/audio/SD

for dir in $rtve_2018_dev $rtve_2018_test $rtve_2020_dev $rtve_2020_test; do
  echo $dir
  dir_duration=0
  dir_count=0
  for name in $(ls $dir); do
    filepath=$dir/$name
    duration=$(ffprobe -i $filepath -show_entries format=duration -v quiet -of csv="p=0")
    dir_duration=$(echo $dir_duration + $duration | bc -l)
    dir_count=$(echo $dir_count + 1 | bc -l)
    echo $duration
  done
  #dir_mean=$(echo $dir_duration / $dir_count | bc -l)
  #echo total: $dir_duration s
  #echo total: $(echo $dir_duration / 3600 | bc -l) h
  #echo num files: $dir_count
  #echo mean: $dir_mean s
  #echo mean: $(echo $dir_mean / 3600 | bc -l) h
done
