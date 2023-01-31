# Contributing to vmware-cloud-sizer-companion-cli

We welcome contributions from the community and first want to thank you for taking the time to contribute!

Please familiarize yourself with the [Code of Conduct](https://github.com/vmware/.github/blob/main/CODE_OF_CONDUCT.md) before contributing.

Before you start working with vmware-cloud-sizer-companion-cli, please read our [Developer Certificate of Origin](https://cla.vmware.com/dco). All contributions to this repository must be signed as described on that page. Your signature certifies that you wrote the patch or have the right to pass it on as an open-source patch.

## Ways to contribute

We welcome many different types of contributions and not all of them need a Pull request. Contributions may include:

* New features and proposals
* Documentation
* Bug fixes
* Issue Triage
* Answering questions and giving feedback
* Helping to onboard new contributors
* Other related activities

## Getting started

Two tools are required in order to contribute code - You must install [Git](https://git-scm.com/downloads) and [Python](https://www.python.org/downloads/).  This tool is dependent on Python3 (specifically 3.10), you can find installation instructions for your operating system in the Python documentation (https://wiki.python.org/moin/BeginnersGuide/Download).  

After you have installed python, be sure to install dependencies.  When you navigate to the project folder, you will find a requirements.txt file that lists all your Python packages. They can all be installed by running the following command on Linux/Mac:

```pip3 install -r requirements.txt```

On Windows, use

```python -m pip install -r requirements.txt```

You must also create a [Github](https://github.com/join) account. You need to verify your email with Github in order to contribute to this repository.

# Quickstart for Contributing

## Configure git to sign code with your verified name and email
```bash
git config --global user.name "Your Name"
git config --global user.email "youremail@domain.com"
```

## Download the VMware Cloud Sizer Companion CLI tool source code
```bash
git clone [https://github.com/vmware-samples/vmware-cloud-sizer-companion-cli.git](https://github.com/vmware-samples/vmware-cloud-sizer-companion-cli.git)
```

Make the necessary changes and save your files. 
```bash
git diff
```

Commit the code and push your commit. -a commits all changed files, -s signs your commit, and -m is a commit message - a short description of your change.

```bash
git commit -a -s -m "Added prereq and git diff output to contribution page."
git push
```

### Pull Request Checklist

Before submitting your pull request, we advise you to use the following:

1. Check if your code changes will pass both code linting checks and unit tests.
2. Ensure your commit messages are descriptive. We follow the conventions on [How to Write a Git Commit Message](http://chris.beams.io/posts/git-commit/). Be sure to include any related GitHub issue references in the commit message. See [GFM syntax](https://guides.github.com/features/mastering-markdown/#GitHub-flavored-markdown) for referencing issues and commits.
3. Check the commits and commits messages and ensure they are free from typos.

## Reporting Bugs and Creating Issues

For specifics on what to include in your report, please follow the guidelines in the issue and pull request templates when available.


## Ask for Help

The best way to reach us with a question when contributing is to ask on:

* The original GitHub issue
* The developer mailing list
