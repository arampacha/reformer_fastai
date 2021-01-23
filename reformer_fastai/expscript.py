# AUTOGENERATED! DO NOT EDIT! File to edit: nbs/20_experiment-script.ipynb (unless otherwise specified).

__all__ = ['download_enwik8_data', 'download_wmt14_data', 'get_twin_sequence_dataloaders', 'get_enwik8_dataloader',
           'get_wmt14_dataloader', 'get_synthetic_learner', 'get_lm_learner', 'get_reformerlm_learner',
           'get_seq2seq_learner', 'init_wandb', 'run_exp']

# Cell
import sys
import multiprocessing

from fastcore.all import *
from fastai.basics import *
from fastai.text.all import *
from fastai.distributed import *

from .all import *

# Cell
def download_enwik8_data(data_path='./data'):
    dest = Path(data_path)
    if not dest.exists(): dest.mkdir()
    return untar_data('http://mattmahoney.net/dc/enwik8.zip', dest=dest)

# Cell
def download_wmt14_data(data_path='./data'):
    dest = Path(data_path)
    if not dest.exists(): dest.mkdir()

    if not os.path.isfile(f'{data_path}/wmt14_test'):
        print('Downloading data')
        try:
            from datasets import load_dataset
        except ImportError as e:
            print(e)
        dataset = load_dataset('wmt_t2t', 'de-en')

        train_df = pd.DataFrame(dataset['train']['translation'])
        train_df['is_valid'] = False
        valid_df = pd.DataFrame(dataset['validation']['translation'])
        train_df['is_valid'] = True
        test_df = pd.DataFrame(dataset['test']['translation'])
        test_df['is_test'] = True

        train_df.to_feather(f'{data_path}/wmt14_train')
        valid_df.to_feather(f'{data_path}/wmt14_valid')
        test_df.to_feather(f'{data_path}/wmt14_test')

# Cell
def get_twin_sequence_dataloaders(bs:int=32, sl:int=1024, train_sz:int=500, valid_sz:int=100, seed=None):
    dls = DataLoaders.from_dsets(DeterministicTwinSequence(sl, train_sz, seed),
                                 DeterministicTwinSequence(sl, valid_sz, seed),
                                 bs=bs, shuffle=False, device='cuda')
    return dls

