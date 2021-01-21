#!/bin/bash

if [ $# != 1 ]; then
  echo "Usage: $0 <script>"
  exit 1
fi

rm -f qsub.log
qsub -cwd -j y -o qsub.log -l gpu=1,mem_free=60G,ram_free=60G -V $1

