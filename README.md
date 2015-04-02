Evolvix ABCtoolbox Wrapper
==========================

An automation pipeline for parameter estimation in Evolvix using the ABCtoolbox
project from Wegmann D, Leuenberger C , Neuenschwander S &amp; Excoffier L
(2010) ABCtoolbox: a versatile toolkit for approximate Bayesian computations.
BMC Bioinformatics 11: 116

The scripts contained herein are thus far a collaboration between Kurt Ehlert
and Seth Keel. Kurt focused on the parameter estimation workflow and Seth
focused on the distributed computing aspect, but the lines are blurry. We're
migrating from an existing repo and losing our history, so contact me (Seth) if
you have any questions and I'll redirect you as necessary.

The fork of the ABCToolbox project, which is what this pipeline uses, can be
found at: https://github.com/sakeel/ABCtoolbox

Build the ABCToolbox binaries and put the binaries directly in the root of this
project. You also will need to move the plotPosteriorsGLM.r file from the script
directory into the root of this project.

Evolvix will eventually be open-sourced as well. For now just grab the main
Evolvix binary and the worker binaries and put them directly in the root of this
project. Evolvix binaries can be found here: http://evolvix.org/

The scripts in this repo will run ABCToolbox using Evolvix quests in parallel
locally or on HTCondor (http://research.cs.wisc.edu/htcondor/) if it is
available on the local system.

This is kind of a kludgy hack for our internal use. We'll refine it into
something more useable for others over time. More documentation will also
follow. For now, if you're having trouble, contact me and I'll help get you
going.


Setup
------

Make sure the latest versions of [R](http://www.r-project.org) and
[Python](http://www.python.org) are installed. Also install the required *rpy2*
python module by running:

        curl -O http://bootstrap.pypa.io/get-pip.py &&\
        sudo python get-pip.py && sudo pip install rpy2

Test the *rpy2* installation by running the following:

        python -c "import rpy2"

If the command returns with no output shown, then *rpy2*
was successfully installed. Next, go into the Evolvix repository and build
*Evolvix_ABCToolbox_Wrapper*. Go to
*.../Evolvix/Build/Packages/Evolvix_ABCToolbox_Wrapper/0.1.0/abc*. Now you are
all set to run ABC. Try running ABC on the birth model to test the build:

        ./run.py birth -n 200 -c 2

The PDF with the posterior should appear in
*.../abc/quests/birth/Working/estimate*.


Adding a new model
-------------------
The models (also known as quests) are in the *quests* directory. Whenever you
add a new one, make a new directory in the *quests directory* with the **same
name as the quest**. Every new quest directory requires the "experimental" data,
a *.est* file with priors, and an Evolvix quest file. Documentation on the
*.est* file is in the ABCToolbox documentation.


Getting parameter estimates
---------------------------

To get parameter estimates, first go to the *run_abc* directory. Make sure there
is an Evolvix binary in that directory. *run.py* is the entry point to parameter
estimation. *sim.py* is just used to run a single simulation. Many of the ABC
settings are changed by editing either *estimatorTemplate.input* or
*samplerTemplate.input*. For more information on the *.input* files, see the
ABCToolbox documentation.

Settings such as the number of jobs, number of simulations, and which quest to
use are set via the command-line options of *run.py*. To get help with the
options, run

        ./run.py --help

Typically, the only options you need to set are <code>-n</code>,
<code>-c</code>, and the quest name. The quest name argument is a positional
argument. Here is an example command:

        ./run.py birth -n 10000 -c 10

That command runs ABC on the birth model with 10 jobs and 10,000 simulations. To
use *HTCondor*, just add <code>-htcondor</code>. However, to use *HTCondor*, you
need to be on a computer that is capable of submitting *HTCondor* jobs.
