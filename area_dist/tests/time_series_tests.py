import unittest
from time_series.time_series import TimeSeries

class TestTimeSeries(unittest.TestCase):
    def testConstructor(self):
        data = [(1,2), (3,4)]
        ts = TimeSeries(data)
        self.assertEqual(data, ts.data)

    def testConstructorParam(self):
        self.assertRaises(Exception, lambda: TimeSeries([(1,2), (3,4)]))
