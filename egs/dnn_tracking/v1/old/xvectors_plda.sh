#!/bin/bash

cd ..

. ./cmd.sh
. ./path.sh
set -e

target_energy=0.1
cleanup=true

if [ $# != 3 ]; then
	echo "Usage: $0 <plda-dir> <ref-xvector> <test-xvector>"
	exit 1;
fi

pldadir=$1
refxvec=$2
testxvec=$3

tmpdir=tmp_$(head /dev/urandom | tr -dc A-Za-z0-9 | head -c 13 ; echo '')
mkdir -p $tmpdir

echo plda reference test > $tmpdir/reco2utt
echo reference $refxvec > $tmpdir/xvectors.1.ark
echo test $testxvec >> $tmpdir/xvectors.1.ark

ivector-plda-scoring-dense --target-energy=$target_energy \
  $pldadir \
  ark:$tmpdir/reco2utt \
  ark:$tmpdir/xvectors.1.ark \
  ark,t:$tmpdir/scores.1.ark || exit 1;

#cat $tmpdir/scores.1.ark
cat $tmpdir/scores.1.ark | grep -Eo '[0-9]+\.[0-9]+' | sed -n 2p

if $cleanup ; then
  rm -rf $tmpdir || exit 1;
fi

cd notebooks

