# AUTOGENERATED! DO NOT EDIT! File to edit: nbs/20_experiment-script.ipynb (unless otherwise specified).

__all__ = ['lr', 'bs', 'sl', 'train_sz', 'valid_sz', 'n_epochs', 'n_hashes', 'bucket_size', 'vocab_sz', 'd_model',
           'n_layers', 'n_heads', 'd_ff', 'attn_dropout', 'ff_dropout', 'emb_dropout', 'max_seq_len', 'causal',
           'use_lsh', 'get_twin_sequence_dataloaders', 'get_lshlm_model', 'get_synthetic_learner', 'init_wandb',
           'run_exp']

# Cell
from fastcore.all import *
from fastai.basics import *

from .reformer import LSHLM
from .data import TwinSequence, MaskTargCallback
from .metrics import MaskedAccuracy

from .tracking import *
from .tracking import WandbCallback
from .configs import SyntheticConfig

# Cell

# Training
lr=1e-3

# Dataloaders
bs=128
sl=1024
train_sz=900
valid_sz=100
n_epochs=1      # we want 150 k iterations according to the paper. Adjust n_epochs according to train_szs and bs

# Model
n_hashes=4
bucket_size=64  # suggested in trax
vocab_sz=128    # specific for the synthetic task
d_model=256
n_layers=1      # specified in paper
n_heads=4
d_ff=4*d_model

attn_dropout=0.1
ff_dropout=0.1
emb_dropout=0.1

max_seq_len=sl
causal=True
use_lsh=True

# Cell
def get_twin_sequence_dataloaders(bs:int=32, sl:int=1024, train_sz:int=500, valid_sz:int=100, seed=None):

    dls = DataLoaders.from_dsets(TwinSequence(sl, train_sz, seed),
                                 TwinSequence(sl, valid_sz, seed),
                                 bs=bs, shuffle=False, device='cuda')
    return dls

# Cell
def get_lshlm_model(vocab_sz:int=128, d_model:int=256, n_layers:int=1, n_heads:int=4, d_ff:int=None,
              max_seq_len:int=64, bucket_size:int=32, n_hashes:int=4, causal:bool=True, use_lsh:bool=True,
              attn_dropout:float=0.1, ff_dropout:float=0.1, emb_dropout:float=0.1, seed=None):

    model = LSHLM(vocab_sz=vocab_sz, d_model=d_model, n_layers=n_layers, n_heads=n_heads, d_ff=d_ff,
                  max_seq_len=max_seq_len, bucket_size=bucket_size, n_hashes=n_hashes, causal=causal,
                  use_lsh=use_lsh, attn_dropout=attn_dropout, ff_dropout=ff_dropout,
                  emb_dropout=emb_dropout, random_state=seed)
    return model

# Cell
def get_synthetic_learner(dls, model):

    learn = Learner(dls, model,
                    loss_func=CrossEntropyLossFlat(ignore_index=-100),
                    metrics=[MaskedAccuracy()]).to_fp16()
    return learn

# Cell
def init_wandb(cbs:list=[], wandb_name:str='', wandb_group:str='', wandb_notes:str='', wandb_tags:str='test'):

    wandb_tags_ls = wandb_tags.split(' ')

    try:
        import wandb
        #!wandb login
    except ImportError as e:
        print(e)

    # Init wandb
    try:
        wandb_run=wandb.init(reinit=True, project="reformer-fastai", entity="fastai_community",
               name=wandb_name, group=wandb_group, notes=wandb_notes, tags=wandb_tags_ls, config={})
        print('Weights & Biases initialised ...')
    except Exception as e:
        print(e)

    cbs.append(WandbCallback(log_model=False, log_preds=False))
    return wandb_run, cbs

