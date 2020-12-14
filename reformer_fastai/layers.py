# AUTOGENERATED! DO NOT EDIT! File to edit: nbs/01_layers.ipynb (unless otherwise specified).

__all__ = ['Residual', 'PostNorm', 'PreNorm', 'FeedForward', 'AbsolutePositionalEmbedding', 'FixedPositionalEmbedding',
           'TransformerEmbedding', 'ByteTextTokenizer']

# Cell
import torch
from torch import nn, einsum
import torch.nn.functional as F
from fastai.basics import *
from fastai.text.all import *

from functools import partial, reduce, wraps
from operator import mul

from torch import Tensor
from typing import Tuple

from einops import rearrange, repeat
try:
    from axial_positional_embedding import AxialPositionalEmbedding, AxialPositionalEmbeddingImage
except ImportError as e:
    print(e)

from .core import *

# Cell
class Residual(Module):
    """Add skip-connection: out = x + sublayer(x)"""
    def __init__(self, sublayer:Module): store_attr()
    def forward(self, x, *args, **kwargs):
        return x + self.sublayer(x, *args, **kwargs)

# Cell
class PostNorm(Module):
    """Adds LayerNorm after sublayer"""
    def __init__(self, d_model:int, sublayer:Module):
        store_attr('sublayer')
        self.norm = nn.LayerNorm(d_model)

    def forward(self, x, *args, **kwargs):
        x = self.sublayer(x, *args, **kwargs)
        return self.norm(x)

# Cell
class PreNorm(Module):
    """Adds LayerNorm before sublayer"""
    def __init__(self, d_model:int, sublayer:Module):
        store_attr('sublayer')
        self.norm = nn.LayerNorm(d_model)

    def forward(self, x, *args, **kwargs):
        x = self.norm(x)
        return self.sublayer(x, *args, **kwargs)

# Cell
class FeedForward(Module):
    """
    Simple positional feed-forward module with GELU activation function.
    If d_ff is None defaults to 4*d_model
    """
    def __init__(self, d_model:int, d_ff:int=None, dropout:float=0.):
        d_ff = default(d_ff, 4 * d_model)
        layers = [nn.Linear(d_model, d_ff), nn.GELU(), nn.Dropout(dropout),
                    nn.Linear(d_ff, d_model), nn.Dropout(dropout)]
        self.net = nn.Sequential(*layers)
        self._init()

    def forward(self, x):
        return self.net(x)

    def _init(self):
        [nn.init.xavier_uniform_(p) for p in self.parameters() if p.dim() > 1]

# Cell
class AbsolutePositionalEmbedding(Module):
    """Learnable absolute positional encodings"""
    def __init__(self, d_emb:int, max_seq_len:int):
        self.emb = nn.Embedding(max_seq_len, d_emb)

    def forward(self, x):
        t = torch.arange(x.shape[1], device=x.device)
        return self.emb(t)

# Cell
class FixedPositionalEmbedding(Module):
    """Fixed positional encodings"""
    def __init__(self, d_emb:int):
        inv_freq = 1. / (10000 ** (torch.arange(0, d_emb, 2).float() / d_emb))
        self.register_buffer('inv_freq', inv_freq)

    def forward(self, x):
        t = torch.arange(x.shape[1], device=x.device).type_as(self.inv_freq)
        sinusoid_inp = torch.einsum("i,j->ij", t, self.inv_freq)
        emb = torch.cat((sinusoid_inp.sin(), sinusoid_inp.cos()), dim=-1)
        return emb[None, :, :]

