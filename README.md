Evolvix ABCtoolbox Wrapper
==========

An automation pipeline for parameter estimation in Evolvlix using the ABCtoolbox project from Wegmann D, Leuenberger C , Neuenschwander S &amp; Excoffier L (2010) ABCtoolbox: a versatile toolkit for approximate Bayesian computations. BMC Bioinformatics 11: 116

The scripts contained herein are thus far a collaboration between Kurt Ehlert and Seth Keel. Kurt focused on the parameter estimation workflow and Seth focused on the distributed computing aspect, but the lines are blurry. We're migrating from an existing repo and losing our history, so contact me (Seth) if you have any questions and I'll redirect you as necessary.

The fork of the ABCToolbox project, which is what this pipeline uses, can be found at:
https://github.com/sakeel/ABCtoolbox

Build the ABCToolbox binaries and put the binaries directly in the root of this project. You also will need to move the plotPosteriorsGLM.r file from the script directory into the root of this project.

Evolvix will eventually be open-sourced as well. For now just grab the main Evolvix binary and the worker binaries and put them directly in the root of this project. Evolvix binaries can be found here:
http://evolvix.org/

The scripts in this repo will run ABCToolbox using Evolvix quests in parallel locally or on HTCondor (http://research.cs.wisc.edu/htcondor/) if it is available on the local system.

This is kind of a kludgy hack for our internal use. We'll refine it into something more useable for others over time. More documentation will also follow. For now, if you're having trouble, contact me and I'll help get you going.
