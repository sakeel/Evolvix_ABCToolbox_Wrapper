import unittest
from time_series.data_point import DataPoint
from time_series.time_series import TimeSeries

class TestTimeSeries(unittest.TestCase):
    def setUp(self):
        self.data = [DataPoint(1,2), DataPoint(3,4)]
        self.ts = TimeSeries(self.data)

    def testConstructor(self):
        self.assertEqual(self.data, self.ts._data)

    def testDataIsCopied(self):
        self.data[0] = DataPoint(0,0) #assign a different tuple
        self.assertEqual(DataPoint(1,2), self.ts._data[0])

    def testIteration(self):
        data = []
        for dataPoint in self.ts:
           data.append(dataPoint)
        self.assertEqual(self.data, data)

    def testOutOfOrderIteration(self):
        swappedData = [self.data[1], self.data[0]]
        swappedTS = TimeSeries(swappedData)
        data = []
        for dataPoint in swappedTS:
            data.append(dataPoint)
        self.assertEqual(self.data, data)

    def testNonUniqueTimes(self):
        self.data.append(DataPoint(1,8))
        self.assertRaisesRegexp(Exception,
                                "duplicate",
                                lambda: TimeSeries(self.data))
