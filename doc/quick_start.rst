.. _quick-start-guide:

Quick Start Guide
=================

This guide will walk you through basic installation and usage of CAMPAREE
running a simulation on a simplified dataset consisting of a mouse genome
truncated to about 6 million bases (the "Baby Genome") and two samples of reads
that align there.

Installation
------------

Make sure you have the following installed on your system:

- git
- python version 3.6
- Java 1.8

Pull the git repo for CAMPAREE and BEERS_UTILS the into a convenient location::

    git clone https://github.com/itmat/CAMPAREE.git
    git clone https://github.com/itmat/BEERS_UTILS.git

Create a Python virtual environment to install required Python libraries to::

    cd CAMPAREE
    python3 -m venv ./venv_camparee

And activate the environment::

    source ./venv_camparee/bin/activate

Install required libraries::

    pip install -r requirements.txt
    pip install -r ../BEERS_UTILS/requirements.txt

Install CAMPAREE package in your Python environment::

    pip install -e .

Next, install the BEERS_UTILS package that CAMPAREE uses::

    pip install -e ../BEERS_UTILS

Note that we currently require the use of the ``-e`` flag during these installs,
otherwise CAMPAREE will not run successfully.

.. _quick-start-baby-genome:

Baby Genome
-----------

The "baby genome" is a truncated version of mm10 consisting of segments of
length at most 1 million bases chosen from chromosomes 1, 2, 3, X, Y, and MT.

Create STAR index for alignment to the baby genome::

    bin/create_star_index_for_baby_genome.sh

Perform Test Run
----------------

We are now ready to run CAMPAREE on a two small sample fastq files aligning to
the baby genome. If you have not already done so for installation, activate the
python environment::

    source ./venv_camparee/bin/activate

The default config file for the baby genome has CAMPAREE run all operations
serially on a single machine. To perform the test with these defaults run::

    bin/run_camparee.py -c config/baby.config.yaml -r 1

The argument ``-r 1`` indicates that the run number is 1. If you run this again,
you must either remove the output directory ``test_data/results/run_1/`` or
specify a new run number.

It is also possible to test deployment to a cluster.
For LSF clusters run::

    bin/run_camparee.py -c config/baby.config.yaml -r 1 -m lsf

For SGE clusters run::

    bin/run_camparee.py -c config/baby.config.yaml -r 1 -m sge

Check Results
-------------

When the run completes, all output will be saved to
``CAMPAREE/test_data/results/run_1/``. The final outputs will be in the text
files ``test_data/results/run_1/CAMPAREE/data/sample1/molecule_file`` and
``test_data/results/run_1/CAMPAREE/data/sample2/molecule_file``. Each line
(after the header line) corresponds to the sequence of a single simulated
molecule in a tab-delimited format. The default config file outputs 10000
molecules.