# Cell
@call_parse
def run_exp(task:Param(help="Which exeriment task to run", type=str),
         n_epochs:Param(help="Number of epochs", type=int, default=n_epochs),
         lr:Param(help="Learning rate", type=float, default=lr),
         bs:Param(help="Batch size", type=int, default=bs),
         sl:Param(help="Seqlence length", type=int, default=sl),
         d_model:Param(help="Model dimension", type=int, default=d_model),
         n_layers:Param(help="Number of model layers", type=int, default=n_layers),
         n_heads:Param(help="Number of attention heads", type=int, default=n_heads),
         vocab_sz:Param(help="Vocab size", type=int, default=vocab_sz),
         d_ff:Param(help="Vocab size", type=int, default=d_ff),
         attn_dropout:Param(help="Attention dropout rate", type=float, default=attn_dropout),
         ff_dropout:Param(help="Attention dropout rate", type=float, default=ff_dropout),
         emb_dropout:Param(help="Attention dropout rate", type=float, default=emb_dropout),
         train_sz:Param(help="TwinSequence train size", type=int, default=train_sz),
         valid_sz:Param(help="TwinSequence valid size", type=int, default=valid_sz),
         n_hashes:Param(help="Number of LSH Attention hashes", type=int, default=n_hashes),
         bucket_size:Param(help="LSH Attention bucket size", type=int, default=bucket_size),
         causal:Param(help="Use causal masking", type=bool_arg, default=causal),
         use_lsh:Param(help="Use LSH Attention", type=bool_arg, default=use_lsh),
         max_seq_len:Param(help="Max sequence length for model embedding", type=int, default=max_seq_len),
         do_wandb_logging:Param(help="Use weights and biases logging", type=bool_arg, default=False),
         wandb_name:Param(help="wandb run name", type=str, default='my_experiment_name'),
         wandb_group:Param(help="wandb group", type=str, default='TEST'),
         wandb_notes:Param(help="wandb notes", type=str, default='My experiment notes'),
#          wandb_config:Param(help="Use wandb logging", type=bool_arg, default='my_experiment_name'),
         wandb_tags:Param(help="wandb tags, add tags in a single string, space separated", type=str, default='test'),
         save_model:Param(help="Save model locally in /models", type=bool_arg, default=False),
         cuda_id:Param(help="Which cuda device to use", type=int, default=0),
         seed:Param(help="Set seed for reproducibiltiy, passing anything except 0 will use fastai's set_seed", type=int, default=0)
        ):

    """tasks: synt, lm, trans"""

    # Callbacks used for training
    cbs = []


    #random seeds
    random_state = seed if seed!=0 else None      # this is passed to LSH and data generator respectively

    if seed !=0 :
        set_seed(seed, reproducible=True)          # this also sets `torch.backends.cudnn`


    if task == 'synt':
        # Set which GPU to run the script on
        torch.cuda.set_device(cuda_id)

        print('Getting dataloaders ...')
        dls = get_twin_sequence_dataloaders(bs=bs, sl=sl, train_sz=train_sz, valid_sz=valid_sz)
        print('done!')

        print('Getting model ...')
        config = SyntheticConfig(**locals())
        config.save(wandb_name, add_tstmp=True)
        model = LSHLM.from_config(config)
        print('done!')

        print('Getting learner ...')
        learn = get_synthetic_learner(dls, model)
        print('done!')

        # Set up Weights & Biases logging, if needed
        if do_wandb_logging:
            wandb_run, cbs = init_wandb(cbs, wandb_name=wandb_name, wandb_group=wandb_group,
                                        wandb_notes=wandb_notes, wandb_tags=wandb_tags)

        # Append training callbacks needed
        cbs.append(MaskTargCallback())

        # Start training
        print('Starting training...')
        learn.fit_one_cycle(n_epochs, lr, cbs=cbs)
        print('done!')

        # Close wandb logging for this run
        if do_wandb_logging: wandb_run.finish()

        # Save model weights if needed
        if save_model:
            import datetime
            now = datetime.datetime.now().strftime("%Y%m%d_%H:%M:%S")
            learn.save(f'{task}_n_hashes-{n_hashes}_use-lsh-{use_lsh}_epohs-{n_epochs}_{now}')

    elif task =='test':
        print('testing testing :)')
    else:
        print('No task run')