#!/usr/bin/env python
#
#  @file  run.py
#
#  Licensing of this file is governed by the Evolvix Contributors License Agreement
#  as described at http://evolvix.org/intro/legal
#
#  The license chosen for this file is the BSD-3-Clause
#  ( http://opensource.org/licenses/BSD-3-Clause ):
#
#  Copyright (c) 3/21/2015  Authors and contributors as listed in the corresponding
#                code repository of this file and associated organizations if applicable.
#                All rights reserved.
#/////////////////////////////////////////////////////////////////////////////
#  Redistribution and use in source and binary forms, with or without modification,
#  are permitted provided that the following conditions are met:
#   - Redistributions of source code must retain the above copyright notice,
#     this list of conditions and the following disclaimer.
#   - Redistributions in binary form must reproduce the above copyright notice,
#     this list of conditions and the following disclaimer in the documentation
#     and/or other materials provided with the distribution.
#   - Neither the names of authors nor the names of their organizations nor
#     the names of other contributors to the project may be used to endorse or promote
#     products derived from this software without specific prior written permission.
#  THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
#  AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
#  WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED.
#  IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT,
#  INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING,
#  BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
#  DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF
#  LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE
#  OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED
#  OF THE POSSIBILITY OF SUCH DAMAGE.
#/////////////////////////////////////////////////////////////////////////////
from __future__ import print_function
import sys
import argparse
import math
import os
import shutil
import fileinput
import platform
import subprocess
import time
import re
from datetime import datetime
from glob import glob
from multiprocessing import Process

import dist

BIN_DIR = os.path.dirname(os.path.abspath(__file__))
QST_NAME = None
QST_DIR = None
HST_DIR = None
WRK_DIR = None
SAM_DIR = None
DAG_DIR = None
DAG_FILE = None
EST_DIR = None
SAM_FILE = None
SAM_FILE_NAME = 'samples.txt'
DISTANCE = None
N_SIMS = None
PERCENT_RETAINED = None
PEAK_WIDTH = None

RUN_ALL_STEPS = True


#**********************************************************************#
def main():
    print('Starting run.py')
    args = parseArgs();

    global QST_NAME
    global QST_DIR
    QST_NAME = args.quest 

    QST_DIR = os.path.abspath('{0}/../quests/{1}'.format(BIN_DIR, QST_NAME))

    global WRK_DIR
    #evaluates to true just when we are running the Condor post-script to estimate and combine
    if args.working_dir:
        WRK_DIR = args.working_dir
    else:
        WRK_DIR = takeSnapshot(args)

    global DISTANCE
    DISTANCE = args.distance
    setUpGlobalVars()
    verifyQuestFilesExist(args.quest)
    validateArgs(args)
    
    global N_SIMS
    N_SIMS = args.n

    global PERCENT_RETAINED
    PERCENT_RETAINED = args.r

    global PEAK_WIDTH
    if args.p:
        PEAK_WIDTH = args.p

    if args.recover:
        htcondorSubmitDAGFile()
        sys.exit(0)

    if args.combine:
        try:
            combineSamples()
        except:
            if not args.sample:
                raise

    if args.htcondor : runOnHTCondor(args)
    else             : runLocally(args)


