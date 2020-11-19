# Activate conda environment
export CONDA_ROOT=/export/b03/carlosc/miniconda3
. $CONDA_ROOT/etc/profile.d/conda.sh conda activate
conda activate wav2vec

python wav2vec_test.py
