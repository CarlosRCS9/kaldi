## DNN model
```python
class Net(nn.Module):
    def __init__(self, models_container_length, vector_length):
        super().__init__()
        n = models_container_length
        m = vector_length
        self.cnn1 = nn.Sequential(
            nn.Conv1d((n + 1), n ** 3, 3),
            nn.ReLU(),
            nn.Conv1d(n ** 3, n ** 2, 3),
            nn.ReLU(),
            nn.Conv1d(n ** 2, n, 3),
            nn.ReLU(),
        )
        self.fc1 = nn.Sequential(
            nn.Linear(n * (m - 6), n * 32),
            nn.ReLU(),
            nn.Linear(n * 32, n * 16),
            nn.ReLU(),
            nn.Linear(n * 16, n),
            nn.Sigmoid(),
        )
        
    def forward(self, input):
        x = torch.stack(input, 1)
        x = self.cnn1(x)
        x = x.view(x.shape[0], -1)
        x = self.fc1(x)
        return x
```
## DNN trainer
```python
lr = 0.0001
epochs = 50
validation_threshold = 0.07
```
## Parameters
```python
a_directory = '../exp/pre_norm/dihard_2019_dev/json'
a_groundtruth = '../data/dihard_2019_dev_1.0_0.5.rttm'
b_directory = '../exp/pre_norm/dihard_2019_eval/json'
b_groundtruth = '../data/dihard_2019_eval_1.0_0.5.rttm'
maximum_speakers_length = 2
valid_speakers_ids = ['A', 'B']
include_overlaps = False
vector = 'ivectors'
vector_length = 400 if vector == 'ivectors' else 512
models_container_length = 2
models_container_include_zeros = True
models_container_include_overlaps = False
models_generation_length = 20
models_generation_selection = 'first'
balance_segments_selection = 'copy'
batch_size = 32
```