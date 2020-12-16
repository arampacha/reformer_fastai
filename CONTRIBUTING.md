# How to contribute

## How to get started

Before anything else, please install the git hooks that run automatic scripts during each commit and merge to strip the notebooks of superfluous metadata (and avoid merge conflicts). After cloning the repository, run the following command inside it:
```
nbdev_install_git_hooks
```

## nbdev Workflow:

Please follow the below guidelines for creating and submitting PRs to this repo

### Do once after cloning the repo
    - [optional] `pip install -e .` - do this if your nbs are not located in the project's root folder, e.g. if they are in reformer_fastai/nbs
    - [optional `gh repo fork --remote` - for the repo if you are not a collaborator
    - `nbdev_install_git_hooks`

### Do for every change you want to make
    - `git checkout -b add-my-feature` - create a new branch
    - **Make your changes to notebook**
    - `nbdev_build_lib` - Build the library
    - `nbdev_build_docs` - Build the docs (see note below on docs)
    - [optional] To run the same checks that the Continuous Integration on Github will run:
        - `nbdev_read_nbs`
        - `nbdev_clean_nbs`
        - `nbdev_diff_nbs`
        - `nbdev_test_nbs`
    - `git commit -am "just testing"` - commit your changes
    - `git push -u origin HEAD` if its your first push from this repo/fork, `git push` after that
    - `gh pr create -f` - Create your PR

### After creating your PR
    - `git pull upstream master` - Keep up to date with the master branch
    - `git checkout master`
    - `git branch -d add-my-feature` - Once PR merged, delete your branch

### Writing Tests
    - Make sure tests don't take too long, testing time quickly adds up!
    - Make sure your tests don't produce new notebooks
    - For experiments and other similar notebooks use the ``#slow` flag for a cell or `#all_slow flag` for the remainder of the notebook to not test those cells.

### Building Docs
    - Note that if you add a new notebook it won't be added to the docs automatically any longer. The .html file has to be added to our custom docs/sidebar.json
    - This is because we are using a custom sidebar, see here for more: https://nbdev.fast.ai/export2html.html#Sidebar

### Other tips
    - Edit index.ipynb to edit the README.md and your project's homepage
    - To checkout an existing PR locally: gh pr checkout pr_number.  If one adds commits to the branch and pushes those, the PR is also updated.

### Taken from:
- [nbdev tutorial](https://nbdev.fast.ai/tutorial.html#Edit-index.ipynb)
- [fastai guide to creating a PR](https://docs.fast.ai/dev-setup.html#Creating-your-PR)

## Did you find a bug?

* Ensure the bug was not already reported by searching on GitHub under Issues.
* If you're unable to find an open issue addressing the problem, open a new one. Be sure to include a title and clear description, as much relevant information as possible, and a code sample or an executable test case demonstrating the expected behavior that is not occurring.
* Be sure to add the complete error messages.

#### Did you write a patch that fixes a bug?

* Open a new GitHub pull request with the patch.
* Ensure that your PR includes a test that fails without your patch, and pass with it.
* Ensure the PR description clearly describes the problem and solution. Include the relevant issue number if applicable.

## PR submission guidelines

* Keep each PR focused. While it's more convenient, do not combine several unrelated fixes together. Create as many branches as needing to keep each PR focused.
* Do not mix style changes/fixes with "functional" changes. It's very difficult to review such PRs and it most likely get rejected.
* Do not add/remove vertical whitespace. Preserve the original style of the file you edit as much as you can.
* Do not turn an already submitted PR into your development playground. If after you submitted PR, you discovered that more work is needed - close the PR, do the required work and then submit a new PR. Otherwise each of your commits requires attention from maintainers of the project.
* If, however, you submitted a PR and received a request for changes, you should proceed with commits inside that PR, so that the maintainer can see the incremental fixes and won't need to review the whole PR again. In the exception case where you realize it'll take many many commits to complete the requests, then it's probably best to close the PR, do the work and then submit it again. Use common sense where you'd choose one way over another.

## Do you want to contribute to the documentation?

* Docs are automatically created from the notebooks in the nbs folder.

