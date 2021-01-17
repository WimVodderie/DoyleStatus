import sqlite3
import os
import datetime
import tempfile

from app import queuecountsdb


class TestQueueCountsDb:
    def setup(self):
        self.dbPath = tempfile.TemporaryDirectory()
        self.dbFile = os.path.join(self.dbPath.name, "testqueuecounts.db")
        self.db = sqlite3.connect(self.dbFile, detect_types=sqlite3.PARSE_DECLTYPES)
        self.sut = queuecountsdb.QueueCountsDb(self.db)

    def teardown(self):
        self.db.close()
        self.dbPath.cleanup()

    def test_add1(self):
        d = datetime.datetime(year=2020, month=12, day=1, hour=12)

        self.sut.add(d, 10)
        self.sut.add(d, 12)

        chartData = self.sut.getChartData(d.date())

        assert len(chartData) == 1
        assert chartData[0][0] == d
        assert chartData[0][1] == 10  # min
        assert chartData[0][2] == 11  # avg
        assert chartData[0][3] == 12  # max

    def test_add2(self):
        d1 = datetime.datetime(year=2020, month=12, day=1, hour=12)
        d2 = datetime.datetime(year=2020, month=12, day=1, hour=13)

        self.sut.add(d1, 10)
        self.sut.add(d1, 12)
        self.sut.add(d2, 14)
        self.sut.add(d2, 16)

        chartData = self.sut.getChartData(d1.date())

        assert len(chartData) == 2
        assert chartData[0][0] == d1
        assert chartData[0][1] == 10  # min
        assert chartData[0][2] == 11  # avg
        assert chartData[0][3] == 12  # max
        assert chartData[1][0] == d2
        assert chartData[1][1] == 14  # min
        assert chartData[1][2] == 15  # avg
        assert chartData[1][3] == 16  # max
