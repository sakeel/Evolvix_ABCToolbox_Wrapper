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

STAGE_FLAGS_USED = False


#**********************************************************************#
def main():
    args = parseArgs();
    
    global DISTANCE
    DISTANCE = args.distance
    setUpGlobalVars(args.quest)
    
    cleanWorkingDir(args)

    verifyQuestFilesExist(args.quest)
    validateArgs(args)
    
    makeTimeStampFile()
    
    if args.recover:
        htcondorSubmitDAGFile()
        sys.exit(0)
    
    if args.combine:
        combineSamples()
        cleanSampleDir(True)
    
    if args.htcondor : runOnHTCondor(args)
    else             : runLocally(args)

#**********************************************************************#
def cleanWorkingDir(args):

    if not os.path.isdir(WRK_DIR):
        os.mkdir(WRK_DIR)
        return
    
    noCleaning = False
    cleanUpSampleDir = True
    cleanUpSampleFiles = True
    cleanUpEstimateDir = True
    
    if (args.recover)     : noCleaning         = True
    if (args.add_samples) : cleanUpSampleFiles = False
    if (args.estimate)    : cleanUpSampleFiles = False
    if (args.combine)     : cleanUpSampleDir   = False
        
    if (noCleaning) : return
    
    if cleanUpSampleFiles and cleanUpSampleDir and cleanUpEstimateDir:
        cleanDir(WRK_DIR)
        return
        
    if cleanUpSampleDir : cleanSampleDir(not cleanUpSampleFiles)

    if cleanUpEstimateDir : cleanDir(EST_DIR)

    for file in listFiles(WRK_DIR) : os.remove(file)


#**********************************************************************#
def makeTimeStampFile():
    if not os.path.isdir(WRK_DIR): os.mkdir(WRK_DIR)
    # Create a time stamp file to capture the start time to use as the folder name in the history
    timeStampFilePath = '{0}/timestamp.txt'.format(WRK_DIR)
    timestampFile = open(timeStampFilePath, 'w')
    timestampFile.write(datetime.fromtimestamp(time.time()).strftime('%Y%m%d_%H%M%S'))
    timestampFile.close()

        
#**********************************************************************#
def setUpGlobalVars(questName):
    global QST_NAME
    global QST_DIR
    global HST_DIR
    global WRK_DIR
    global SAM_DIR
    global SAM_FILE
    global EST_DIR
    global DAG_DIR
    global DAG_FILE

    QST_NAME = questName 
    QST_DIR = os.path.abspath('{0}/../quests/{1}'.format(BIN_DIR, QST_NAME))
    HST_DIR = os.path.join(QST_DIR, 'History')
    WRK_DIR = os.path.join(QST_DIR, 'Working')
    SAM_DIR = os.path.join(WRK_DIR, 'sample')
    EST_DIR = os.path.join(WRK_DIR, 'estimate')
    DAG_DIR = os.path.join(WRK_DIR, 'dag')
    DAG_FILE = os.path.join(DAG_DIR, QST_NAME + '.dag')
    SAM_FILE = os.path.join(SAM_DIR, SAM_FILE_NAME)


