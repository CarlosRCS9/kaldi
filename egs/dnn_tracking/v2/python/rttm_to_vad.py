#!/usr/bin/env python3
#
# Copyright 2020 Carlos Castillo
# Apache 2.0.

from cut import Rttm, Cut, cuts_to_recordings
import argparse
import os
import sys

def get_args():
    parser = argparse.ArgumentParser(description = 'This script generates an oracle vad.scp in the output directory using the ref.rttm from the data directory')
    parser.add_argument('data_dir', type = str, help = 'Kaldi data directory, at least must contain ref.rttm, utt2num_frames, utt2dur')
    parser.add_argument('--output-dir', type = str, default = None, help = 'Output data directory, by default is the same as the data directory')
    parser.add_argument('--min-duration', type = float, default = None, help = 'Minimum duration allowed for cuts')
    args = parser.parse_args()
    return args

def main():
    args = get_args()
    args.output_dir = args.data_dir if args.output_dir is None else args.output_dir
    if not os.path.isdir(args.data_dir):
        sys.exit(args.data_dir + ' must be a directory')
    if os.path.isfile(args.output_dir):
        sys.exit(args.output_dir + ' must not be a file')
    if not os.path.isdir(args.output_dir):
        os.makedirs(args.output_dir)
    if not os.path.isfile(args.data_dir + '/ref.rttm'):
        sys.exit(args.data_dir + '/ref.rttm not found')
    if not os.path.isfile(args.data_dir + '/utt2num_frames'):
        sys.exit(args.data_dir + '/utt2num_frames not found')
    if not os.path.isfile(args.data_dir + '/utt2dur'):
        sys.exit(args.data_dir + '/utt2dur not found')
    if args.min_duration is None or args.min_duration < 0:
        if os.path.isfile(args.data_dir + '/frame_shift'):
            f = open(args.data_dir + '/frame_shift', 'r')
            try:
                args.min_duration = float(f.readline())
            except:
                pass
            f.close()
        if args.min_duration is None:
            args.min_duration = 0.0

    cuts = []
    f = open(args.data_dir + '/ref.rttm', 'r')
    for line in f.readlines():
        cuts.append(Cut(Rttm(line)))
    f.close()
    recordings = cuts_to_recordings(cuts, array = False)

    for recording_id in sorted(recordings.keys()):
        recording = recordings[recording_id]
        recording.explicit_overlap()
        print(recording, end = '')

if __name__ == '__main__':
    main()

