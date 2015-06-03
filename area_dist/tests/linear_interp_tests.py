import unittest
from time_series.data_point import DataPoint
from time_series.time_series import TimeSeries
from linear_interp import LinearInterp

class TestLinearInterp(unittest.TestCase):
    def testConstantTS(self):
        data = [DataPoint(0,1), DataPoint(2,1)]
        ts = TimeSeries(data)
        interp = LinearInterp(ts)

        testTimes = [x * 0.1 for x in range(0, 20)]
        for t in testTimes:
            self.assertEqual(1, interp.getVal(t))

    def testLinearTS(self):
        data = [DataPoint(0,1), DataPoint(2,6), DataPoint(3,5)]
        ts = TimeSeries(data)
        interp = LinearInterp(ts)

        for t in [x * 0.1 for x in range(0, 20)]:
            self.assertEqual(2.5*t+1, interp.getVal(t))

        testTimes = [x * 0.1 for x in range(20, 30)]
        for t in testTimes:
            self.assertEqual(-1*t+8, interp.getVal(t))

    def testLinearTS(self):
        data = []
        ts = TimeSeries(data)
        self.assertRaisesRegexp(Exception,
                                '1 or fewer',
                                lambda : LinearInterp(ts))

    def testNegativeTime(self):
        data = [DataPoint(0,1), DataPoint(2,6)]
        ts = TimeSeries(data)
        interp = LinearInterp(ts)
        self.assertRaisesRegexp(Exception,
                                'negative time',
                                lambda : interp.getVal(-1))

    def testPositiveStartingTime(self):
        data = [DataPoint(1,1), DataPoint(2,6)]
        ts = TimeSeries(data)
        interp = LinearInterp(ts)
        for t in [x * 0.1 for x in range(10, 20)]:
            self.assertEqual(5*t-4, interp.getVal(t))

    def testTooSmallOfTime(self):
        data = [DataPoint(1,1), DataPoint(2,6)]
        ts = TimeSeries(data)
        interp = LinearInterp(ts)
        self.assertRaisesRegexp(Exception,
                                'outside of the interpolation domain',
                                lambda : interp.getVal(0.5))

    def testTooLargeOfTime(self):
        data = [DataPoint(0,1), DataPoint(2,6)]
        ts = TimeSeries(data)
        interp = LinearInterp(ts)
        self.assertRaisesRegexp(Exception,
                                'outside of the interpolation domain',
                                lambda : interp.getVal(3))

    def testOneDataPoint(self):
        data = [DataPoint(1,2)]
        ts = TimeSeries(data)
        self.assertRaisesRegexp(Exception,
                                '1 or fewer',
                                lambda : LinearInterp(ts))