#**********************************************************************#
def parseArgs():
    parser = argparse.ArgumentParser(description='Run ABC.',
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('--htcondor', help='Run the simulations on HTCondor', action='store_true')
    parser.add_argument('--sample', help='Generate the samples only.', action='store_true')
    parser.add_argument('--add-samples', help='Run like usual, but don\'t clean the old samples out, just add the new samples to them.', action='store_true')
    parser.add_argument('--combine', help='Won\'t generate samples, just combines any existing samples into the sample file.', action='store_true')
    parser.add_argument('--estimate', help='Use an existing sample file to estimate parameters.', action="store_true")
    parser.add_argument('--recover', help='Tries to recover in case of early termination. Valid only with runs using --htcondor', action='store_true')
    parser.add_argument('--test', help='Test configuration, Quest file processing, and generate files. Exits prior to any other action.', action='store_true')
    parser.add_argument('--distance', type=str, help='Specify the distance to be used. Options: '
                        'L2, normalizedL2, geometric, dissim', default='L2')
    parser.add_argument('-n', type=int, help='Number of simulations.')
    parser.add_argument('-c', type=int, help='Number of cores.', default=1)
    parser.add_argument('quest', type=str, help='Name of the quest')
    args = parser.parse_args()
    return args


#**********************************************************************#
def validateArgs(args):
    global STAGE_FLAGS_USED
    STAGE_FLAGS_USED =  (args.sample or args.combine or args.estimate)
    if args.sample or not STAGE_FLAGS_USED:
        if args.n <= 0: raise Exception('Number of simulations must be greater than zero.')
        if args.c <= 0: raise Exception('Number of cores must be greater than zero.')
    if (args.htcondor and not args.sample and (args.combine or args.estimate)):
        raise Exception('--htcondor can not be used with flags --combine or --estimate. Just remove the --htcondor flag and run either or both of those stages locally (assuming sampling is already complete).')
    if (args.recover and STAGE_FLAGS_USED):
        raise Exception('--recover can not be used with other stage flags (e.g. --sample, --combine, or --estimate)')
    if (args.recover and not os.path.isfile('{0}/{1}.dag'.format(DAG_DIR,args.quest))):
        raise Exception('--recover can only be used with quests with an existing dag file. No existing dag file found.')
    if (args.estimate and (not (args.sample or args.combine) or os.path.isfile('{0}/samples.txt'.format(DAG_DIR,args.quest)))):
        raise Exception('--estimate requires samples to have already been generated or to be called with an action that will generate samples.')


#**********************************************************************#
def verifyQuestFilesExist(QST_NAME):
    if(not os.path.isdir(QST_DIR)):
        print('Quest from command line: ' + QST_NAME)
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
def runLocally(args):
    if args.sample or not STAGE_FLAGS_USED:
        # run sampler and combine output
        runSampler(args.quest, args.n, args.c)
        combineSamples()

    if args.estimate or not STAGE_FLAGS_USED:
        # estimate based on the distance of the samples generated
        runEstimator(args.quest)


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
    shutil.copy(os.path.join(BIN_DIR, 'data.obs'), SAM_DIR)


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

    inputFilePath = os.path.join(SAM_DIR, QST_NAME + 'Sampler.input')
    writeInputFile(BIN_DIR + '/samplerTemplate.input', inputFilePath, replacements)
    return os.path.basename(inputFilePath) 


#**********************************************************************#
def runSamplerLocally(QST_NAME, nCores):

    procs = []

    samplerInput = os.path.join(SAM_DIR, QST_NAME + 'Sampler.input')
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

    estimatorFileName = writeEstimatorFile(QST_NAME)
    shutil.copy(SAM_DIR + '/data.obs', EST_DIR)
    shutil.copyfile(SAM_FILE, EST_DIR + '/out.txt_sampling1.txt')
    
    questPath = os.path.join(QST_DIR, '{0}Quest.txt'.format(QST_NAME))
    trueParamsValsPath = os.path.join(EST_DIR, 'true_param_vals.txt')
    writeTrueParamValsFile(questPath, trueParamsValsPath)
    
    callEstimator(estimatorFileName)
    callPlotScript(estimatorFileName)


#**********************************************************************#
def writeEstimatorFile(QST_NAME):
    replacements = {'N_PARAMS' : ','.join(map(str, range(2, getNumParams(QST_NAME)+2)))}
    inputFilePath = os.path.join(EST_DIR, QST_NAME + 'Estimator.input')
    writeInputFile(BIN_DIR + '/estimatorTemplate.input', inputFilePath, replacements)
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
    except subprocess.CalledPocessError:
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
    
    if args.sample or not STAGE_FLAGS_USED:
    # run sampler and combine output
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
    dagFile.write(htcondorGenerateSampleJobLines(args.quest, args.c))
    dagFile.write(htcondorGenerateEstimateJobLines(args.quest))

    dagFile.close()


#**********************************************************************#
def htcondorDagFileHeader(QST_NAME):
    dagHeader = '# DAGMan file ({0}.dag) for quest {0}\n'.format(QST_NAME)
    dagHeader += '#\n#  *** This is an automatically generated file from the Evolvix run.py script. ***'
    dagHeader += '\n#  *** Any changes to this file will be lost. ***\n\n\n'
    return dagHeader


#**********************************************************************#
def htcondorGenerateSampleJobLines(QST_NAME, nCores):

    inputFiles  = ','.join(listFiles(SAM_DIR)) 
    inputFiles += ',{0}/sim.py'.format(BIN_DIR)
    inputFiles += ',{0}/argparse.py'.format(BIN_DIR)
    inputFiles += ',{0}/Worker_SSA_SDM'.format(BIN_DIR)

    submitFile = os.path.join(BIN_DIR, 'evolvix_generic_condor.sub')

    return htcondorJobSpecificLines(nCores, submitFile, QST_NAME + 'Sampler.input', inputFiles)


#**********************************************************************#
def htcondorGenerateEstimateJobLines(QST_NAME):

    return '\nSCRIPT POST Evolvix_PE_Sample /usr/bin/env python {0}/run.py --combine --estimate {1}\n'.format(BIN_DIR, QST_NAME)


#**********************************************************************#
def htcondorJobSpecificLines(nCores, submitFile, inputFileName, inputFiles):
    jobName = 'Evolvix_PE_Sample'
    allJobSpecificLines   = 'JOB {0} {1}\n'.format(jobName, submitFile)
    allJobSpecificLines  += 'VARS {0} EVOLVIX_INITDIR="{1}"\n'.format(jobName, SAM_DIR)
    allJobSpecificLines  += 'VARS {0} EVOLVIX_BIN="ABCsampler"\n'.format(jobName)
    allJobSpecificLines  += 'VARS {0} EVOLVIX_BIN_DIR="{1}"\n'.format(jobName, BIN_DIR)
    allJobSpecificLines  += 'VARS {0} EVOLVIX_INPUT_FILE_NAME="{1}"\n'.format(jobName, inputFileName)
    allJobSpecificLines  += 'VARS {0} EVOLVIX_INPUT_FILES="{1}"\n'.format(jobName, inputFiles)
    allJobSpecificLines  += 'VARS {0} EVOLVIX_NUM_THREADS="{1}"\n'.format(jobName, nCores)
    return allJobSpecificLines
    

#**********************************************************************#
def htcondorSubmitDAGFile():
    try:
        subprocess.call(['condor_submit_dag', DAG_FILE])
    except OSError:
        raise Exception('There was an error submiting the HTCondor job. Check that HTCondor is installed with DAGMan.')


#**********************************************************************#
def combineSamples():

    if os.path.isfile(SAM_FILE) : combinedSamplesFile = open(SAM_FILE, 'a')
    
    sampleFiles = {}    
    if os.path.isdir(SAM_DIR):
        f = 'out.txt_sampling1.txt'
        sampleFiles = [os.path.join(dir,f) for dir in listDirs(SAM_DIR) if os.path.isfile(os.path.join(dir, f))] 

    for sampleFile in sampleFiles:
        if not os.path.isfile(SAM_FILE):
        # If the combined sample doesn't exist yet, copy over the first sample file to use
            shutil.copyfile(sampleFile, SAM_FILE)
            combinedSamplesFile = open(SAM_FILE, 'a')

        else:
        # The combined sample file already exists, so just read the sample file and append the content
            nextFile = open(sampleFile)
            nextFile.readline()
            print(''.join(nextFile.readlines()), file=combinedSamplesFile)
            nextFile.close()

        # Rename the file in case something goes wrong later, so we don't duplicate samples on the next combine
        os.rename(sampleFile, 'processed_out.txt_sampling1.txt')


#**********************************************************************#
def makeRunDirs(nCores):
    for i in range(0, nCores) : os.mkdir(os.path.join(SAM_DIR, str(i)))


#**********************************************************************#
def prepRunDirs(nCores):
    srcFiles = listFiles(SAM_DIR)
    
    try: srcFiles.remove(SAM_FILE)
    except ValueError: pass
    
    for i in range(nCores) :
        runDir = os.path.join(SAM_DIR, str(i))
        os.mkdir(runDir)
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
            f.write('{}\t'.format(name))
        f.write('\n')
        for name in paramNames:
            f.write('{}\t'.format(params[name]))
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
    return [os.path.join(dirPath, f) for f in os.listdir(dirPath) if os.path.isfile(os.path.join(dirPath, f))]


#**********************************************************************#
def listDir(dirPath):
    return [os.path.join(dirPath, f) for f in os.listdir(dirPath)]


main()
