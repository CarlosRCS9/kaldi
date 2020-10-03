#!/bin/bash
cd /export/b03/carlosc/repositories/kaldi/egs/albayzin/v2
. ./path.sh
( echo '#' Running on `hostname`
  echo '#' Started at `date`
  echo -n '# '; cat <<EOF
exp/xvector_nnet_1a/log/init_model.log nnet3-init --srand=123 exp/xvector_nnet_1a/configs/final.config exp/xvector_nnet_1a/0.raw 
EOF
) >hostname=!b18*&b*
time1=`date +"%s"`
 ( exp/xvector_nnet_1a/log/init_model.log nnet3-init --srand=123 exp/xvector_nnet_1a/configs/final.config exp/xvector_nnet_1a/0.raw  ) 2>>hostname=!b18*&b* >>hostname=!b18*&b*
ret=$?
time2=`date +"%s"`
echo '#' Accounting: time=$(($time2-$time1)) threads=1 >>hostname=!b18*&b*
echo '#' Finished at `date` with status $ret >>hostname=!b18*&b*
[ $ret -eq 137 ] && exit 100;
touch ./q/sync/done.41337
exit $[$ret ? 1 : 0]
## submitted with:
# qsub -v PATH -cwd -S /bin/bash -j y -l arch=*64* -o ./q/hostname=!b18*&b*    /export/b03/carlosc/repositories/kaldi/egs/albayzin/v2/./q/hostname=!b18*&b*.sh >>./q/hostname=!b18*&b* 2>&1
