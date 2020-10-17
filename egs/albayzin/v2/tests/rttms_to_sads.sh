for filepath in $(ls $1/*.rttm); do
  filename=${filepath%.*}
  new_filepath=$filename.sad
  cat $filepath | python3 tests/rttm_to_sad.py > $new_filepath
  #cat $filepath | python3 tests/rttm_to_sad.py
done
