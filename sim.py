#!/usr/bin/env python
#
#  @file  sim.py
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
import pprint
import math
import os
import sys
import glob
import argparse

try:
    from rpy2.robjects import r
except ImportError:
    print("Could not find rpy2. Error will occur if sim.py uses rpy2.")

BIN_DIR = os.path.dirname(os.path.abspath(__file__))
QST_DIR = None
QUEST_NAME = None
DISTANCE_FUNC = None

def main():
    args = parseArgs()
    global QUEST_NAME
    QUEST_NAME = args.quest
    QST_DIR = '{0}/Quests/{1}'.format(os.path.abspath(BIN_DIR + '/..'), QUEST_NAME)

    setDistanceFunc(args.distance)

    paramsArg = getParamsArg()
    if os.path.isfile('Worker_SSA_SDM'):
        workerPath = './Worker_SSA_SDM'
    else:
        workerPath = BIN_DIR + '/Worker_SSA_SDM'
 
    os.system('{0} {1}Quest.epb {2} >> /dev/null'.format(workerPath, QUEST_NAME, paramsArg))

    obsData = getData([QUEST_NAME + 'Data.txt'])
    simData = getData(glob.glob('TS*.txt'))
    dist = getDist(obsData, simData)
    with open('summary_stats_temp.txt', 'w') as f:
        print('myDist\n%.10f\n' % dist, file=f)

def parseArgs():
    parser = argparse.ArgumentParser(description='Run a simulation.',
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('quest', type=str, help='Name of the Quest.')
    parser.add_argument('--distance', type=str, help='Specify the distance to be used.', default='L2')
    return parser.parse_args()

def getParamsArg():
    paramsFile = open(QUEST_NAME + '-temp.par', 'r')
    params = []
    for line in paramsFile:
        fields = [x.strip() for x in  line.split(':')]
        params.append('{0}Part={1}'.format(fields[0], fields[1]))
    return '--Change_Model ' + ' '.join(params) 

def setDistanceFunc(funcName):
    funcs = {
        'L2': calculateL2Dist,
        'normalizedL2': calculateNormalizedL2Dist,
        'geometric': calculateGeometricDist,
        'dissim': calculateDissimDist
    }
    try:
        global DISTANCE_FUNC
        DISTANCE_FUNC = funcs[funcName]
    except KeyError:    
        print('Invalid distance function name: {}'.format(funcName))
        sys.exit(1)


def getData(filePaths):
    files = map(lambda x: open(x, 'r'), filePaths)
    data = {}
    for f in files:
        fileData = {}
        headers = f.readline().split()
        for header in headers:
            fileData[header] = []
        for line in f:
            for i in range(0, len(headers)):
                fileData[headers[i]].append(float(line.split()[i]))
        mergeData(data, fileData)
    return data;

def mergeData(data, newData):
    if 'Time' in data:
        if data['Time'] != newData['Time']:
            raise Exception('Times do not match while merging data.')   
    else:
        data['Time'] = newData['Time']

    for key in newData:
        if key == 'Time': continue
        if key in data:
            raise Exception('Cannot overwrite amounts while merging data.')
        data[key] = newData[key]

def getDist(obsData, simData):
    distances = {}
    if obsData.keys() != simData.keys():
        raise Exception('Keys must be equal when calculating the distance.')
    if obsData['Time'] != simData['Time']:
        raise Exception('Times must be equal when calculating the distance.')
    for key in obsData:
        if key == 'Time': continue
        if len(obsData[key]) != len(simData[key]):
            raise Exception("Distance function requires vectors of the same length")
        distances[key] = DISTANCE_FUNC(obsData[key], simData[key])
    dist = 0
    for key in distances:
        dist  += distances[key]
    return dist

def calculateL2Dist(obsData, simData):
    dist = 0
    for i in range(0, len(simData)):
        dist += math.pow(simData[i] - obsData[i], 2)
    return dist
    
def calculateNormalizedL2Dist(obsData, simData):
    dist = 0
    for i in range(0, len(obsData)):
        dist += math.pow(simData[i] - obsData[i], 2) / max(obsData[i], 1)
    return dist
    
def calculateGeometricDist(obsData, simData):
    dist = 1
    for i in range(0, len(obsData)):
        z = max(obsData[i],1)
        dist *= max(math.pow((simData[i] - obsData[i]), 2) / z, 1/z)
    return math.pow(dist, 1/len(obsData))
    
def calculateDissimDist(obsData, simData):
    #throws exception if library not found
    r('suppressMessages(library(TSdist))')
    dataStrings = list(map(lambda data: ','.join(str(a) for a in data), [obsData, simData]))
    dist = float(r('dissimDistance(c({}),c({}))'.format(dataStrings[0], dataStrings[1]))[0])
    return dist
 
main()
