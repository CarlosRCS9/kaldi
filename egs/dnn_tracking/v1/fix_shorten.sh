#!/bin/bash

. ./cmd.sh
. ./path.sh

folder=/export/b03/carlosc/data/NIST/LDC2001S97/sid00sg1/data

while read line; do
  sph2pipe=$(echo $line | sed -E 's/\w*\s//' | sed 's/\ |//')
  filename=$(echo $sph2pipe | rev | cut -d'/' -f 1 | rev)
  new_filename=$(echo $filename | cut -d'.' -f 1).wav
  new_filepath=$folder/$new_filename
  new_line=$(echo $line | cut -d' ' -f 1)" "$new_filepath
  $sph2pipe $new_filepath
  echo $new_line
done < <(cat "$1" - )
