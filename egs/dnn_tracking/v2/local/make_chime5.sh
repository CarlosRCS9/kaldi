#!/bin/bash
# Copyright 2020 Carlos Castillo
#
# Apache 2.0

if [[ $# != 2 ]]; then
	echo "Usage: $0 <path-to-chime5> <dataset>"
	echo "e.g.: $0 /export/corpora5/CHiME5 train"
	exit 1
fi

if [[ "$2" = "dev" ]] || [[ "$2" = "eval" ]] || [[ "$2" = "train" ]]; then
	dataset=$2
else
	echo "Usage: $0 <dataset> must be dev, eval or train"
	exit 1
fi

