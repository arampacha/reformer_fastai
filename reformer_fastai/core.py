# AUTOGENERATED! DO NOT EDIT! File to edit: nbs/00_core.ipynb (unless otherwise specified).

__all__ = ['exists', 'default', 'expand_dim1', 'max_neg_value', 'setattr_on', 'top_p_filter', 'top_k_filter',
           'cache_method_decorator', 'look_one_back', 'chunked_sum', 'sort_key_val', 'batched_index_select',
           'do_cuda_timing', 'model_performance', 'total_params', 'CombineInputOutputCallback', 'RemoveEOSCallback',
           'LossTargetShiftCallback', 'LabelSmoothingCrossEntropy', 'LabelSmoothingCrossEntropyFlat']

# Cell
import torch
from torch import nn, einsum
import torch.nn.functional as F
import torch.autograd.profiler as profiler

from fastai.basics import *
from fastai.text.all import *
from fastai.test_utils import *

from functools import partial, reduce, wraps
from inspect import isfunction
from operator import mul
from copy import deepcopy

from torch import Tensor
from typing import Tuple

from einops import rearrange, repeat

# Cell
def exists(val):
    return val is not None

def default(val, d):
    if exists(val):
        return val
    return d() if isfunction(d) else d

def expand_dim1(x):
    if len(x.shape) == 1:
        return x[None, :]
    else: return x

def max_neg_value(tensor):
    return -torch.finfo(tensor.dtype).max

# Cell
def setattr_on(model, attr, val, module_class):
    for m in model.modules():
        if isinstance(m, module_class):
            setattr(m, attr, val)

# Cell
# generative helpers
# credit https://github.com/huggingface/transformers/blob/a0c62d249303a68f5336e3f9a96ecf9241d7abbe/src/transformers/generation_logits_process.py
def top_p_filter(logits, top_p=0.9):
    sorted_logits, sorted_indices = torch.sort(logits, descending=True)
    cum_probs = torch.cumsum(F.softmax(sorted_logits, dim=-1), dim=-1)

    sorted_indices_to_remove = cum_probs > top_p
    sorted_indices_to_remove[..., 1:] = sorted_indices_to_remove[..., :-1].clone()
    sorted_indices_to_remove[..., 0] = 0
    # if min_tokens_to_keep > 1:
    #         # Keep at least min_tokens_to_keep (set to min_tokens_to_keep-1 because we add the first one below)
    #         sorted_indices_to_remove[..., : min_tokens_to_keep - 1] = 0
    indices_to_remove = sorted_indices_to_remove.scatter(1, sorted_indices, sorted_indices_to_remove)
    logits[indices_to_remove] = float('-inf')
    return logits

def top_k_filter(logits, top_k=20):
    indices_to_remove = logits < torch.topk(logits, top_k)[0][..., -1, None]
    logits[indices_to_remove] = float('-inf')
    return logits

_sampler = {
    'top_k':top_k_filter,
    'top_p':top_p_filter,
    'gready':lambda x: x.argmax(-1)
}

# Cell
def cache_method_decorator(cache_attr, cache_namespace, reexecute = False):
    def inner_fn(fn):
        @wraps(fn)
        def wrapper(self, *args, key_namespace=None, fetch=False, set_cache=True, **kwargs):
            namespace_str = str(default(key_namespace, ''))
            _cache = getattr(self, cache_attr)
            _keyname = f'{cache_namespace}:{namespace_str}'

            if fetch:
                val = _cache[_keyname]
                if reexecute:
                    fn(self, *args, **kwargs)
            else:
                val = fn(self, *args, **kwargs)
                if set_cache:
                    setattr(self, cache_attr, {**_cache, **{_keyname: val}})
            return val
        return wrapper
    return inner_fn

# Cell
def look_one_back(x):
    x_extra = torch.cat([x[:, -1:, ...], x[:, :-1, ...]], dim=1)
    return torch.cat([x, x_extra], dim=2)

# Cell
def chunked_sum(tensor, chunks=1):
    *orig_size, last_dim = tensor.shape
    tensor = tensor.reshape(-1, last_dim)
    summed_tensors = [c.sum(dim=-1) for c in tensor.chunk(chunks, dim=0)]
    return torch.cat(summed_tensors, dim=0).reshape(orig_size)

# Cell
def sort_key_val(t1, t2, dim=-1):
    values, indices = t1.sort(dim=dim)
    t2 = t2.expand_as(t1)
    return values, t2.gather(dim, indices)

# Cell
def batched_index_select(values, indices):
    last_dim = values.shape[-1]
    return values.gather(1, indices[:, :, None].expand(-1, -1, last_dim))

# Cell
def do_cuda_timing(f, inp, context=None, n_loops=100):
    '''
        Get timings of cuda modules. Note `self_cpu_time_total` is returned, but
        from experiments this appears to be similar/same to the total CUDA time

        f :  function to profile, typically an nn.Module
        inp : required input to f
        context : optional additional input into f, used for Decoder-style modules
    '''
    f.cuda()
    inp = inp.cuda()
    if context is not None: context = context.cuda()
    with profiler.profile(record_shapes=False, use_cuda=True) as prof:
        with profiler.record_function("model_inference"):
            with torch.no_grad():
                for _ in range(n_loops):
                    if context is None: f(inp)
                    else: f(inp, context)
                    torch.cuda.synchronize()

    res = round((prof.key_averages().self_cpu_time_total / 1000) / n_loops, 3)
    print(f'{res}ms')
    return res

