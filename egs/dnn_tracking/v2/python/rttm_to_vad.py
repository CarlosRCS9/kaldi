#!/usr/bin/env python3
#
# Copyright 2020 Carlos Castillo
# Apache 2.0.

from cut import Rttm, Cut, cuts_to_recordings, write_kaldi_vector
import argparse
import os
import sys

def get_args():
    parser = argparse.ArgumentParser(description = 'This script generates an oracle vad.scp in the output directory using the ref.rttm from the data directory')
    parser.add_argument('data_dir', type = str, help = 'Kaldi data directory, at least must contain ref.rttm, utt2num_frames, utt2dur')
    parser.add_argument('--output-dir', type = str, default = None, help = 'Output data directory, by default is the same as the data directory')
    parser.add_argument('--frame-shift', type = float, default = None, help = 'Frame shift, overrides frame_shift in the data directory, default is 0.0')
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
    if args.frame_shift is None or args.frame_shift < 0:
        if os.path.isfile(args.data_dir + '/frame_shift'):
            f = open(args.data_dir + '/frame_shift', 'r')
            try:
                args.frame_shift = float(f.readline())
            except:
                pass
            f.close()
        if args.frame_shift is None:
            args.frame_shift = 0.0

    cuts = []
    f = open(args.data_dir + '/ref.rttm', 'r')
    for line in f.readlines():
        cuts.append(Cut(Rttm(line)))
    f.close()

    utt2num_frames ={}
    f = open(args.data_dir + '/utt2num_frames', 'r')
    for line in f.readlines():
        recording_id, num_frames = line.strip().split()
        if recording_id not in utt2num_frames:
            utt2num_frames[recording_id] = int(num_frames)
    f.close()

    recordings = cuts_to_recordings(cuts, array = False)
    recordings_vad = {}
    for recording_id in sorted(recordings.keys()):
        recording = recordings[recording_id]
        recording.explicit_overlap()
        vad = recording.get_vad(utt2num_frames[recording_id], args.frame_shift)
        recordings_vad[recording_id] = vad
    write_kaldi_vector(recordings_vad, args.output_dir + '/vad.scp', args.output_dir + '/vad.ark')

if __name__ == '__main__':
    main()

