# AUTOGENERATED! DO NOT EDIT! File to edit: nbs/21_experiment-configs.ipynb (unless otherwise specified).

__all__ = ['update_sig', 'ConfigBase', 'SyntheticConfig', 'TransformerLMConfigEnwik8', 'ReversibleLMConfigEnwik8',
           'NHashesConfig', 'NLayersConfig', 'ReversibleTransformerConfigWMT', 'TransformerConfigWMT']

# Cell
from fastcore.all import *
from fastai.basics import *

from .core import *
from .transformer import *
from .reformer import *

import json
from inspect import signature, Parameter

# Cell
def _dummy(): return

# Cell
def update_sig(d):
    "Update signature of `f` from dict `d`"
    d = {k:Parameter(k, Parameter.KEYWORD_ONLY, default=v) for k,v in d.items()}
    def _f(f):
        sig = signature(f)
        sigd = dict(sig.parameters)
        sigd.pop('kwargs')
        sigd.update(d)
        f.__signature__ = sig.replace(parameters=sigd.values())
        return f
    return _f

# Cell
class ConfigBase:
    "Base class for Configs"
    _d:dict = None
    _model = _dummy

    def __init__(self, *, verbose=False, warn=True, **kwargs):
        self.validate()
        for k,v in kwargs.items():
            if k in self._d:
                self._d[k]=v
                if verbose: print(f'Setting `{k}` = {v}')
            elif warn: print(f'Parameter `{k}` is not accepted by {self._model.__name__}. Skipped')

    def validate(self):
        assert exists(self._d), "_d missing. You might want to provide defaults for config"
        assert self._model is not _dummy, "_model missing. Provide a model class"

    def validate_arg(self, k):
        assert k in self._d.keys(), f"{self._model.__name__} does not accept `{k}` argument"

    def __getattr__(self, k):
        try:
            res = self._d[k]
        except KeyError:
            raise AttributeError(f"{type(self).__name__} does not have attribute `{k}`")
        return res

    def __setattr__(self, k, v):
        self.validate_arg(k)
        self._d[k] = v

    def __getitem__(self, k):
        return self._d[k]

    def __setitem__(self, k, v):
        self.validate_arg(k)
        self._d[k] = v

    def __repr__(self):
        s = f"{self._model.__name__} config \n" + '-'*20
        s += ''.join(f'\n{k:16}{v}' for k,v in self._d.items())
        return s

    def dict(self): return self._d

    def save(self, fn, add_tstmp=False):
        os.makedirs('exp_configs', exist_ok=True)
        if add_tstmp:
            tstmp = time.strftime("_%d_%m_%Y_%H:%M", time.gmtime())
            fn += tstmp
        with open(f'exp_configs/{fn}.json', 'w') as f:
            json.dump(self.dict(), f)

    @classmethod
    def from_file(cls, fn):
        with open(f'exp_configs/{fn}.json') as f:
            d = json.load(f)
        return cls(**d)


# Cell
class SyntheticConfig(ConfigBase):
    """
    Config for Synthetic Experiment.
    See https://arampacha.github.io/reformer_fastai/experiment.synthetic-task.html for details
    """
    _model = LSHLM
    _d = {
        'vocab_sz':128,
        'd_model':256,
        'n_layers':1,
        'n_heads':4,
        'd_ff':256,
        'attn_dropout':0.0,
        'ff_dropout':0.0,
        'emb_dropout':0.0,
        'tie_weights':True,
        'causal':True,
        'pos_enc':'absolute',
        'max_seq_len':1024,
        'axial_shape':None,
        'axial_emb_dims':None,
        'pad_idx':None,
        'prenorm':False,
        'attn_bias':False,
        'bucket_size':64,
        'use_lsh':True,
        'n_hashes':4,
        'seed':123,
    }
    @update_sig(_d)
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

# Cell
class TransformerLMConfigEnwik8(ConfigBase):
    """
    Config for enwik8 Experiment.
    See https://arampacha.github.io/reformer_fastai/experiment.enwik8-baseline.html for details
    """
    _model = TransformerLM
    _d = {
        'vocab_sz':256,
        'd_model':1024,
        'n_layers':3,
        'n_heads':8,
        'd_ff':4096,
        'attn_dropout':0.1,
        'ff_dropout':0.1,
        'emb_dropout':0.1,
        'tie_weights':True,
        'causal':True,
        'pos_enc':'axial',
        'max_seq_len':2048,
        'axial_shape':(64,32),
        'axial_emb_dims':None,
        'pad_idx':None,
        'prenorm':False,
        'attn_bias':False,
        'shared_qk':False,
    }
    @update_sig(_d)
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

