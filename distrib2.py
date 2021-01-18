from fastai.basics import *
from fastai.distributed import *
from reformer_fastai.all import *
from reformer_fastai.expscript import *

import time

@call_parse
def run_exp(
    data_path:  Param(help="Path to data folder", type=str, default='./data'),
    n_epochs:   Param(help="Number of epochs", type=int, default=1),
    # lr:Param(help="Learning rate", type=float, default=1e-3),
    bs:         Param(help="Batch size", type=int, default=4),
    sl:         Param(help="Sequence length", type=int, default=512),
    max_seq_len:Param(help="Max sequence length for model embedding and dataloader", type=int, default=512),
    axial_shape:Param(help="Axial Positional Encoding shape, passed as a string, e.g. '64,32''", type=str, default='32,16'),
    wandb_log:  Param(help="Use weights and biases logging", type=bool_arg, default=False),
    run_name:   Param(help="Run name for wandb tracking and model filename", type=str, default=''),
    wandb_group:Param(help="wandb group", type=str, default='TEST'),
    wandb_notes:Param(help="wandb notes", type=str, default='My experiment notes'),
    wandb_tags: Param(help="wandb tags, add tags in a single string, space separated", type=str, default='test'),
    save_model: Param(help="Save model locally in /models", type=bool_arg, default=False),
    # grad_accum:Param(help="Gradient Accumulation, set greater than 1 to implement", type=int, default=1),
    ):
    print('Loading data...')
    path = rank0_first(download_enwik8_data, dest=data_path)
    print('Preparing dataloaders...')
    dls = rank0_first(get_enwik8_dataloader, data_path=data_path, bs=bs, sl=sl, n_workers=None)
    config = TransformerLMConfigEnwik8(warn=False, verbose=False, max_seq_len=max_seq_len, axial_shape=axial_shape,
                                    )
    model = TransformerLM.from_config(config)
    learn = rank0_first(get_lm_learner, dls, model)
    cbs = []
    if do_wandb_logging:
        wandb_run, cbs = init_wandb(cbs, wandb_name=run_name, wandb_group=wandb_group, 
                                    wandb_notes=wandb_notes, wandb_tags=wandb_tags)
    print('Training...')
    with learn.distrib_ctx(): learn.fit(n_epochs, cbs=cbs)

    if save_model:
        now = time.strftime("_%d_%m_%Y_%H:%M", time.gmtime())
        learn.save(f'{run_name}_{now}')