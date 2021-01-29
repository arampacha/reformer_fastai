# Adding Experiment Results with DVC
This document explains how to add experiment results – models and other artifacts to the project. It uses a package called [DVC](https://dvc.org) to do this.

if you haven't already installed dvc you can do it with the following command:
```
pip install dvc
```

## Pulling existing experiment results (optional)
To pull results, simply checkout the version of git you want and then do dvc pull
```
git checkout {commit/branch/tag}
dvc pull -r origin
```

## Adding experiment results
To add experiment results, simply put the result files (models, or anything else) into the `experiment_results/` folder (if it doesn't exist you can create it with `mkdir experiment_results/`).

For convention, I've defined a folder structure as following: 
```
experiment_results
└── task_name/wandb_group_name (e.g lm_base)
    └── wandb_run_name (e.g.) lm_base_enwik8_sl-4096_bs-2_n_eps-10_seed-42_grad-accum-8
        ├── exp_configs
        └── models
```

After you've finished adding the results simply copy and paste the following:
```
dvc commit experiment_results.dvc
git add .
git commit -m "Added experiment results for XXXX"
```

Then, in order to push the data back type in:
```
dvc remote modify origin --local auth basic
dvc remote modify origin --local user {input your dagshub username}
dvc remote modify origin --local ask_password true
git push origin master
dvc push -r origin
```
You will be prompted for your password, after which all changes will be uploaded.