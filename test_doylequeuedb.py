import os
import datetime

from app import doylefiledb

#testDbPath="./TestData/TestDb"
testDbPath="/tmp"

class TestDoyleQueueDb:
    def setup(self):
        os.remove(f"{testDbPath}/{doylefiledb.DoyleFileDb.DBFILE_NAME}")
        self.d = doylefiledb.DoyleFileDb(testDbPath)

    def teardown(self):
        self.d.quit()

    def test_init(self):
        start_date=datetime.datetime(year=2000,month=1,day=1)
        end_date=datetime.datetime(year=2000,month=12,day=31)
        assert len(self.d.getCounts(start_date,end_date)) == 0

    def test_add(self):
        d=datetime.datetime(year=2000,month=1,day=2)
        c=10
        self.d.addCount(d,c)

        # now there should be one entry
        start_date=datetime.datetime(year=2000,month=1,day=1)
        end_date=datetime.datetime(year=2000,month=12,day=31)
        assert len(self.d.getCounts(start_date,end_date)) == 1



