from fastai.basics import *
from reformer_fastai.all import *
from reformer_fastai.expscript import *
from fastai.distributed import *
import time

print('Loading data...')
path = rank0_first(download_enwik8_data)
print('Preparing dataloaders...')
dls = rank0_first(get_enwik8_dataloader, data_path='./data', bs=4, sl=512, n_workers=4)
config = TransformerLMConfigEnwik8(warn=False, verbose=False)
model = TransformerLM.from_config(config)
learn = rank0_first(get_lm_learner, dls, model)
cbs = []
# wandb_run, cbs = init_wandb(cbs, wandb_name=run_name, wandb_group=wandb_group, 
#                             wandb_notes=wandb_notes, wandb_tags=wandb_tags)
print('Training...')
with learn.distrib_ctx(): learn.fit(1, cbs=cbs)

save_model = False
if save_model:
    now = time.strftime("_%d_%m_%Y_%H:%M", time.gmtime())
    learn.save(f'{task}_{run_name}_{now}')