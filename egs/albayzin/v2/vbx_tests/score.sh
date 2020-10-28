#!/bin/bash
# Copyright 2020 Carlos Castillo
#
# Apache 2.0.

#ref_file=/export/b03/carlosc/repositories/kaldi/egs/albayzin/v2/data/rtve_2020_EXP022_eval/ref.rttm
ref_file=/export/b03/carlosc/repositories/kaldi/egs/albayzin/v2/data/rtve_2020_EXP008_oracle/ref.rttm
output_root=/export/b03/carlosc/repositories/kaldi/egs/albayzin/v2/vbx_tests
md_eval=/export/b03/carlosc/repositories/kaldi/egs/albayzin/v2/md.eval-v22.pl
speaker_eval=/export/b03/carlosc/repositories/kaldi/egs/albayzin/v2/tests/rttm_speaker_accuracy.py

if [[ $# != 1 ]]; then
  echo "Usage: $0 <src-dir>"
  echo " e.g.: $0 /export/b04/leibny/VBx-May2020/VBx/out_dir_albayzin2020_janto4dev"
  exit 1
fi

if [[ -d $1 ]]; then
  src_dir=$1
  src_name=$(basename $src_dir)
  output_dir=$output_root/$src_name
  mkdir -p $output_dir
  cat $src_dir/*.rttm > $output_dir/results.rttm
  cp $ref_file $output_dir/reference.rttm
  $md_eval -c 0.25 -b \
    -r $output_dir/reference.rttm \
    -s $output_dir/results.rttm \
    2> $output_dir/der.log \
    > $output_dir/der
  python3 $speaker_eval $output_dir/reference.rttm $output_dir/results.rttm > $output_dir/speaker
fi




