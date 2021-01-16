from fastai.basics import *
from .all import *
from .expscript import *
from fastai.distributed import *
import time

path = rank0_first(download_enwik8_data())
dls = get_enwik8_dataloader(data_path='./data', bs=8, sl=2048, n_workers=None)
config = TransformerLMConfigEnwik8(warn=False, verbose=False)
model = TransformerLM.from_config(config)
learn = get_lm_learner(dls, model)

# wandb_run, cbs = init_wandb(cbs, wandb_name=run_name, wandb_group=wandb_group, 
#                             wandb_notes=wandb_notes, wandb_tags=wandb_tags)
with learn.distrib_ctx(): learn.fit(1)

save_model = False
if save_model:
    now = time.strftime("_%d_%m_%Y_%H:%M", time.gmtime())
    learn.save(f'{task}_{run_name}_{now}')