from sets import Set

class TimeSeries:
    def __init__(self, data):
        #check for non-unique times
        timesSet = Set()
        for point in data:
            timesSet.add(point.time)
        if len(timesSet) != len(data):
            raise Exception('Data contains duplicate times.')
        self._data = sorted(data, lambda p1,p2: cmp(p1.time - p2.time, 0))

    def __len__(self):
        return len(self._data)
    
    def __getitem__(self, index):
        return self._data[index]
