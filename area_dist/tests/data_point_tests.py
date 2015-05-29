import unittest
from time_series.data_point import DataPoint

class TestDataPoint(unittest.TestCase):
    def testConstructor(self):
        dataPoint = DataPoint(1,2)
        self.assertEqual(1, dataPoint.time)
        self.assertEqual(2, dataPoint.amount)
