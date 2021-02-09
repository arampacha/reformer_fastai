
# Reformer Reproducibility Experiments
> Fastai community entry to <a href='https://paperswithcode.com/rc2020'>2020 Papers With Code Reproducibility Challenge</a>


## Our Reproducibility Challenge Submission

- Our OpenReview paper submission to the challenge can be found [here](https://openreview.net/forum?id=3s8Y7dHYkN-) 
- Our Weights & Biases Report, with interactive charts, is available [here](https://wandb.ai/fastai_community/reformer-fastai/reports/Reformer-Reproducibility-Report---Vmlldzo0MzQ1OTg) 

## Installation

### Setup
If you don't already, its a good idea to install the package into a virtual environment

```
python3 -m venv my_env
source ./my_env/bin/activate
```

### Install
Then you can install the package via pip:

`pip install reformer-fastai`

Or (even better) install latest version from github:

`pip install git+git://github.com/arampacha/reformer_fastai.git`

### Contributing
This project used nbdev for all development, see [their docs here](https://nbdev.fast.ai/) to install nbdev and get started. Once you have nbdev installed we suggest you follow the suggested [contributor workflow](https://github.com/arampacha/reformer_fastai/blob/master/CONTRIBUTING.md)

## Running Experiments

A pip installed version of this library is needed to run experiments. All experiments are run using the `run_exp` command, followed by the particular task name and then the parameters related to that task. `run_exp --help` will display a list of all parameters as well as a brief description. For brevity, an example of how to run a Reformer Language Model experiment is show below, **a list of all experiment commands can be found here**

### Example: Reversible Language Model
Below is an example of the code used that generated the results in Section 4.4 "Effect of reversible layers" of our submission paper.

```
run_exp "lm_rev" \
        --n_epochs=10 \
        --bs=2 \
        --max_seq_len=4096 \
        --grad_accum=8 \
        --save_model=True  \
        --clip=0.5 \
        --seed=444 \
        --precision=2 \
        --do_wandb_logging=False \
```

## Hyperparameters Used

The main hyperparameters used are documented in the [Experiment Commands](https://arampacha.github.io/reformer_fastai/experiment.experiment-commands.html) page and the [Experiment Configs](https://arampacha.github.io/reformer_fastai/experiment-configs.html) page. In addition, a full list of our hyperparameters can be found in the Run Sets tables of [our Weights & Biases Report](https://wandb.ai/fastai_community/reformer-fastai/reports/Reformer-Reproducibility-Report---Vmlldzo0MzQ1OTg). To see these, navigate to the experiment of interests, click on the "Run Set" button under each chart and scroll across to find all hyperparameters.

## Results
All full description of our results, including charts and tables can be found in our paper [here on OpenReview](https://openreview.net/forum?id=3s8Y7dHYkN-). Our results are summarised as follows:

> Claims around speed on longer sequences and reduced memory footprint were validated; as sequence length
increased, Locality Sensitive Hashing ("LSH") Attention became faster and increasing the number of hashes improved
performance. We could not achieve the performance of a traditional Transformer with Reformer. Some experiments
were not run for as long as in the paper due to a lack of computational resources. Potentially the under-performance
of our Reformer may be due to under-training, implementation differences or nuances in JAX vs Pytorch. Also,
exploding gradients were encountered with mixed precision training and several model settings were found to be
unstable depending on the random seed or learning rate.

## Trained Models

All trained models from this project can be found in our [Weights & Biases project here](https://wandb.ai/fastai_community/reformer-fastai/artifacts)

## Project Links

- [Our OpenReview paper submission](https://openreview.net/forum?id=3s8Y7dHYkN-)
- [Reformer Reproducibility Report on WandB](https://wandb.ai/fastai_community/reformer-fastai/reports/Reformer-Reproducibility-Final-Edits---Vmlldzo0MzQ1OTg)
- [Our project documentation](https://arampacha.github.io/reformer_fastai/)
- [Fastai forums thread](https://forums.fast.ai/t/reproducibility-challenge-2020-fastai-folks-interested/80336/39)
- [Google doc used for early planning](https://docs.google.com/document/d/1wF83E3B3yXIGZixEgOUJI2T2XXhT1DVCrPXS5Dbsyh8/edit)

## Resources

### Author's Code and Resources
- [Reformer Paper](https://openreview.net/pdf?id=rkgNKkHtvB)
- [Authors ICLR video](https://iclr.cc/virtual_2020/poster_rkgNKkHtvB.html)
- [Google Blog](https://ai.googleblog.com/2020/01/reformer-efficient-transformer.html)
- [Authors code (TRAX)](https://github.com/google/trax/tree/master/trax/models/reformer)
- [Reformer enwik8 model and training config](https://github.com/google/trax/blob/f8024e8057599b92fce82842f342cb3d39c8f405/trax/supervised/configs/reformer_enwik8.gin)

### More Code
- [@lucidrain’s Reformer code](https://github.com/lucidrains/reformer-pytorch/)
- [HuggingFace: Reformer source code](https://github.com/huggingface/transformers/blob/a1bbcf3f6c20e15fe799a8659d6b7bd36fdf11ed/src/transformers/modeling_reformer.py)
    - [Reformer enwik8 configs](https://github.com/google/trax/blob/master/trax/supervised/configs/reformer_enwik8.gin)
    - [Reformer WMT14 en-de configs](https://github.com/google/trax/blob/master/trax/supervised/configs/reformer_wmt_ende.gin)
    - [Reformer Machine Translation example](https://github.com/google/trax/blob/a0483a12cb7ebece40b5e302e8e81fd9249c6ef6/trax/models/reformer/machine_translation.ipynb)
    = [SubwordTextEncoder tokenizer used for Machine Translation](https://github.com/tensorflow/tensor2tensor/blob/21dba2c1bdcc7ab582a2bfd8c0885c217963bb4f/tensor2tensor/data_generators/text_encoder.py#L448)
- [HuggingFace: Reformer notebook example](https://colab.research.google.com/github/patrickvonplaten/blog/blob/master/notebooks/03_reformer.ipynb)
- [HuggingFace: long sequences](https://colab.research.google.com/github/patrickvonplaten/notebooks/blob/master/PyTorch_Reformer.ipynb)
- [HuggingFace: Pretraining](https://colab.research.google.com/drive/1tzzh0i8PgDQGV3SMFUGxM7_gGae3K-uW?usp=sharing)

### Data

Tokenizers used with these datasets can be [found here](https://arampacha.github.io/reformer_fastai/tokenizers.html)

**enwik8**
- [enwik8.zip, raw data, 100mb](http://mattmahoney.net/dc/enwik8.zip)
- [Tensor2Tensor enwik8 data generator code, with train/dev/test split](https://github.com/tensorflow/tensor2tensor/blob/master/tensor2tensor/data_generators/enwik8.py). File lengths:
    - Train: 89,621,832
    - Eval: 5,000,000
    - Test: 5,000,000
- Tokenier used: ByteTextTokenizer

**WMT14**
- [WMT on HuggingFace Datasets](https://huggingface.co/datasets/viewer/?dataset=wmt14&config=cs-en)
- [Reformer pre-trained WMT14 vocab](https://github.com/google/trax/tree/a0483a12cb7ebece40b5e302e8e81fd9249c6ef6/trax/models/reformer/testdata)
    - Vocab size = 33300, from [WMT14 model config](https://github.com/google/trax/blob/master/trax/supervised/configs/reformer_wmt_ende.gin)
- Train Test split: newstest2013 for validation and newstest2014 for test, in consistence with Vaswani et al. (2017) - from https://arxiv.org/pdf/2009.02070.pdf
- Tokenizer used: SubWordTextEncoder

### Explainers

- [Yannic K explainer](https://www.youtube.com/watch?v=i4H0kjxrias&t=1s)
- [HuggingFace blog post](https://huggingface.co/blog/reformer)
- [Illustrating the Reformer blog post](https://towardsdatascience.com/illustrating-the-reformer-393575ac6ba0)
- [Reformer Deep Dive](https://www.pragmatic.ml/reformer-deep-dive/)

### Related

- [Coursera Attention Models in NLP course, with Reformer co-author](https://www.coursera.org/learn/attention-models-in-nlp)
- [@hallvagi Attention blogpost](https://hallvagi.github.io/dl-explorer/fastai/attention/lstm/2020/06/29/Attention.html)
- [The Transformer Family by @lilianweng](https://lilianweng.github.io/lil-log/2020/04/07/the-transformer-family.html)
- [A Family of Attention Mechanisms bu @lilianweng](https://lilianweng.github.io/lil-log/2018/06/24/attention-attention.html#a-family-of-attention-mechanisms)
