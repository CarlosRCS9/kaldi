#!/usr/bin/env bash
# Copyright 2021 Carlos Castillo
#
# Apache 2.0

. ./path.sh
export CONDA_ROOT=/export/b03/carlosc/miniconda3
. $CONDA_ROOT/etc/profile.d/conda.sh conda activate
conda activate wav2vec

callhome_root=/export/corpora5/LDC/LDC2001S97
prefix=exp000_
audio_dir=audio
wav2vec_audio_dir=wav2vec_audio

stage=3

if [ $stage -le 0 ]; then
  local/make_callhome.sh $callhome_root data
fi

if [ $stage -le 1 ]; then
  for name in callhome1 callhome2; do
    data_dir=data/$name
    output_dir=data/${prefix}${name}
    echo "0.01" > $output_dir/frame_shift
    local/wav_scp_2_wav.sh $data_dir/wav.scp $output_dir $audio_dir false
    cp data/callhome/fullref.rttm $output_dir/ref.rttm
    python3 local/fix_ref_rttm.py $output_dir
  done
fi

if [ $stage -le 2 ]; then
  for name in callhome1 callhome2; do
    data_dir=data/${prefix}${name}
    output_dir=data/${prefix}wav2vec_${name}
    local/wav_2_wav2vec_wav.sh $data_dir $output_dir $wav2vec_audio_dir false
    cp -r $data_dir/{frame_shift,log,ref.rttm,split1utt,split4utt,utt2dur,utt2spk} $output_dir/
  done
fi

if [ $stage -le 3 ]; then
  for name in callhome1 callhome2; do
    data_dir=data/${prefix}wav2vec_${name}
    output_dir=$data_dir/wav2vec
    python local/extract_wav2vec.py $data_dir $output_dir --rename-speakers true
    cat ${output_dir}/utt2spk | utils/utt2spk_to_spk2utt.pl > ${output_dir}/spk2utt
  done
fi
