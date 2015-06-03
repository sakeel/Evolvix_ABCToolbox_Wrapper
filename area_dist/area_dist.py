def getAreaDist(interp1, interp2):
    times1 = interp1.times
    times2 = interp2.times
    if times1[0] != times2[0]:
        raise Exception('The interpolations must have the same start time.')
    if times1[-1] != times2[-1]:
        raise Exception('The interpolations must have the same end time.')

    times = sorted(set(interp1.times + interp2.times))

    #look for intersections between the two interpolations
    intersectionTimes = []
    for i in range(0, len(times)-1):
        t1 = times[i]
        t2 = times[i+1]
        params1 = interp1.getInterpParams(t1)
        params2 = interp2.getInterpParams(t1)
        #check if lines are parallel 
        if params1[0] == params2[0]: continue
        intersection = (params2[1] - params1[1]) / (params1[0] - params2[0])
        #check if the intersection is in the open interval
        if intersection > t1 and intersection < t2:
            intersectionTimes.append(intersection)
    times = sorted(times + intersectionTimes)

    #get the intervals over which we'll integrate over
    #integralIntervals is a list of pairs, which are the intervals
    integralIntervals = zip(times[0:len(times)-1], times[1:])

    areas = []
    for interp in [interp1, interp2]:
        areas.append(map(lambda interval: getArea(interval[0], interval[1], interp),
                         integralIntervals))
    absAreas = [abs(area1 - area2) for area1,area2 in zip(*areas)]
    return sum(absAreas)

def getArea(time1, time2, interp):
    times = interp.times
    width = abs(time2 - time1)
    return 0.5*width*(interp.getVal(time1) + interp.getVal(time2))