# Cell
def get_enwik8_dataloader(data_path='data', bs:int=8, val_bs:int=16, sl:int=1024, n_workers=None,
                          val_test_chars:int=10e6, verbose=False, tiny=False, small=False):

    if 'google.colab' in sys.modules:
        data_path = '/content' + data_path + '/enwik8'
    else:
        data_path = data_path + '/enwik8'

    if verbose: print('Reading data into dataframe ...')
    df = pd.DataFrame({'text':read_lines(data_path)})
    if tiny:
        df = df.sample(frac=0.05)
        df.reset_index(drop=True, inplace=True)
        val_test_chars = 10000
    elif small:
        df = df[:len(df)//4].copy()
        val_test_chars = 4e6

    if verbose: print('done')

    # Do tokenization
    btt = ByteTextTokenizer(is_lm=True, add_bos=False, add_eos=False)
    if verbose: print('Tokenizing text ...')
    df['toks'] = df['text'].apply(btt)
    if verbose: print('done')

    # Get length of each sample and cumulative sum of lens
    df['lens'] = df['toks'].apply(len)
    df['lens_cum_sum'] = df.lens.cumsum()

    # Get splits, split train/valid/test based on count of tokens in each split
    train_cutoff = df.lens.sum() - val_test_chars  # keep all but 10M characters for val and test
    train_idxs = df.loc[df['lens_cum_sum'] < train_cutoff].index.values
    train_idxs = list(range(0, max(train_idxs)))

    remaining_idxs = len(df) - max(train_idxs)
    validation_idxs = list(range(max(train_idxs), max(train_idxs) + int(remaining_idxs/2)))
    test_idxs = list(range(max(validation_idxs), len(df)))

    splits = [train_idxs, validation_idxs]

    # Get Datasets
    if verbose: print('Setting up Datasets ...')
    tfms = [attrgetter("text"), btt]
    dsets = Datasets(df, [tfms], splits=splits, dl_type=LMDataLoader)
    if verbose: print('done')

    # Get Dataloaders
    dl_kwargs = [{'lens':df['lens'].values[train_idxs]},
                 {'val_lens':df['lens'].values[validation_idxs]}]
    if verbose: print('Setting up Dataloaders ...')

    n_cpus = multiprocessing.cpu_count()
    n_workers = n_cpus if n_workers is None else n_workers

    dls = dsets.dataloaders(bs=bs, val_bs=val_bs, seq_len=sl, dl_kwargs=dl_kwargs, shuffle_train=True, n_workers=n_workers)
    print('done')
    return dls

# Cell
def get_wmt14_dataloader(data_path='data', bs:int=8, val_bs:int=8, sl:int=1024, n_workers=None,
                         verbose=False, tiny=False):

    if verbose: print('Reading data into dataframe ...')
    train_df = pd.read_feather(f'{data_path}/wmt14_train')
    valid_df = pd.read_feather(f'{data_path}/wmt14_valid')
    test_df = pd.read_feather(f'{data_path}/wmt14_test')

    if tiny:
        train_df = train_df.sample(frac=0.02)
        train_df.reset_index(drop=True, inplace=True)

    # Merge Train and Validation datasets
    df = pd.concat([train_df, valid_df])
    if verbose: print('done')

    # TOKENIZER + DATASETS
    if verbose: print('Setting up Datasets ...')
    tok = SubwordTextEncoder(filename=f'{data_path}/swe_vocab', add_bos=True, seq_len=sl)

    train_split = df.loc[df.is_valid].index.values
    valid_split = df.loc[df.is_valid].index.values
    splits = train_split, valid_split

    # Get text lengths to enable faster init with SortedDL
    df['de_lens'] = df['de'].str.len()

    # Transforms
    en_tfms = [ColReader("en"), tok, add_eos_id]
    de_tfms = [ColReader("de"), tok, add_eos_id]

    # Set up datsets
    dsets = Datasets(df, [en_tfms, de_tfms], splits=splits)
    if verbose: print('done')

    # DATALOADERS
    if verbose: print('Setting up Dataloaders ...')
    srtd_dl = partial(SortedDL, shuffle=True, res=df['de_lens'].values[splits[0]])
    dl_kwargs = [{},{'val_res': df['de_lens'].values[splits[1]]}]

    # Define padding
    pad_seq2seq = partial(pad_input, pad_idx=tok.PAD_ID, pad_fields=[0,1])

    # Workers
    n_cpus = multiprocessing.cpu_count()
    n_workers = n_cpus if n_workers is None else n_workers

    dls = dsets.dataloaders(bs=bs, before_batch=pad_seq2seq, dl_type=srtd_dl, dl_kwargs=dl_kwargs,
                            shuffle_train=True, n_workers=n_workers)
    if verbose: print('done')
    return dls, tok

# Cell
def get_synthetic_learner(dls, model):
    learn = Learner(dls, model,
                    loss_func=CrossEntropyLossFlat(ignore_index=-100),
                    metrics=[MaskedAccuracy()]).to_fp16()
    return learn

# Cell
def get_lm_learner(dls, model, opt_func=adafactor):
    learn = Learner(dls, model,
                    loss_func=CrossEntropyLossFlat(ignore_index=dls.byte_text_tokenizer.pad_token_id),
                    opt_func=opt_func, metrics=[accuracy, perplexity, bpc]).to_fp16()
    return learn

# Cell
def get_reformerlm_learner(dls, model, opt_func=adafactor):
    learn = Learner(dls, model,
                    loss_func=CrossEntropyLossFlat(ignore_index=dls.byte_text_tokenizer.pad_token_id),
                    opt_func=opt_func, metrics=[accuracy, perplexity, bpc])
    return learn

# Cell
def get_seq2seq_learner(dls, model, tok):
    learn = Learner(dls, model,
                    loss_func=CrossEntropyLossFlat(ignore_index=tok.PAD_ID), # opt_func=adafactor,
                    metrics=[accuracy, Perplexity(), CorpusBLEUMetric()]).to_native_fp16()
    return learn

# Cell
def init_wandb(cbs:list=[], wandb_name:str='', wandb_group:str='', wandb_notes:str='', wandb_tags:str='test', save_model=False):
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

    cbs.append(WandbCallback(log_model=save_model, log_preds=False))
    return wandb_run, cbs

# Cell
@call_parse
def run_exp(task:Param(help="Task options: 'synt','lm_base','lm_rev',lm_shared_qk, n_hashes, trans", type=str),
         data_path:Param(help="Path to data folder", type=str, default='./data'),
         n_epochs:Param(help="Number of epochs", type=int, default=1),
         lr:Param(help="Learning rate", type=float, default=1e-3),
         bs:Param(help="Batch size", type=int, default=64),
         train_sz:Param(help="TwinSequence train size", type=int, default=12800),
         valid_sz:Param(help="TwinSequence valid size", type=int, default=1280),
         n_layers:Param(help="Number of layers", type=int, default=3),
         n_hashes:Param(help="Number of LSH Attention hashes", type=int, default=1),
         use_lsh:Param(help="Use LSH Attention", type=bool_arg, default=False),
         max_seq_len:Param(help="Max sequence length for model embedding and dataloader", type=int, default=2048),
         do_wandb_logging:Param(help="Use weights and biases logging", type=bool_arg, default=False),
         run_name:Param(help="Run name for wandb tracking and model filename", type=str, default=''),
         wandb_group:Param(help="wandb group", type=str, default='TEST'),
         wandb_notes:Param(help="wandb notes", type=str, default='My experiment notes'),
         wandb_tags:Param(help="wandb tags, add tags in a single string, space separated", type=str, default='test'),
         save_model:Param(help="Save model locally in /models", type=bool_arg, default=False),
         grad_accum:Param(help="Gradient Accumulation, set greater than 1 to implement", type=int, default=1),
         clip:Param(help="Gradient Clipping, will be set if > 0.0", type=float, default=0.0),
         cuda_id:Param(help="Which cuda device to use", type=int, default=0),
         seed:Param(help="Set seed for reproducibiltiy, passing anything except 0 will use fastai's set_seed", type=int, default=0),
         distrib:Param(help="Set to True if using distributed training", type=bool_arg, default=False),
         verbose:Param(help="Print script logs", type=bool_arg, default=True),
         tiny:Param(help="Use 5% of data, for quick iteration and testings", type=bool_arg, default=False),
        ):

    """Task options: 'synt','lm_base','lm_rev',lm_shared_qk, trans"""
    #Set up distributed training
#     _wrapper = rank0_first if distrib else partial
#     if distrib: cuda_id = None
    torch.cuda.set_device(cuda_id)

    # Callbacks used for training
    cbs = []
    if save_model: cbs.append(SaveModelCallback(every_epoch=True))

    #random seeds
    if seed!=0:
        set_seed(seed, reproducible=True)  # this  sets `torch.cudnn.backends ++`
    else:
        seed = None   # this is passed to LSH and data generator. They expect None or int

    if task == 'synt':
        "Model + Data Args than can be changed from command line: train_sz, valid_sz, n_hashes, use_lsh, seed"


        if run_name == '':
            if use_lsh: run_name = f'{task}_lsh-{n_hashes}_bs-{bs}_n_eps-{n_epochs}_seed-{seed}'
            else: run_name = f'{task}_full-attn_bs-{bs}_n_eps-{n_epochs}'

        print('Getting model ...')
        config = SyntheticConfig(warn=False, verbose=verbose, n_hashes=n_hashes, use_lsh=use_lsh)
        if verbose: print(config)
        config.save(run_name, add_tstmp=True)
        model = LSHLM.from_config(config)
        print('done!')

        print('Getting dataloaders ...')
        if train_sz != 12800: print(f'Note, "train_sz" changed from recommended 12800 to {train_sz}')
        dls = get_twin_sequence_dataloaders(bs=bs, sl=config['max_seq_len'], train_sz=train_sz,
                                            valid_sz=valid_sz, seed=seed)
        print('done!')

        print('Getting learner ...')
        learn = get_synthetic_learner(dls, model)
        print('done!')

        # Set up Weights & Biases logging, if needed
        if do_wandb_logging and rank_distrib()==0:
            wandb_run, cbs = init_wandb(cbs, wandb_name=run_name, wandb_group=wandb_group,
                                        wandb_notes=wandb_notes, wandb_tags=wandb_tags, save_model=save_model)

        # Append training callbacks needed
        cbs.append(MaskTargCallback())

        # Start training
        print('Starting training...')
        with learn.distrib_ctx(cuda_id=cuda_id): learn.fit_one_cycle(n_epochs, lr, cbs=cbs)
        print('done!')

        # Close wandb logging for this run
        if do_wandb_logging: wandb_run.finish()

        # Save model weights if needed, saved in /models relative to where script is run
        if save_model:
            now = time.strftime("_%d_%m_%Y_%H:%M", time.gmtime())
            learn.save(f'{task}_{run_name}_{now}')

    elif 'lm' in task:
        "Model args that can be changed from command line: axial_shape, max_seq_len"
        axial_shape = get_axial_shape(max_seq_len)
        if task == 'lm_base':
            if run_name == '': run_name = f'{task}_enwik8_sl-{max_seq_len}_bs-{bs}_n_eps-{n_epochs}_seed-{seed}'
            config = TransformerLMConfigEnwik8(warn=False, verbose=verbose,
                                               axial_shape=axial_shape, max_seq_len=max_seq_len)
            print('Getting model ...')
            model = TransformerLM.from_config(config)
            print('done!')
        elif task == 'lm_rev':
            if run_name == '': run_name = f'{task}_enwik8_sl-{max_seq_len}_bs-{bs}_n_eps-{n_epochs}_seed-{seed}'
            config = ReversibleLMConfigEnwik8(warn=False, verbose=verbose,
                                              axial_shape=axial_shape, max_seq_len=max_seq_len)
            print('Getting model ...')
            model = ReversibleLM.from_config(config)
            print('done!')
        elif task == 'lm_shared_qk':
            if run_name == '': run_name = f'{task}_enwik8_sl-{max_seq_len}_bs-{bs}_n_eps-{n_epochs}_seed-{seed}'
            config = TransformerLMConfigEnwik8(warn=False, verbose=verbose, shared_qk=True,
                                               axial_shape=axial_shape, max_seq_len=max_seq_len)
            print('Getting model ...')
            model = TransformerLM.from_config(config)
            print('done!')

        if verbose: print(config)
        config.save(run_name, add_tstmp=True)

        print('Checking data')
#         _wrapper(download_enwik8_data, data_path=data_path)
#         if distrib: rank0_first(download_enwik8_data, data_path=data_path)
        download_enwik8_data(data_path=data_path)
        print('done')

        print('Getting dataloaders ...')
        dls = get_enwik8_dataloader(data_path=data_path, bs=bs, val_bs=bs, sl=max_seq_len,
                                    verbose=verbose, tiny=tiny)
        print('done')

        print('Getting learner ...')
        learn = get_lm_learner(dls, model, opt_func=adafactor)
        print('done!')

        # CALLBACKS
        ## Gradient Clipping
        if clip != 0.0: cbs.append(GradientClip(max_norm=clip))

        ## Gradient Accumulation
        if grad_accum > 1:
            print(f'Gradient accumulation on, virtual batch size == {grad_accum}')
            cbs.append(GradientAccumulation(n_acc=grad_accum))
            run_name = run_name + f'_grad-accum-{grad_accum}'

        # Set up Weights & Biases logging, if needed
        if do_wandb_logging and rank_distrib()==0:
            wandb_run, cbs = init_wandb(cbs, wandb_name=run_name, wandb_group=wandb_group,
                                        wandb_notes=wandb_notes, wandb_tags=wandb_tags)

        # Start training
        print('Starting training...')
        learn.fit(n_epochs, cbs=cbs)
        print('done!')

        # Close wandb logging for this run
        if do_wandb_logging: wandb_run.finish()

        # Save model weights if needed, saved in /models relative to where script is run
        if save_model:
            now = time.strftime("_%d_%m_%Y_%H:%M", time.gmtime())
            learn.save(f'{task}_{run_name}_{now}')

    elif task == 'n_hashes':
        "Model args that can be changed from command line: n_hashes, seed"

        if run_name == '': run_name = f'{task}-{n_hashes}_enwik8_sl-{max_seq_len}_bs-{bs}_n_eps-{n_epochs}_seed-{seed}'

        print('Checking data')
#         _wrapper(download_enwik8_data, data_path=data_path)
#         if distrib: rank0_first(download_enwik8_data, data_path=data_path)
        download_enwik8_data(data_path=data_path)
        print('done')

        print('Getting dataloaders ...')
        dls = get_enwik8_dataloader(data_path=data_path, bs=bs, val_bs=bs, sl=max_seq_len,
                                    verbose=verbose, tiny=tiny)
        print('done')
        pad_id = dls.byte_text_tokenizer.pad_token_id

        config = NHashesConfig(warn=False, verbose=verbose, n_hashes=n_hashes,
                               seed=seed, pad_idx=pad_id)
        print('Getting model ...')
        model = LSHLM.from_config(config)
        print('done!')

        if verbose: print(config)
        config.save(run_name, add_tstmp=True)

        print('Getting learner ...')
        learn = get_lm_learner(dls, model, opt_func=adafactor)
        print('done!')

        # CALLBACKS
        ## Gradient Clipping
        if clip != 0.0: cbs.append(GradientClip(max_norm=clip))

        ## Gradient Accumulation
        if grad_accum > 1:
            print(f'Gradient accumulation on, virtual batch size == {grad_accum}')
            cbs.append(GradientAccumulation(n_acc=grad_accum))
            run_name = run_name + f'_grad-accum-{grad_accum}'
        #LSH-specific callback
        if config.use_lsh: cbs.append(PadBatchCallback(bucket_size=config.bucket_size,
                                                       val=pad_id, y_val=pad_id))
        # Set up Weights & Biases logging, if needed
        if do_wandb_logging and rank_distrib()==0:
            wandb_run, cbs = init_wandb(cbs, wandb_name=run_name, wandb_group=wandb_group,
                                        wandb_notes=wandb_notes, wandb_tags=wandb_tags)

        # Start training
        print('Starting training...')
        learn.fit(n_epochs, cbs=cbs)
        print('done!')

        # Close wandb logging for this run
        if do_wandb_logging: wandb_run.finish()

        # Save model weights if needed, saved in /models relative to where script is run
        if save_model:
            now = time.strftime("_%d_%m_%Y_%H:%M", time.gmtime())
            learn.save(f'{task}_{run_name}_{now}')

    elif task == 'n_layers':
        "Model args that can be changed from command line: n_hashes, seed"

        if run_name == '': run_name = f'{task}-{n_layers}_enwik8_sl-{max_seq_len}_bs-{bs}_n_eps-{n_epochs}_seed-{seed}'

        print('Checking data')
#         _wrapper(download_enwik8_data, data_path=data_path)
#         if distrib: rank0_first(download_enwik8_data, data_path=data_path)
        download_enwik8_data(data_path=data_path)
        print('done')

        print('Getting dataloaders ...')
        dls = get_enwik8_dataloader(data_path=data_path, bs=bs, val_bs=bs, sl=max_seq_len,
                                    verbose=verbose, tiny=tiny, small=True)
        print('done')
        pad_id = dls.byte_text_tokenizer.pad_token_id

        config = NLayersConfig(warn=False, verbose=verbose, n_layers=n_layers,
                               max_seq_len=max_seq_len, seed=seed, pad_idx=pad_id)
        print('Getting model ...')
        model = ReformerLM.from_config(config)
        print('done!')

        if verbose: print(config)
        config.save(run_name, add_tstmp=True)

        print('Getting learner ...')
        learn = get_reformerlm_learner(dls, model, opt_func=adafactor)
        print('done!')

        # CALLBACKS
        ## Gradient Clipping
        if clip != 0.0: cbs.append(GradientClip(max_norm=clip))

        ## Gradient Accumulation
        if grad_accum > 1:
            print(f'Gradient accumulation on, virtual batch size == {grad_accum}')
            cbs.append(GradientAccumulation(n_acc=grad_accum))
            run_name = run_name + f'_grad-accum-{grad_accum}'
        #LSH-specific callback
        if config.use_lsh: cbs.append(PadBatchCallback(bucket_size=config.bucket_size,
                                                       val=pad_id, y_val=pad_id))
        # Set up Weights & Biases logging, if needed
        if do_wandb_logging and rank_distrib()==0:
            wandb_run, cbs = init_wandb(cbs, wandb_name=run_name, wandb_group=wandb_group,
                                        wandb_notes=wandb_notes, wandb_tags=wandb_tags)

        # Start training
        print('Starting training...')
        learn.fit(n_epochs, cbs=cbs)
        print('done!')

        # Close wandb logging for this run
        if do_wandb_logging: wandb_run.finish()

        # Save model weights if needed, saved in /models relative to where script is run
        if save_model:
            now = time.strftime("_%d_%m_%Y_%H:%M", time.gmtime())
            learn.save(f'{task}_{run_name}_{now}')


    elif task == 'wmt_rev':
        "Model args that can be changed from command line: n_layers, max_seq_len"
        axial_shape = get_axial_shape(max_seq_len)
        if run_name == '': run_name = f'{task}_sl-{max_seq_len}_bs-{bs}_n_eps-{n_epochs}_seed-{seed}'

        print('Checking data')
        download_wmt14_data(data_path=data_path)
        print('done')

        print('Getting dataloaders and tokenizer ...')
        dls, tok = get_wmt14_dataloader(data_path=data_path, bs=bs, val_bs=bs, sl=max_seq_len,
                                           verbose=verbose, tiny=tiny)
        print('done')

        print('Getting model ...')
        config = ReversibleTransformerConfigWMT(warn=False, verbose=verbose,
                                                enc_vocab_sz=tok.vocab_size, dec_vocab_sz=tok.vocab_size, pad_idx=tok.PAD_ID,
                                                n_enc_layers=n_layers, n_dec_layers=n_layers)

        model = ReversibleTransformer.from_config(config)
        print('done!')

        if verbose: print(config)
        config.save(run_name, add_tstmp=True)

        print('Getting learner ...')
        # Use AdaFactor?
        learn = get_seq2seq_learner(dls, model, tok)
        print('done!')

        # CALLBACKS
        cbs.append(CombineInputOutputCallback(), LossTargetShiftCallback(), RemoveEOSCallback(eos_idx=tok.EOS_ID))

        ## Gradient Clipping Callback
        if clip != 0.0: cbs.append(GradientClip(max_norm=clip))

        ## Gradient Accumulation Callback
        if grad_accum > 1:
            print(f'Gradient accumulation on, virtual batch size == {grad_accum}')
            cbs.append(GradientAccumulation(n_acc=grad_accum))
            run_name = run_name + f'_grad-accum-{grad_accum}'

        # Set up Weights & Biases logging, if needed
        if do_wandb_logging and rank_distrib()==0:
            wandb_run, cbs = init_wandb(cbs, wandb_name=run_name, wandb_group=wandb_group,
                                        wandb_notes=wandb_notes, wandb_tags=wandb_tags)

        # Start training
        print('Starting training...')
        learn.fit_one_cycle(n_epochs, lr, cbs=cbs)
        print('done!')

        # Close wandb logging for this run
        if do_wandb_logging: wandb_run.finish()

        # Save model weights if needed, saved in /models relative to where script is run
        if save_model:
            now = time.strftime("_%d_%m_%Y_%H:%M", time.gmtime())
            learn.save(f'{task}_{run_name}_{now}')


    elif task == 'test_cfg':
        print('Locals ', locals())
        print()
        config = SyntheticConfig(verbouse=True, **locals())
        print(config)
        config.save('test')
        config2 = SyntheticConfig.from_file('test')
        print(config2)

    elif task == 'test':
        print('testing testing :)')
        print(verbose)

    else:
        print('No task run')