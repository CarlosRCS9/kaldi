#!/usr/bin/env bash
# Copyright 2020 Carlos Castillo
#
# Apache 2.0.

if [ $# -lt 4 ]; then
  echo "Usage: $0 <mode> <path-to-rtve_2020_test_sd> <path-to-rttm> <path-to-output> <speaker-overlap> <speaker-rename>"
  echo " e.g.: $0 eval /export/corpora5/RTVE/RTVE2020DB/test/audio/SD december/test/RTVE2020-SDreference.rttm data/rtve_2020_test_sd true false"
  exit 1
fi

if [ $1 = "eval" ] || [ $1 = "oracle" ] || [ $1 = "train" ]; then
  mode=$1
else
  echo "Usage: $0 <mode> must be eval, oracle or train"
  exit 1
fi

data_dir=$2
rttm=$3
output_dir=$4
audio_dir=/export/b03/carlosc/repositories/kaldi/egs/albayzin/v2/data/audio
speaker_overlap=$([ ${5:-true} = true ] && echo true || echo false)
speaker_rename=$([ ${6:-false} = true ] && echo true || echo false)

rm -rf $output_dir
mkdir -p $output_dir

cat $rttm \
  | iconv -f utf8 -t ascii//TRANSLIT \
  | sed -e 's/SPKR/SPEAKER/' \
  | sed -e 's/SPEAKER-INFO/SPEAKER/' \
  | grep " <NA> " \
  > $output_dir/ref_original.rttm
sed "/unknown/d" -i $output_dir/ref_original.rttm
sed "/musica/d" -i $output_dir/ref_original.rttm
sed -e "s/$/ <NA>/" -i $output_dir/ref_original.rttm
# At this point the ref_original.rttm file has the standard sctructure, with no music and no unknown
cat $output_dir/ref_original.rttm \
  | python3 scripts/rttm_explicit_overlap.py \
  > $output_dir/ref.rttm
# At this point the ref.rttm file has the same data as the ref_original.rttm, but with explicit overlap
if [ $speaker_rename = true ]; then
  cat $output_dir/ref.rttm | python3 scripts/rttm_get_file_name.py rtve_2020_test_sd > $output_dir/recording_name

  cat $output_dir/ref.rttm | python3 scripts/rename.py $output_dir/recording_name > $output_dir/ref_tmp.rttm
  mv $output_dir/ref_tmp.rttm $output_dir/ref.rttm
  # At this point the ref.rttm file has new recordings ids
fi
if [ $mode = train ]; then
  cat $output_dir/ref.rttm \
    | python3 scripts/rttm_split.py 86400 0 --min-length=0.5 \
    > $output_dir/ref_tmp.rttm
  mv $output_dir/ref_tmp.rttm $output_dir/ref.rttm
  # At this point the ref.rttm has explicit overlaps and the segments shorter than 0.5 s have been removed
fi
if [ $speaker_overlap = false ]; then
  cat $output_dir/ref.rttm  \
    | python3 scripts/rttm_split_filter.py 86400 0 --max-file-speakers=1000 --max-segment-speakers=1 \
    > $output_dir/ref_tmp.rttm
  mv $output_dir/ref_tmp.rttm $output_dir/ref.rttm
  # At this point the ref.rttm does not have any overlapping speech instances
fi
python3 tests/rttm_to_rttms.py $output_dir/ref.rttm
if [ $speaker_rename = true ]; then
  cat $output_dir/ref.rttm | python3 scripts/rttm_get_speaker_name.py rtve_2020_test_sd_speaker > $output_dir/speaker_name
fi

# ------------------------- segments ------------------------- #
if [ $mode = "train" ]; then
  cat $output_dir/ref.rttm \
    | python3 scripts/rttm_to_segments.py > $output_dir/segments
  if [ $speaker_rename = true ]; then
    cat $output_dir/segments | python3 scripts/rename.py $output_dir/speaker_name > $output_dir/segments_tmp
    mv $output_dir/segments_tmp $output_dir/segments
  fi
fi

# ------------------------- utt2spk ------------------------- #
if [ $mode = "train" ]; then
  cat $output_dir/ref.rttm \
    | python3 scripts/rttm_to_utt2spk.py > $output_dir/utt2spk
  if [ $speaker_rename = true ]; then
    cat $output_dir/utt2spk | python3 scripts/rename.py $output_dir/speaker_name > $output_dir/utt2spk_tmp
    mv $output_dir/utt2spk_tmp $output_dir/utt2spk
  fi
fi

for filepath in $(ls -d $data_dir/*.aac); do
  if [ $speaker_rename = true ]; then
    name=$(basename $filepath .aac | python3 scripts/rename.py $output_dir/recording_name)
  else
    name=$(basename $filepath .aac)
  fi

  # ------------------------- utt2spk ------------------------- #
  if [ $mode = 'eval' ] || [ $mode = 'oracle' ]; then
    echo $name $name >> $output_dir/utt2spk
  fi

  # ------------------------- wav.scp ------------------------- #
  mkdir -p $audio_dir
  filepath_new=$audio_dir/${name}.wav
  if [ -f $filepath_new ]; then
    echo "$name $filepath_new" \
      >> $output_dir/wav.scp
  else
    echo "$name ffmpeg -i $filepath -f wav -ar 16000 -ac 1 $filepath_new; cat $filepath_new |" \
      >> $output_dir/wav.scp
  fi
done

if [ $mode = 'train' ]; then
  python3 scripts/segments_to_wav.py $output_dir $output_dir
  mv $output_dir/segments $output_dir/segments.backup
  mv $output_dir/segments_tmp $output_dir/segments
  mv $output_dir/wav.scp $output_dir/wav.scp.backup
  mv $output_dir/wav_tmp.scp $output_dir/wav.scp
fi

# ------------------------- spk2utt ------------------------- #
cat $output_dir/utt2spk | utils/utt2spk_to_spk2utt.pl > $output_dir/spk2utt

# ------------------------- reco2num_spk ------------------------- #
if [ $mode = "oracle" ] || [ $mode = "train" ]; then
  cat $output_dir/ref.rttm | python3 scripts/rttm_to_reco2num_spk.py > $output_dir/reco2num_spk
fi

utils/fix_data_dir.sh $output_dir



                

