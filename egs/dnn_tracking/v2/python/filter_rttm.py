# -*- coding: utf-8 -*-
#!/usr/bin/env python3
#
# Copyright 2020 Carlos Castillo
# Apache 2.0.

import sys
sys.path.insert(0, 'python')
from cut import Rttm, Cut, cuts_to_recordings

def get_stdin():
  return sys.stdin

def main():
  stdin = get_stdin()
  cuts = [Cut(Rttm(line)) for line in stdin]
  recordings = cuts_to_recordings(cuts, array = False)
  recordings_cuts = {}
  for recording_id in recordings:
    recordings[recording_id].explicit_overlap()
    recordings_cuts[recording_id] = [Cut(cut) for cut in recordings[recording_id].get_cuts() \
      if cut.get_speakers_length() == 1]
  for recording_id in recordings_cuts:
    for cut in recordings_cuts[recording_id]:
      print(cut.get_rttm_string(0.01))

if __name__ == '__main__':
  main()