#**********************************************************************#
def parseArgs():
    parser = argparse.ArgumentParser(description='Run ABC.',
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('--htcondor', help='Run the simulations on HTCondor', action='store_true')
    parser.add_argument('--sample', help='Generate the samples only.', action='store_true')
    parser.add_argument('--combine', help='Won\'t generate samples, just combines any existing samples into the sample file.', action='store_true')
    parser.add_argument('--estimate', help='Use an existing sample file to estimate parameters.', action="store_true")
    parser.add_argument('--recover', help='Tries to recover in case of early termination. Valid only with runs using --htcondor', action='store_true')
    parser.add_argument('--distance', type=str, help='Distance to use. Options: ' \
                        + (', ').join(dist.distFuncs.keys()), default='L2')
    parser.add_argument('--working-dir', type=str, help='Specify a working directory to use. Overrides use of a timestamp.')
    parser.add_argument('--comment', type=str, help='Add a comment to the run\'s directory name.', default='')
    parser.add_argument('-n', type=int, help='Number of simulations.')
    parser.add_argument('-c', type=int, help='Number of cores.', default=1)
    parser.add_argument('-r', type=int, help='Percentage of simulations retained (see "numRetained" in ABCToolbox manual.', default=20)
    parser.add_argument('-p', type=float, help='See "diracPeakWidth" in ABCToolbox manual. Default: 1/(number of simulations)')
    parser.add_argument('quest', type=str, help='Name of the quest')
    args = parser.parse_args()
    return args


#**********************************************************************#
def takeSnapshot(args):
    print('taking a snapshot')
    timeStamp = datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d_%Hh%Mm%Ss')
    snapshotDir = os.path.join(QST_DIR, '{0}_{2}_{1:.0e}_runs_{3}'.format(QST_NAME, float(args.n), timeStamp, args.comment))


    #fail if snapshotdirAlready exists, just wait a second to run run.py again
    try:
        os.mkdir(snapshotDir)
    except OSError:
        raise Exception('The directory ' + snapshotDir + ' already exists. '
                        'Wait at least 1 second between run.py commands.')

    map(lambda file: shutil.copyfile(os.path.join(BIN_DIR, file),
                                     os.path.join(snapshotDir, file)),
        ['dist.py', 'plotDistance.r', 'plotPosteriorsGLM.r', 'sim.py', 'run.py']
    )
    relQuestPath = os.path.join('..', 'quests', QST_NAME, QST_NAME + 'Quest.txt')
    shutil.copyfile(relQuestPath, os.path.join(snapshotDir, QST_NAME + 'Quest.txt'))

    with open(os.path.join(snapshotDir, 'args.txt'), 'w') as f:
        map(lambda arg: f.write((' = ').join(str(x) for x in arg) + '\n'),
            vars(args).items()
        ) 
    return snapshotDir



#**********************************************************************#

def setUpGlobalVars():
    global HST_DIR
    global SAM_DIR
    global SAM_FILE
    global EST_DIR
    global DAG_DIR
    global DAG_FILE

    HST_DIR = os.path.join(QST_DIR, 'History')
    SAM_DIR = os.path.join(WRK_DIR, 'sample')
    EST_DIR = os.path.join(WRK_DIR, 'estimate')
    DAG_DIR = os.path.join(WRK_DIR, 'dag')
    DAG_FILE = os.path.join(DAG_DIR, QST_NAME + '.dag')
    SAM_FILE = os.path.join(SAM_DIR, SAM_FILE_NAME)


#**********************************************************************#
def verifyQuestFilesExist(QST_NAME):
    if(not os.path.isdir(QST_DIR)):
        print('Quest from command line:'  + QST_NAME)
        print('Error: No associated directory found at ' + QST_DIR)
        raise Exception('Could not find the folder for the ' + QST_NAME + ' quest.')
    if(not os.path.isfile(os.path.join(QST_DIR, QST_NAME + 'Quest.txt'))):
        print('Quest from command line: ' + QST_NAME)
        print('Error: No quest file found found at: ' + os.path.join(QST_DIR, QST_NAME + 'Quest.txt'))
        raise Exception('Could not find the quest file for the ' + QST_NAME + ' quest.')
    if(not os.path.isfile(os.path.join(QST_DIR, QST_NAME + 'Data.txt'))):
        print('Quest from command line: ' + QST_NAME)
        print('Error: No data file found found at: ' + os.path.join(QST_DIR, QST_NAME + 'Data.txt'))
        raise Exception('Could not find the data file for the ' + QST_NAME + ' quest.')
    if(not os.path.isfile(os.path.join(QST_DIR, QST_NAME + 'Priors.est'))):
        print('Quest from command line: ' + QST_NAME)
        print('Error: No priors file found found at: ' + os.path.join(QST_DIR, QST_NAME + 'Priors.est'))
        raise Exception('Could not find the priors file for the ' + QST_NAME + ' quest.')


#**********************************************************************#
def validateArgs(args):
    global RUN_ALL_STEPS
    RUN_ALL_STEPS =  not (args.sample or args.combine or args.estimate)
    if args.sample or RUN_ALL_STEPS:
        if args.n <= 0: raise Exception('Number of simulations must be greater than zero.')
        if args.c <= 0: raise Exception('Number of cores must be greater than zero.')
    if (args.recover and  not RUN_ALL_STEPS):
        raise Exception('--recover can not be used with other stage flags (e.g. --sample, --combine, or --estimate)')
    if (args.recover and not os.path.isfile('{0}/{1}.dag'.format(DAG_DIR,args.quest))):
        raise Exception('--recover can only be used with quests with an existing dag file. No existing dag file found.')


#**********************************************************************#
def runLocally(args):
    if args.sample or RUN_ALL_STEPS:
        # run sampler and combine output
        runSampler(args.quest, args.n, args.c)
        combineSamples()

    if args.estimate or RUN_ALL_STEPS:
        # estimate based on the distance of the samples generated
        runEstimator(args.quest)

    #even when using condor, it runs it locally to do the estimation
    #so taking the snapshot here still works for running on condor


#**********************************************************************#
def runSampler(QST_NAME, nSims, nCores):
    prepSamplerFiles(QST_NAME, nSims, nCores)
    prepRunDirs(nCores)
    runSamplerLocally(QST_NAME, nCores)


#**********************************************************************#
def prepSamplerFiles(QST_NAME, nSims, nCores, htcondor = False):   
    if not os.path.isdir(SAM_DIR) : os.mkdir(SAM_DIR)

    generateEPBFile(QST_NAME)
    writeParFile(QST_NAME)
    writeSamplerFile(QST_NAME, getSimsPerCore(nSims, nCores), htcondor)
    shutil.copy(os.path.join(QST_DIR, QST_NAME + 'Priors.est'), SAM_DIR)
    shutil.copy(os.path.join(QST_DIR, QST_NAME + 'Data.txt'), SAM_DIR)
    shutil.copy(os.path.join(BIN_DIR, 'target_distance.txt'), SAM_DIR)


#**********************************************************************#
def generateEPBFile(QST_NAME):
    questTextFile = os.path.join(QST_DIR, QST_NAME + 'Quest.txt')
    if not os.path.isfile(questTextFile):
        raise Exception('A quest file matching the quest name was not found.  Looked for {0} and did not find it.'.format(questTextFile))
    try:
        subprocess.call([BIN_DIR + '/Evolvix', '--parse_only', os.path.join(SAM_DIR, QST_NAME + 'Quest.epb'), questTextFile])
    except OSError:
        raise Exception('There was an error parsing the quest file. Check that Evolvix is installed and available.')


#**********************************************************************#
def writeParFile(QST_NAME):
    priorsFile = open(os.path.join(QST_DIR, QST_NAME + 'Priors.est'), 'r')
    priorsFile.readline()
    priorsFile.readline()

    parFile = open(os.path.join(SAM_DIR, QST_NAME + '.par'), 'w')
    for line in priorsFile:
        paramName = line.split('\t')[1]
        parFile.write('{0}: {0}\n'.format(paramName))

    parFile.close()


#**********************************************************************#
def getSimsPerCore(nSims, nCores):
    quo,rem = divmod(nSims, nCores)
    simsPerCore = int(math.ceil(float(nSims) / nCores))
    assert simsPerCore > 0
    print('Running {0} simulations over {1} parallel jobs.'.format(nSims, nCores))
    print('Simulations per job: {0}'.format(simsPerCore))
    return simsPerCore


#**********************************************************************#
def writeSamplerFile(QST_NAME, simsPerCore, htcondor = False):
    replacements = {}
    replacements['PRIORS_FILE'] = QST_NAME + 'Priors.est'
    replacements['N_SIMS'] = str(simsPerCore)
    replacements['PARS_FILE'] = QST_NAME + '.par'
    replacements['MODEL_NAME'] = QST_NAME
    replacements['DISTANCE'] = DISTANCE
    if htcondor : replacements['SRC_DIR'] = '.'
    else :        replacements['SRC_DIR'] = BIN_DIR

    inputFilePath = os.path.join(SAM_DIR, QST_NAME + 'Sampler.input.txt')
    writeInputFile(BIN_DIR + '/samplerTemplate.input.txt', inputFilePath, replacements)
    return os.path.basename(inputFilePath) 


#**********************************************************************#
def runSamplerLocally(QST_NAME, nCores):
    procs = []
    samplerInput = os.path.join(SAM_DIR, QST_NAME + 'Sampler.input.txt')
    samplerInput = os.path.abspath(samplerInput)
    for i in range(0, nCores):
        p = Process(target = execSampler, args=(i, samplerInput))
        procs.append(p)
        p.start()
    for p in procs:
        p.join()
        procs.remove(p)
        if p.exitcode:
            cleanupChildren(procs)
            raise Exception('Failed to run ABCsampler.')


#**********************************************************************#
def execSampler(taskID, samplerFileName):
    os.chdir(os.path.join(SAM_DIR, str(taskID)))
    err = os.system('{0}/ABCsampler {1}'.format(BIN_DIR, samplerFileName))
    if err: sys.exit(1)
    sys.exit(0)


#**********************************************************************#
def cleanupChildren(procs):
    for p in procs:
        p.terminate()
        assert not p.is_alive()


#**********************************************************************#
def runEstimator(QST_NAME):
    if not os.path.isdir(EST_DIR) : os.mkdir(EST_DIR)
    
    shutil.copy(SAM_DIR + '/target_distance.txt', EST_DIR)
    
    combinedSamples = os.path.join(SAM_DIR + '/samples.txt')
    nSamples = None
    with open(combinedSamples) as f:
        f.readline() #skip the header
        nSamples = sum(1 for line in f)
    estimatorFileName = writeEstimatorFile(QST_NAME, nSamples)
    
    questPath = os.path.join(QST_DIR, '{0}Quest.txt'.format(QST_NAME))
    trueParamsValsPath = os.path.join(EST_DIR, 'true_param_vals.txt')
    writeTrueParamValsFile(questPath, trueParamsValsPath)

    callEstimator(estimatorFileName)
    callPlotScript(estimatorFileName)

#**********************************************************************#
def writeEstimatorFile(QST_NAME, nSamples):
    replacements = {}
    replacements['SAMPLES'] = os.path.abspath(SAM_FILE)
    replacements['N_PARAMS'] = ','.join(map(str, range(2, getNumParams(QST_NAME)+2)))
    replacements['N_SIMS'] = str(math.pow(10, 8)) #ABCEstimator stops working after ~10^8
    replacements['N_RETAINED'] = str(round(PERCENT_RETAINED/100.0*nSamples))

    global PEAK_WIDTH
    if not PEAK_WIDTH:
        PEAK_WIDTH = 1/float(nSamples)
        print(PEAK_WIDTH)
    replacements['PEAK_WIDTH'] = str(PEAK_WIDTH)

    inputFilePath = os.path.join(EST_DIR, QST_NAME + 'Estimator.input.txt')
    writeInputFile(BIN_DIR + '/estimatorTemplate.input.txt', inputFilePath, replacements)
    return os.path.basename(inputFilePath)


#**********************************************************************#
def getNumParams(QST_NAME):
    f = open(os.path.join(SAM_DIR, QST_NAME + '.par'), 'r')
    numParams = 0
    while(f.readline()): numParams += 1
    return numParams


#**********************************************************************#
def callEstimator(estimatorFileName):
    try:
        subprocess.check_call([BIN_DIR + '/ABCestimator', estimatorFileName], cwd=EST_DIR, stdin=None, stdout=None, stderr=None, shell=False)
    except subprocess.CalledProcessError:
        raise Exception('ABCestimator exited with an error.')
    except OSError:
        raise Exception('ABCestimator was not found at: ' + BIN_DIR + '/ABCestimator')


#**********************************************************************#
def callPlotScript(estimatorFileName):
    try:
        subprocess.check_call(['Rscript', BIN_DIR + '/plotPosteriorsGLM.r', estimatorFileName], cwd=EST_DIR, stdin=None, stdout=None, stderr=None, shell=False)
    except subprocess.CalledProcessError:
        raise Exception('Rscript exited with an error.')
    except OSError:
        raise Exception('Rscript was not found. Please confirm that R is installed and that it is in the search PATH.')


#**********************************************************************#
def runOnHTCondor(args):
    #condor complains if there's are any existing dag files
    shutil.rmtree(DAG_DIR, ignore_errors = True)

    # Catch the case where we only want to combine, and then just run locally
    if args.combine and not (args.sample or args.estimate) :
        combineSamples()
    
    elif args.sample or RUN_ALL_STEPS:
        prepSamplerFiles(args.quest, args.n, args.c, True)
        makeRunDirs(args.c)
    htcondorBuildDAGFile(args)
    htcondorSubmitDAGFile()


#**********************************************************************#
def htcondorBuildDAGFile(args):
    if args.c > 10000:
        raise Exception('The run.py script is currently not capable of running more than 10,000 threads concurrently.')

    if not os.path.isdir(DAG_DIR) : os.mkdir(DAG_DIR)

    dagFile = open(DAG_FILE, 'w')
    dagFile.write(htcondorDagFileHeader(args.quest))

    # Check if we need to run the simulations
    if args.sample or RUN_ALL_STEPS:
        dagFile.write(htcondorGenerateSampleJobLines(args.quest, args.c) + '\n\n')

    # Check to see if we need to run the combine step and decide where to put it
    # PRE or POST is arbitrary if all the steps need to be run
    if args.combine or RUN_ALL_STEPS:
        if args.sample or RUN_ALL_STEPS:
            script_type = 'POST'
            job_name = 'Evolvix_PE_Sample'
        elif args.estimate:
            script_type = 'PRE'
            job_name = 'Evolvix_PE_Estimate'

        dagFile.write(htcondorGenerateCombineScriptLines(script_type, job_name, args.quest) + '\n\n')

    # Check if we need to run the estimator
    if args.estimate or RUN_ALL_STEPS:
        dagFile.write(htcondorGenerateEstimateJobLines(args.quest) + '\n\n')
        # Add a line to create the dependency between sample and estimate, if needed
        if args.sample or RUN_ALL_STEPS:
            dagFile.write('PARENT Evolvix_PE_Sample CHILD Evolvix_PE_Estimate\n\n')

    dagFile.close()


#**********************************************************************#
def htcondorDagFileHeader(QST_NAME):
    dagHeader = '# DAGMan file ({0}.dag) for quest {0}\n'.format(QST_NAME)
    dagHeader += '#\n#  *** This is an automatically generated file from the Evolvix run.py script. ***'
    dagHeader += '\n#  *** Any changes to this file will be lost. ***\n\n'
    dagHeader += '#######################################################\n\n\n'
    return dagHeader


#**********************************************************************#
def htcondorGenerateSampleJobLines(QST_NAME, nCores):
    
    inputFiles  = ','.join(listFiles(SAM_DIR)) 
    inputFiles += ',{0}/sim.py'.format(BIN_DIR)
    inputFiles += ',{0}/dist.py'.format(BIN_DIR)
    inputFiles += ',{0}/argparse.py'.format(BIN_DIR)
    inputFiles += ',{0}/Worker_MultiWorker'.format(BIN_DIR)
    
    submitFile = os.path.join(BIN_DIR, 'evolvix_generic_condor.sub')
    
    return htcondorSampleJobSpecificLines('Evolvix_PE_Sample', submitFile, nCores, QST_NAME + 'Sampler.input.txt', inputFiles)


#**********************************************************************#
def htcondorSampleJobSpecificLines(jobName, submitFile, nCores, inputFileName, inputFiles):

    vars = 'VARS {0} '.format(jobName)
    
    allJobSpecificLines   = 'JOB {0} {1}\n'.format(jobName, submitFile)
    allJobSpecificLines  += vars + 'EVOLVIX_INITDIR="{0}"\n'.format(SAM_DIR)
    allJobSpecificLines  += vars + 'EVOLVIX_BIN="ABCsampler"\n'
    allJobSpecificLines  += vars + 'EVOLVIX_BIN_DIR="{0}"\n'.format(BIN_DIR)
    allJobSpecificLines  += vars + 'EVOLVIX_INPUT_FILE_NAME="{0}"\n'.format(inputFileName)
    allJobSpecificLines  += vars + 'EVOLVIX_INPUT_FILES="{0}"\n'.format(inputFiles)
    allJobSpecificLines  += vars + 'EVOLVIX_NUM_THREADS="{0}"\n'.format(nCores)
    return allJobSpecificLines


#**********************************************************************#
def htcondorGenerateEstimateJobLines(QST_NAME):
    
    inputFiles  = '{0}/samples.txt'.format(SAM_DIR)
    inputFiles += ',{0}/target_distance.txt'.format(SAM_DIR)
    inputFiles += ',{0}/run.py'.format(BIN_DIR)
    inputFiles += ',{0}/argparse.py'.format(BIN_DIR)
    inputFiles += ',{0}/dist.py'.format(BIN_DIR)
    inputFiles += ',{0}/plotDistance.r'.format(BIN_DIR)
    inputFiles += ',{0}/plotPosteriorsGLM.r'.format(BIN_DIR)
    
    submitFile = os.path.join(BIN_DIR, 'evolvix_estimate.sub')
    
    return htcondorEstimateJobSpecificLines('Evolvix_PE_Estimate', submitFile, inputFiles, htcondorEstimateRAMRequire())


#**********************************************************************#
def htcondorEstimateJobSpecificLines(jobName, submitFile, inputFiles, ram_required):
    
    vars = 'VARS {0} '.format(jobName)
    
    allJobSpecificLines   = 'JOB {0} {1}\n'.format(jobName, submitFile)
    allJobSpecificLines  += vars + 'EVOLVIX_BIN="/usr/bin/env"\n'
    allJobSpecificLines  += vars + 'EVOLVIX_ESTIMATE_ARGUMENTS="python run.py {1}'\
            ' --estimate --working-dir {2}"\n'.format(BIN_DIR, QST_NAME, WRK_DIR)
    allJobSpecificLines  += vars + 'EVOLVIX_INITDIR="{0}"\n'.format(WRK_DIR)
    allJobSpecificLines  += vars + 'EVOLVIX_BIN_DIR="{0}"\n'.format(BIN_DIR)
    allJobSpecificLines  += vars + 'EVOLVIX_INPUT_FILES="{0}"\n'.format(inputFiles)
    allJobSpecificLines  += vars + 'EVOLVIX_RAM_REQUIRED="{0}"\n'.format(ram_required)
    return allJobSpecificLines


#**********************************************************************#
def htcondorGenerateCombineScriptLines(SCRIPT_TYPE, JOB_NAME, QST_NAME):
    
    if SCRIPT_TYPE == 'PRE':
        combine_lines = '#######################################################\n\n'
    else:
        combine_lines = ''
    
    combine_lines += 'SCRIPT {0} {1} /usr/bin/env python {2}/run.py '\
        '--combine {3} --working-dir {4}'.format(SCRIPT_TYPE, JOB_NAME, BIN_DIR, QST_NAME, WRK_DIR)

    if SCRIPT_TYPE == 'POST':
        combine_lines += '\n\n#######################################################\n'

    return combine_lines


#**********************************************************************#
def htcondorGenerateEstimateJobLines_old(QST_NAME):
    return 'SCRIPT POST Evolvix_PE_Sample /usr/bin/env python {0}/run.py ' \
        '--combine --estimate {1} --working-dir {2}\n'.format(BIN_DIR, QST_NAME, WRK_DIR)


#**********************************************************************#
def htcondorEstimateRAMRequire():
    return '10 GB'


#**********************************************************************#
def htcondorSubmitDAGFile():
    try:
        subprocess.call(['condor_submit_dag', DAG_FILE])
    except OSError:
        raise Exception('There was an error submiting the HTCondor job. Check that HTCondor is installed with DAGMan.')


#**********************************************************************#
def combineSamples():
    print('Combining all of the samples into the file ' + SAM_FILE)

    if not os.path.isdir(SAM_DIR):
        raise Exception('Cannot find the samples directory: ' + SAM_DIR)

    sampleFiles = {}    
    sampleFileName = 'out.txt_sampling1.txt'
    sampleFiles = [os.path.join(dir,sampleFileName)
                   for dir in listDirs(SAM_DIR)
                   if os.path.isfile(os.path.join(dir, sampleFileName))] 

    if len(sampleFiles) == 0:
        raise Exception('Could not find any samples. Check for '
                         + sampleFileName
                         + ' in the numbered jobs directories. '
                         + 'Did you already combine the samples?')

    #need to copy the header from one of the sample files to the combined file
    if not os.path.isfile(SAM_FILE):
        with open(SAM_FILE, 'w') as combinedSamples:
            with open(sampleFiles[0], 'r') as sampleFile:
                header = sampleFile.readline()
                print(header, file=combinedSamples, end='')

    with open(SAM_FILE, 'a') as combinedSamples:
        for sampleFile in sampleFiles:
            with open(sampleFile, 'r') as nextFile:
                nextFile.readline()
                print(''.join(nextFile.readlines()), file=combinedSamples, end='')
            print('Done processing ' + os.path.abspath(sampleFile))
    print('Done combining the samples')


#**********************************************************************#
def makeRunDirs(nCores):
    for i in range(0, nCores) :
        path = os.path.join(SAM_DIR, str(i))
        shutil.rmtree(path, ignore_errors = True)
        os.mkdir(path)


#**********************************************************************#
def prepRunDirs(nCores):
    srcFiles = listFiles(SAM_DIR)
    
    try: srcFiles.remove(SAM_FILE)
    except ValueError: pass
    
    for i in range(nCores) :
        runDir = os.path.join(SAM_DIR, str(i))
        if not os.path.exists(runDir): os.mkdir(runDir)
        for f in srcFiles:
            shutil.copy(f, runDir)

#**********************************************************************#
def writeInputFile(templateFilePath, inputFilePath, replacements):
    templateFile = open(templateFilePath, 'r')
    inputFile = open(inputFilePath, 'w')
    for line in templateFile:
        for text,replacement in replacements.items():
            line = line.replace(text, replacement)
        inputFile.write(line)
  
        
#**********************************************************************#
def writeTrueParamValsFile(questPath, path):
    with open(questPath, 'r') as f:
        paramRegex = re.compile(r'Initial Amount of ([a-zA-Z]+Rate)Part = ([0-9.]+)')
        matches = list(filter(lambda x: x != None, [re.match(paramRegex, line) for line in f]))
        params = {}
        for match in matches:
            params[match.group(1)] = match.group(2)
    paramNames = params.keys()
    with open(path, 'w') as f:
        for name in paramNames:
            f.write('{0}\t'.format(name))
        f.write('\n')
        for name in paramNames:
            f.write('{0}\t'.format(params[name]))
        f.write('\n')

#**********************************************************************#
def cleanSampleDir(saveTopLevelFiles=False):
    if saveTopLevelFiles : map(lambda dir: removeFSObject(dir), listDirs(SAM_DIR))
    else : cleanDir(SAM_DIR) 


#**********************************************************************#
def cleanDir(dirPath):
    if os.path.isdir(dirPath) : removeFSObject(dirPath)
    os.mkdir(dirPath)


#**********************************************************************#
def removeFSObject(fsObjectPath):
    if os.path.isfile(fsObjectPath)  : os.remove(fsObjectPath)
    elif os.path.isdir(fsObjectPath) : shutil.rmtree(fsObjectPath)


#**********************************************************************#
def listDirs(dirPath):
    return [os.path.join(dirPath, f) for f in os.listdir(dirPath) if os.path.isdir(os.path.join(dirPath, f))]


#**********************************************************************#
def listFiles(dirPath):
    return [os.path.abspath(os.path.join(dirPath, f)) for f in os.listdir(dirPath) if os.path.isfile(os.path.join(dirPath, f))]


#**********************************************************************#
def listDir(dirPath):
    return [os.path.join(dirPath, f) for f in os.listdir(dirPath)]


main()
