import unittest
from time_series.data_point import DataPoint
from time_series.time_series import TimeSeries
from area_dist import getAreaDist
from linear_interp import LinearInterp

class TestAreaDist(unittest.TestCase):
    def testNonequalStartingTimes(self):
        interps = TestAreaDist.getInterps([[(0,1), (2,1)], [(1,1), (2,2)]])
        self.assertRaisesRegexp(Exception,
                                'same start time',
                                lambda : getAreaDist(*interps))

    def testNonequalEndingTimes(self):
        interps = TestAreaDist.getInterps([[(0,1), (1,1)], [(0,1), (2,2)]])
        self.assertRaisesRegexp(Exception,
                                'same end time',
                                lambda : getAreaDist(*interps))

    def testConstantTS(self):
        interps = TestAreaDist.getInterps([[(0,1), (2,1)], [(0,4), (1,4), (2,4)]])
        self.assertEqual(6, getAreaDist(*interps))

    def testCrossingTS(self):
        interps = TestAreaDist.getInterps([[(0,1), (1,5)], [(0,5), (1,1)]])
        self.assertEqual(2, getAreaDist(*interps))

    @staticmethod
    #data is something like [[(0,1)], [(2,2)]]
    def getInterps(data):
        def getSingleInterp(dataSet):
            dataPoints = map(lambda x: (DataPoint(*x)), dataSet)
            return LinearInterp(TimeSeries(dataPoints))
        return map(getSingleInterp, data)

    #test time series that cross
