#!/bin/bash

# $1 input1, $2 input1 start, $3 input1 length
# $4 input2, $5 input2 start, $6 input2 length
# $7 output1

sox -m "|sox $1 -t sph - trim $2 $3" "|sox $4 -t sph - trim $5 $6" $7
#echo "sox -m \"|sox $1 -t sph - trim $2 $3\" \"|sox $4 -t sph - trim $5 $6\" $7"
