import unittest
from time_series.data_point import DataPoint

class TestDataPoint(unittest.TestCase):
    def testConstructor(self):
        dataPoint = DataPoint(1,2)
        self.assertEqual(1, dataPoint.time)
        self.assertEqual(2, dataPoint.amount)

    def testComparePoints(self):
        point = DataPoint(1,2)
        self.assertEquals(DataPoint(1,2), point)
        self.assertNotEqual(DataPoint(1,1), point)
        self.assertNotEqual(DataPoint(2,1), point)
