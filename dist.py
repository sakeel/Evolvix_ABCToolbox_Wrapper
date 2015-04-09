import sys
import inspect

try:
    from rpy2.robjects import r
except ImportError:
    pass

def L2(obsData, simData):
    dist = 0
    for i in range(0, len(simData)):
        dist += math.pow(simData[i] - obsData[i], 2)
    return dist

def normalizedL2(obsData, simData):
    dist = 0
    for i in range(0, len(obsData)):
        dist += math.pow(simData[i] - obsData[i], 2) / max(obsData[i], 1)
    return dist
    
def geometric(obsData, simData):
    dist = 1
    for i in range(0, len(obsData)):
        z = max(obsData[i],1)
        dist *= max(math.pow((simData[i] - obsData[i]), 2) / z, 1/z)
    return math.pow(dist, 1/len(obsData))
    
def dissim(obsData, simData):
    #throws exception if library not found
    r('suppressMessages(library(TSdist))')
    dataStrings = list(map(lambda data: ','.join(str(a) for a in data), [obsData, simData]))
    dist = float(r('dissimDistance(c({}),c({}))'.format(dataStrings[0], dataStrings[1]))[0])
    return dist

#the following code needs to be below all function definitions
funcObjects = inspect.getmembers(sys.modules[__name__], inspect.isfunction)
distFuncs = {name: func for name, func in funcObjects}