# Cell
class ReversibleLMConfigEnwik8(ConfigBase):
    """
    Config for enwik8 Experiment.
    See https://arampacha.github.io/reformer_fastai/experiment.enwik8-reversible.html for details
    """
    _model = ReversibleLM
    _d = {
        'vocab_sz':256,
        'd_model':1024,
        'n_layers':3,
        'n_heads':8,
        'd_ff':4096,
        'attn_dropout':0.1,
        'ff_dropout':0.1,
        'emb_dropout':0.1,
        'tie_weights':True,
        'causal':True,
        'pos_enc':'axial',
        'max_seq_len':2048,
        'axial_shape':(64,32),
        'axial_emb_dims':None,
        'pad_idx':None,
        'prenorm':True,
        'attn_bias':False,
        'rev_thres':0,
    }
    @update_sig(_d)
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

# Cell
class NHashesConfig(ConfigBase):
    """
    Config for evaluating performance as function of `n_hashes`.
    See https://arampacha.github.io/reformer_fastai/experiment.enwik8-n_hashes.html for details
    """
    _model = LSHLM
    _d = {
        'vocab_sz':256,
        'd_model':1024,
        'n_layers':3,
        'n_heads':8,
        'd_ff':4096,
        'attn_dropout':0.1,
        'ff_dropout':0.1,
        'emb_dropout':0.1,
        'tie_weights':True,
        'causal':True,
        'pos_enc':'axial',
        'max_seq_len':4096,
        'axial_shape':None,
        'axial_emb_dims':None,
        'pad_idx':None,
        'prenorm':False,
        'attn_bias':False,
        'bucket_size':64,
        'use_lsh':True,
        'n_hashes':2,
        'seed':842,
    }
    @update_sig(_d)
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

# Cell
class NLayersConfig(ConfigBase):
    """
    Config for evaluating performance as function of `n_layers`.
    See https://arampacha.github.io/reformer_fastai/experiment.enwik8-n_layers.html for details
    """
    _model = ReformerLM
    _d = {
        'vocab_sz':256,
        'd_model':1024,
        'n_layers':3,
        'n_heads':8,
        'd_ff':4096,
        'ff_chunks':64,
        'attn_dropout':0.1,
        'ff_dropout':0.1,
        'emb_dropout':0.1,
        'tie_weights':True,
        'causal':True,
        'pos_enc':'axial',
        'max_seq_len':2**14,
        'axial_shape':None,
        'axial_emb_dims':None,
        'pad_idx':None,
        'prenorm':True,
        'attn_bias':False,
        'bucket_size':64,
        'use_lsh':True,
        'n_hashes':8,
        'rev_thres':0,
        'seed':842,
    }
    @update_sig(_d)
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

# Cell
class ReversibleTransformerConfigWMT(ConfigBase):
    """
    Config for WMT Experiment.
    See https://arampacha.github.io/reformer_fastai/
    """
    _model = ReversibleTransformer
    _d = {
        'enc_vocab_sz':33708,
        'dec_vocab_sz':33708,
        'n_enc_layers':6,
        'n_dec_layers':6,
        'n_heads':8,
        'd_model':512,
        'd_ff':2048,
        'attn_dropout':0.1,
        'ff_dropout':0.1,
        'emb_dropout':0.1,
        'tie_weights':True,
        'shared_emb': True,
        'pos_enc':'fixed',
        'max_seq_len':256,
        'axial_shape':(64,32),
        'axial_emb_dims':None,
        'pad_idx':None,
        'prenorm':False,
        'attn_bias':False,
        'comb_attn':False,
    }
    @update_sig(_d)
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

# Cell
class TransformerConfigWMT(ConfigBase):
    """
    Config for WMT Experiment.
    See https://arampacha.github.io/reformer_fastai/
    """
    _model = Transformer
    _d = {
        'enc_vocab_sz':33708,
        'dec_vocab_sz':33708,
        'n_enc_layers':6,
        'n_dec_layers':6,
        'n_heads':8,
        'd_model':512,
        'd_ff':2048,
        'attn_dropout':0.1,
        'ff_dropout':0.1,
        'emb_dropout':0.1,
        'tie_weights':True,
        'shared_emb': True,
        'pos_enc':'fixed',
        'max_seq_len':256,
        'axial_shape':(64,32),
        'axial_emb_dims':None,
        'pad_idx':None,
        'prenorm':False,
        'attn_bias':False,
        'comb_attn':True,
    }
    @update_sig(_d)
    def __init__(self, **kwargs):
        super().__init__(**kwargs)