# Cell
def model_performance(n_loops=5, model='arto', dls=None, n_epochs=1, lr=5e-4):
    """
        DEMO CODE ONLY!
        Run training loop to measure timings. Note that the models internally
        should be changed depending on the model you would like to use.
        You should also adjust the metrics you are monitoring
    """
    acc_ls, ppl_ls =[], []
    for i in range(n_loops):
        # ADD YOUR MODEL(S) INIT HERE
#         if model == 'arto': m = artoTransformerLM(vocab_sz, 512)
#         elif model == 'pt': m = ptTransformerLM(vocab_sz, 512)
#         else: print('model name not correct')

        learn = Learner(dls, m,
                    loss_func=CrossEntropyLossFlat(),
                    metrics=[accuracy, Perplexity()]).to_native_fp16()

        learn.fit_one_cycle(n_epochs, lr, wd=0.05)

        acc_ls.append(learn.recorder.final_record[2])
        ppl_ls.append(learn.recorder.final_record[3])
    print(f'Avg Accuracy: {round(sum(acc_ls)/len(acc_ls),3)}, std: {np.std(acc_ls)}')
    print(f'Avg Perplexity: {round(sum(ppl_ls)/len(ppl_ls),3)}, std: {np.std(ppl_ls)}')
    print()
    return learn, acc_ls, ppl_ls

# Cell
def total_params(m):
    """
    Give the number of parameters of a module and if it's trainable or not
    - Taken from Taken from fastai.callback.hook
    """
    params = sum([p.numel() for p in m.parameters()])
    trains = [p.requires_grad for p in m.parameters()]
    return params, (False if len(trains)==0 else trains[0])

# Cell
class CombineInputOutputCallback(Callback):
    """
    Callback to combine the source (self.xb) and target (self.yb) into self.xb
    """
    def __init__(self): pass
    def before_batch(self):
        self.learn.xb = (self.xb[0], self.yb[0])

# Cell
class RemoveEOSCallback(Callback):
    """
        Shift the target presented to the model during training to remove the "eos" token as
        we don't want the model to learn to translate EOS when it sees EOS.

        In practice we actually mask the EOS token as due to batching the last token will often be a <pad> token,
        not EOS
    """
    def __init__(self, eos_idx): self.eos_idx=eos_idx
    def before_batch(self):
        eos_mask=(self.learn.xb[1]!=self.eos_idx)
        sz=torch.tensor(self.learn.xb[1].size())
        sz[1]=sz[1]-1
        self.learn.xb = (self.learn.xb[0], self.learn.xb[1][eos_mask].view((sz[0],sz[1])))

# Cell
class LossTargetShiftCallback(Callback):
    """
        Shift the target shown to the loss to exclude the "bos" token as the first token we want predicted
        should be an actual word, not the "bos" token (as we have already given the model "bos" )
    """
    def __init__(self): pass
    def after_pred(self):
        self.learn.yb = (self.learn.yb[0][:,1:],)

# Cell
class LabelSmoothingCrossEntropy(Module):
    """Label smotthing cross entropy similar to fastai implementation
    https://github.com/fastai/fastai/blob/89b1afb59e37e5abf7008888f6e4dd1bf1211e3e/fastai/losses.py#L79
    with added option to provide ignore_index"""
    y_int = True
    def __init__(self, eps:float=0.1, reduction='mean', ignore_index=-100): store_attr()

    def forward(self, output, target):
        c = output.size()[-1]
        log_preds = F.log_softmax(output, dim=-1)
        nll_loss = F.nll_loss(log_preds, target.long(), reduction=self.reduction, ignore_index=self.ignore_index)
        mask = target.eq(self.ignore_index)
        log_preds = log_preds.masked_fill(mask.unsqueeze(-1), 0.)
        if self.reduction=='sum': smooth_loss = -log_preds.sum()
        else:
            smooth_loss = -log_preds.sum(dim=-1) #We divide by that size at the return line so sum and not mean
            if self.reduction=='mean':  smooth_loss = smooth_loss.mean()/(1-mask.float().mean())# devide by fraction of accounted values to debias mean
        return smooth_loss*self.eps/c + (1-self.eps)*nll_loss

    def activation(self, out): return F.softmax(out, dim=-1)
    def decodes(self, out):    return out.argmax(dim=-1)


# Cell
@delegates()
class LabelSmoothingCrossEntropyFlat(BaseLoss):
    "Same as `LabelSmoothingCrossEntropy`, but flattens input and target."
    y_int = True
    @use_kwargs_dict(keep=True, eps=0.1, reduction='mean')
    def __init__(self, *args, axis=-1, **kwargs): super().__init__(LabelSmoothingCrossEntropy, *args, axis=axis, **kwargs)
    def activation(self, out): return F.softmax(out, dim=-1)
    def decodes(self, out):    return out.argmax(dim=-1)