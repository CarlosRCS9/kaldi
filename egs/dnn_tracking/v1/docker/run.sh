docker run -it --rm -u $UID:$UID -v "$(pwd):/opt/kaldi/egs_external" -v /mnt/ST001/data:/export/b03/carlosc/data -p 8888:8888 --gpus "device=0" crcs/pytorch-kaldi
