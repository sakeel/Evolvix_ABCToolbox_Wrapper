from bisect import bisect_left

class LinearInterp:
    def __init__(self, ts):
        self._interp = {}
        self.times = []

        #do not add more keys to _interp after this loop
        #because times would be invalid
        if len(ts) > 1:
            for i in range(0, len(ts)-1):
                point1 = ts[i]
                point2 = ts[i+1]

                #_interp[(t_i, t_{i+1})] = (a,b), from y=ax+b
                a = (point2.amount - point1.amount) / (point2.time - point1.time)
                b = point1.amount - a * point1.time
                self._interp[point1.time, point2.time] = (a,b)

                self.times.append(ts[i].time)
        else:
            raise Exception('Cannot interpolate a time series with 1 or fewer '
                            'data points.')
        self.times.append(ts[len(ts)-1].time)

    def getInterpParams(self, time):
        if time < 0:
            raise Exception('Cannot get interpolation for a negative time')
        if time == self.times[0]:
            return self._interp[(time, self.times[1])]
        else:
            indexOfUpperTime = bisect_left(self.times, time)
            if indexOfUpperTime == 0 or indexOfUpperTime >= len(self.times):
                raise Exception(str(time) + ' is outside of the interpolation domain.')
            containingInterval = (self.times[indexOfUpperTime-1],
                                  self.times[indexOfUpperTime])
            return self._interp[containingInterval]

    def getVal(self, time):
        interpParams = self.getInterpParams(time)
        return interpParams[0]*time + interpParams[1]
