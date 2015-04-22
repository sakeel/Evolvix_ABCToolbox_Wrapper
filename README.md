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
python module by first running:

        cd .../[EVOLVIX_HOME]/Build/Packages/Evolvix_ABCToolbox_Wrapper

Then running:

        curl -O https://bootstrap.pypa.io/get-pip.py &&\
        sudo python get-pip.py && sudo pip install rpy2

Test the *rpy2* installation by running the following:

        python -c "import rpy2"

If the command returns with no output shown, then *rpy2* was successfully
installed. 

Next, go into the Evolvix repository and run *Evolvix_ABCToolbox_Wrapper*:

        cd .../[EVOLVIX_HOME]/Scripts
        python EvolvixDevelopmentAutomation.py --clean
        cd ../Build && make Evolvix_ABCToolbox_Wrapper

 Go to the ABC working directory:
 
        cd  .../[EVOLVIX_HOME]/Build/Packages/Evolvix_ABCToolbox_Wrapper/0.1.0/
        
Now you are all set to run ABC.  Try running ABC on the birth model to test the
build in the folder above::
    
        ./run.py birth -n 200 -c 2

The PDF with the posterior should appear in::

        .../[EVOLVIX_HOME]/Build/Packages/Evolvix_ABCToolbox_Wrapper/quests/birth/Working/estimate

Adding a new model
-------------------
The models (also known as Quests) are in the following folder:

        cd EvolvixHome cd ./Build/Packages/Evolvix_ABCToolbox_Wrapper/quests
        
Whenever you add a new Quest, you make a folder with the  **same name as the
quest**:

        mkdir [QUEST_NAME]

Every new quest directory requires 

* [QUEST_NAME]Data.txt 
* [QUEST_NAME]Priors.est (see ABCToolbox documentation for info on this file)
* [QUEST_NAME]Quest.txt
    
Here is an example directory with all the necessary files: cd
.../[EVOLVIX_HOME]/Packages/Evolvix_ABCToolbox_Wrapper/demo_quests/birth

Getting parameter estimates
---------------------------

To get parameter estimates, first go to the *run_abc* directory. Make sure there
is an Evolvix binary in that directory. *run.py* is the entry point to parameter
estimation. *sim.py* is just used to run a single simulation. 

Many of the ABC settings are changed by editing either *estimatorTemplate.input*
or *samplerTemplate.input*. Those files are found in 

    .../[EVOLVIX_HOME]/Build/Packages/Evolvix_ABCToolbox_Wrapper/0.1.0/samplerTemplate.input
      
which get automatically copied to the following results location:

    .../[EVOLVIX_HOME]/Build/Packages/Evolvix_ABCToolbox_Wrapper/quests/[QUEST_NAME]/Working

For more information on the *.input* files, see the ABCToolbox documentation.

Settings such as the number of jobs, number of simulations, and which quest to
use are set via the command-line options of *run.py*. To get help with the
options, run

        cd .../[EVOLVIX_HOME]/Build/Packages/Evolvix_ABCToolbox_Wrapper/0.1.0
        ./run.py --help

Typically, the only options you need to set are <code>-n</code>,
<code>-c</code>, and the quest name. The quest name argument is a positional
argument. Here is an example command:

        ./run.py birth -n 10000 -c 10

That command runs ABC on the birth model with 10 jobs and 10,000 simulations. To
use *HTCondor*, just add <code>-htcondor</code>. However, to use *HTCondor*, you
need to be on a computer that is capable of submitting *HTCondor* jobs.

Running on Condor
---------------------------

    ./run.py birth -n 10000 -c 10 --htcondor

If you run <code>condor_q</code> and do not see any of your jobs, then they are
completed.