# Cell
class TransformerEmbedding(Module):
    """
    Combines token embedings with positional encodings
    pos_enc: str from {'absolute', 'fixed', 'axial'}
    """
    def __init__(self,
                 emb_sz:int,
                 d_emb:int,
                 max_seq_len:int=512,
                 dropout:float=0.,
                 pos_enc:str='absolute',
                 axial_shape:Tuple=None,
                 axial_emb_dims:Tuple=None):
        store_attr('d_emb')
        self.scale = d_emb ** 0.5
        self.std = 0.02    # fairseq: d_emb ** -0.5, fastai: 0.01
        self.emb = nn.Embedding(emb_sz, d_emb)
        self.dropout = nn.Dropout(dropout)

        if pos_enc == 'absolute': self.pos_enc = AbsolutePositionalEmbedding(d_emb, max_seq_len)
        elif pos_enc == 'fixed': self.pos_enc = FixedPositionalEmbedding(d_emb)
        elif pos_enc == 'axial':
            assert axial_shape is not None
            assert reduce(mul, axial_shape) == max_seq_len
            axial_emb_dims = default(axial_emb_dims, get_axial_dims(d_emb, len(axial_shape)))
            self.pos_enc = AxialPositionalEmbedding(d_emb, axial_shape, axial_emb_dims)
        self._init()

    def forward(self, x):
        x = self.emb(x)  #* self.scale
        x *= self.scale
        x += self.pos_enc(x)
        return self.dropout(x)

    def _init(self):
        nn.init.trunc_normal_(self.emb.weight, std = self.std)
        if hasattr(self.pos_enc, 'weight'): nn.init.trunc_normal_(self.pos_enc.weight, std = self.std)

# Cell
import six
from fastai.text.all import *

# Cell
class ByteTextTokenizer(Transform):
    """
        Encodes each byte to an id. For 8-bit strings only.
        Credit: https://github.com/tensorflow/tensor2tensor/blob/5f9dd2db6d7797162e53adf152310ed13e9fc711/tensor2tensor/data_generators/text_encoder.py#L176
    """
    def __init__(self, is_lm=True, add_bos=False, add_eos=False):
        store_attr('is_lm, add_bos, add_eos')
        self.pad_token, self.eos_token, self.bos_token = '<pad>', '<eos>', '<bos>',
        self.pad_token_id, self.eos_token_id, self.bos_token_id = 0,1,2
        self.reserved_toks = [self.pad_token, self.eos_token, self.bos_token]  ## self.bos_token_id
        self.reserved_tokens_bytes = [bytes(rtok, 'ascii') for rtok in self.reserved_toks]
        self.numres = len(self.reserved_toks)
        self.int2byte = six.int2byte

    @typedispatch
    def __call__(self, o:list, **kwargs):
        out = [c + self.numres for s in o for c in s.encode("utf-8")]
        if self.add_bos: out = [self.bos_token_id] + out
        if self.add_eos: out =  out + [self.eos_token_id]
        if self.is_lm:return LMTensorText(out)
        else: return TensorText(out)

    @typedispatch
    def __call__(self, o:str, **kwargs):
        out = [c + self.numres for c in o.encode("utf-8")]
        if self.add_bos: out = [self.bos_token_id] + out
        if self.add_eos: out =  out + [self.eos_token_id]
        if self.is_lm: return LMTensorText(out)
        else: return TensorText(out)

    def encodes(self,o):
        return self.__call__(o)

    def decodes(self, o:tuple):
        decoded_ids = ()
        for i in o:
            tmp_ls=[]
            for id_ in i:
                if 0 <= id_ < self.numres: tmp_ls.append(self.reserved_tokens_bytes[int(id_)])
                else: tmp_ls.append(self.int2byte(id_ - self.numres))
            decoded_ids = decoded_ids + (b"".join(tmp_ls).decode("utf-8", "replace"),)
        return TitledStr(decoded_ids)

    def decodes(self, o:list):
        decoded_ids = []
        for id_ in o:
            if 0 <= id_ < self.numres: decoded_ids.append(self.reserved_tokens_bytes[int(id_)])
            else: decoded_ids.append(self.int2byte(id_ - self.numres))
        return TitledStr(b"".join(decoded_ids).decode("utf-8", "replace"))

    def decodes(self, o:TensorText):
        return self.decodes(o.tolist())

    def decodes(self, o:LMTensorText):
        return self.decodes(o.tolist())

    @property
    def vocab_size(self): return 2**8 + self.numres