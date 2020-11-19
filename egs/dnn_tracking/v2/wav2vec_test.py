#def task(x):
import torch
from fairseq.models.wav2vec import Wav2VecModel

cp = torch.load('wav2vec_large.pt')
model = Wav2VecModel.build_model(cp['args'], task=None)
model.load_state_dict(cp['model'])
model.eval()

wav_input_16khz = torch.randn(1,10000)
z = model.feature_extractor(wav_input_16khz)
c = model.feature_aggregator(z)
print('hello world')

#import plz
#plz.map(task, range(1), jobs=1, gpus=1)
