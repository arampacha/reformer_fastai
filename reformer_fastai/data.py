# AUTOGENERATED! DO NOT EDIT! File to edit: nbs/06_data.ipynb (unless otherwise specified).

__all__ = ['read_lines', 'convert_data_to_seq_length', 'read_and_prepare_data', 'TwinSequence', 'MaskTargCallback',
           'DeterministicTwinSequence']

# Cell
# Imports for data functions
import pandas as pd
import os
from .tokenizers import ByteTextTokenizer
from fastai.text.all import *
from torch.utils.data import Dataset
import time
from tqdm import tqdm

# Cell
def read_lines(path):
    """
    Tokenizes a text file.
    """
    assert os.path.exists(path)
    lines = []
    with open(path, 'r') as f:
        for line in f:
            lines.append(line)  # + ['<eos>'])
    return lines


def convert_data_to_seq_length(df, seq_length=2**16):
    """
    Take a dataframe text data and convert it to a dataframe with the same columns where
    every data sample is of numericalized token length of seq_length, except for the last example which is the remainder.
    (less than but closest to the value given)
    :param df: a pandas dataframe with columns [tokenized, lens] consisting of the numericalized tokens of text and their respective lengths
    :param seq_length: the numericalized token sequence length to split the data into
    :return: the new dataframe with split data samples
    """
    concat_data = to_concat(list(df['tokenized']))
    result = pd.DataFrame(columns=['tokenized', 'lens'])
    n_seqs = len(concat_data)//seq_length
    for i in tqdm(range(n_seqs), desc="Splitting data", total=n_seqs):
        sample = concat_data[i*seq_length:(i+1)*seq_length]
        result = result.append(
            {
                'tokenized': sample,
                'lens': len(sample),
            },
            ignore_index=True)
    # Add last data sample which is the remainder
    sample = concat_data[n_seqs*seq_length:]
    if len(sample) > 0:
        result = result.append(
        {
            'tokenized': sample,
            'lens': len(sample),
        },
        ignore_index=True)
    return result


def read_and_prepare_data(data_path, seq_length=0):
    """
    Read the data from file, and prepare the dataframe.
    This does not include splitting into train and validation sets.
    :param data_path: relative path to the raw data
    :param seq_length: sequence length to split data into, default is don't change data sample length
    :return: the dataframe after preparations
    """
    print("Reading data from path...")
    # Read the data from file
    enwik8 = read_lines(data_path)
    df = pd.DataFrame({'text': enwik8})
    print("Done!")

    time.sleep(0.5)  # this is so the printing of the progress bar is not weird
    # Initialize the BTT
    btt = ByteTextTokenizer(is_lm=True, add_bos=True, add_eos=True)

    # Modify dataset for training
    tqdm.pandas(desc="Tokenizing data")
    df['tokenized'] = df['text'].progress_map(lambda x: btt(x))

    # By default we won't change the data sample length
    if seq_length != 0:
        print("Sequence length has been added, splitting data to samples with sequence length " + str(seq_length))
        # Convert data samples according to sequence length
        df = convert_data_to_seq_length(df, seq_length)
        print("Done!")
    else:
        df['lens'] = df['text'].map(lambda x: len(x))

    df['lens_cum_sum'] = df.lens.cumsum()

    return df

# Cell
class TwinSequence(Dataset):
    def __init__(self, sl=1024, len=100, seed=None):
        assert sl%2 == 0
        self.sl = sl
        self.len = len
        if seed is not None:
            torch.manual_seed(seed)
    def __getitem__(self, idx):
        seq = torch.randint(1,128,(self.sl//2,))             # w: [1-127] of len sl//2
        seq[0] = 0                                           # seq = 0w
        seq = torch.cat((seq,seq), -1)                       # seq = 0w0w
        target = torch.cat((seq[1:],torch.tensor([0])), -1)  # return offset target x:[0123], y:[1230]
        return (seq, target)
    def __len__(self):
        return self.len

# Cell
class MaskTargCallback(Callback):
    def before_batch(self):
        self.y[:, :self.dls.train_ds.sl//2] = -100

# Cell
class DeterministicTwinSequence(Dataset):
    def __init__(self, sl=1024, n_items=100, seed=None):
        assert sl%2 == 0
        self.items, self.target = self._create_ds(sl, n_items, seed)

    def __getitem__(self, idx):
        return (self.items[idx], self.target[idx])

    def __len__(self):
        return len(self.items)

    def _create_ds(self, sl, n_items, seed):
        if seed is not None:
            torch.manual_seed(seed)
        items = torch.randint(1,128,(n_items, sl//2))
        items[:,0] = 0                                                        # seq = 0
        items = torch.cat((items,items), -1)                                  # seq = 0w0w
        target = torch.cat((items[:,1:],torch.zeros_like(items[:,-1:])), -1)  # offset target x:[0123], y:[1230]
        return items, target