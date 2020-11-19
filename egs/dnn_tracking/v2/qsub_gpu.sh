#!/bin/bash

if [ $# != 1 ]; then
  echo "Usage: $0 <script>"
  exit 1
fi

rm qsub.log
qsub -cwd -j y -o qsub.log -l gpu=1 -V $1

