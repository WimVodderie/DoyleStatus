import datetime
import operator
import os
from queue import Queue, Empty
import shutil
import sqlite3
import threading
import time
import traceback
import statistics

# for measuring how long execution takes
from timeit import default_timer as timer

from app import queuecountsdb

class DoyleFileDb(threading.Thread):

    TABLE_NAME_TESTS = "executed_tests"
    DBFILE_NAME = "doyle.db"

    def __init__(self, dbFilePath, dbBackupPath):
        super(DoyleFileDb, self).__init__()
        self.dbFile = os.path.join(dbFilePath, DoyleFileDb.DBFILE_NAME)
        self.dbFilePath = dbFilePath
        self.dbBackupPath = dbBackupPath
        self.reqs = Queue()
        self.start()
        self.queueCounts = None

    def run(self):
        self.db = sqlite3.connect(self.dbFile, detect_types=sqlite3.PARSE_DECLTYPES)

        # check if table exists
        c = self.db.cursor()
        c.execute("SELECT name FROM sqlite_master WHERE type='table'")
        table_names = [x[0] for x in c.fetchall()]
        c.close()

        print(f"current db has following tables: {table_names}")

        # create table if it does not exist yet
        if DoyleFileDb.TABLE_NAME_TESTS not in table_names:
            cmd = f"CREATE TABLE {DoyleFileDb.TABLE_NAME_TESTS} (file char(100) PRIMARY KEY, target char(100) NOT NULL, type char(10), server char(64) NOT NULL, queue char(64), xbetree char(32) NOT NULL, xbegroup char(64) NOT NULL, xbeproject char(100) NOT NULL, xbebuildid INTEGER, tfsbuildid INTEGER, queuedtime TIMESTAMP, firstexecutiontime TIMESTAMP, lastexecutiontime TIMESTAMP)"
            print(cmd)
            self.db.execute(cmd)
            self.db.commit()

        # create queuecounts buffer
        self.queueCounts = queuecountsdb.QueueCountsDb(self.db)

        while True:
            try:
                req, arg, res = self.reqs.get(timeout=1)

                if req == "loadFile":
                    res.put(self._loadFile(arg))
                if req == "addFile":
                    self._addFile(arg)
                if req == "updateFile":
                    self._updateFile(arg)
                if req == "getExecutionTimes":
                    res.put(self._getExecutionTimes(*arg))
                if req == "getExpectedExecutionTime":
                    res.put(self._getExpectedExecutionTime(arg))
                if req == "getDoyleHistory":
                    res.put(self._getDoyleHistory(*arg))
                if req == "addQueuedCount":
                    self.queueCounts.add(*arg)
                if req == "getQueuedChartData":
                    res.put(self.queueCounts.getChartData(arg))
                if req == "getServerList":
                    res.put(self._getServerList())
                if req == "cleanupDatabase":
                    res.put(self._cleanupDatabase())
                if req == "backupDatabase":
                    self._backupDatabase()
                if req == "--close--":
                    break
            except Empty:
                # nothing to do, do some maintenance
                if self.queueCounts.conversionNeeded:
                    self.queueCounts.convertOldData()

        # cleanup
        self.db.close()

    def quit(self):
        # queue the command to stop the thread
        print("Asking db thread to stop")
        self.reqs.put(("--close--", None, None))
        print("Waiting for db thread to stop")
        self.join()

    def loadFile(self, doyleFile):
        res = Queue()
        self.reqs.put(("loadFile", doyleFile, res))
        return res.get()

    def _loadFile(self, doyleFile):
        # try to get entry from database
        c = self.db.cursor()
        c.execute(f"SELECT * FROM {DoyleFileDb.TABLE_NAME_TESTS} WHERE file IS '{doyleFile.file}'")
        result = c.fetchall()
        c.close()

        # if entry returned load all fields from the query result
        if len(result):
            doyleFile.file = result[0][0]
            doyleFile.target = result[0][1]
            doyleFile.type = result[0][2]
            doyleFile.server = result[0][3]
            doyleFile.queue = result[0][4]
            doyleFile.xbetree = result[0][5]
            doyleFile.xbegroup = result[0][6]
            doyleFile.xbeproject = result[0][7]
            doyleFile.xbebuildid = result[0][8]
            doyleFile.tfsbuildid = result[0][9]
            doyleFile.queuedTime = result[0][10]
            doyleFile.firstExecutionTime = result[0][11]
            doyleFile.lastExecutionTime = result[0][12]

            print(f"{doyleFile.file}: loaded from db")
            return True
        else:
            return False

    def addFile(self, doyleFile):
        self.reqs.put(("addFile", doyleFile, None))

    def _addFile(self, doyleFile):
        """ Add a doyleFile object to the database."""
        c = self.db.cursor()
        c.execute(
            f"INSERT INTO {DoyleFileDb.TABLE_NAME_TESTS} (file,target,type,server,queue,xbetree,xbegroup,xbeproject,xbebuildid,tfsbuildid,queuedtime) VALUES (?, ?, ? ,? ,? ,? ,? ,? ,? ,? ,? )",
            (doyleFile.file, doyleFile.target, doyleFile.type, doyleFile.server, doyleFile.queue, doyleFile.xbetree, doyleFile.xbegroup, doyleFile.xbeproject, doyleFile.xbebuildid, doyleFile.tfsbuildid, doyleFile.queuedTime),
        )
        c.close()
        self.db.commit()
        print(f"{doyleFile.file}: inserted in db")

    def updateFile(self, doyleFile):
        self.reqs.put(("updateFile", doyleFile, None))

    def _updateFile(self, doyleFile):
        """ Update the parts of the doyleFile that change."""
        # only update the database when something has changed
        if doyleFile.firstExecutionTime != None and doyleFile.lastExecutionTime != None and doyleFile.server != None:
            c = self.db.cursor()
            c.execute(f"UPDATE {DoyleFileDb.TABLE_NAME_TESTS} SET firstexecutiontime=?,lastexecutiontime=?,server=?  WHERE file IS '{doyleFile.file}'", (doyleFile.firstExecutionTime, doyleFile.lastExecutionTime, doyleFile.server))
            c.close()
            self.db.commit()
            print(f"{doyleFile.file}: saved to db (exec time {doyleFile.firstExecutionTime} -> {doyleFile.lastExecutionTime} @ {doyleFile.server})")

    def getExecutionTimes(self, xbetree, xbegroup, xbeproject, target):
        res = Queue()
        self.reqs.put(("getExecutionTimes", (xbetree, xbegroup, xbeproject, target), res))
        return res.get()

    def _getExecutionTimes(self, xbetree, xbegroup, xbeproject, target):
        """ Get a list of excecution times (in seconds) from the db for the given test (xbetree may be None or '')."""
        start = timer()

        c = self.db.cursor()
        if xbetree == None or xbetree == "":
            c.execute(f"SELECT firstexecutiontime,lastexecutiontime FROM {DoyleFileDb.TABLE_NAME_TESTS} WHERE firstexecutiontime IS NOT NULL AND xbegroup='{xbegroup}' AND xbeproject='{xbeproject}' AND target='{target}'")
        else:
            c.execute(f"SELECT firstexecutiontime,lastexecutiontime FROM {DoyleFileDb.TABLE_NAME_TESTS} WHERE firstexecutiontime IS NOT NULL AND xbetree='{xbetree}' AND xbegroup='{xbegroup}' AND xbeproject='{xbeproject}' AND target='{target}'")
        entries = c.fetchall()
        c.close()

        # transform to seconds and only keep entries where last time is after first time
        times = [(x[1] - x[0]).total_seconds() for x in entries if x[1] > x[0]]
        # filter the tests that lasted less than 10 seconds, this happens when a test detects that it should not execute after all
        times = [x for x in times if x > 10.0]

        end = timer()
        print(f"Got {len(entries)} ({len(times)} useful) from db, took {(end - start):.4}s")

        return times

    def getExpectedExecutionTime(self, doyleFile):
        res = Queue()
        self.reqs.put(("getExpectedExecutionTime", doyleFile, res))
        return res.get()

    def _getExpectedExecutionTime(self, doyleFile):
        """ Get the past execution times from the db and predict how long this test may take. Returns average, warning and fail execution times for it."""

        averageTime = 0.0
        warnTime = 0.0
        failTime = 0.0

        try:
            times = self._getExecutionTimes(doyleFile.xbetree, doyleFile.xbegroup, doyleFile.xbeproject, doyleFile.target)

            if len(times) == 0:
                # no data ? guess 1 hour as warning and 2 hours as fail
                averageTime = 3600.0
                warnTime = 3600.0
                failTime = 7200.0
                print(f"{doyleFile.file}: 0 entries in db -> warn {warnTime:.01f} fail {failTime:.01f}")

            elif len(times) == 1:
                # cannot do statistics when there is only 1 data point
                averageTime = times[0]
                warnTime = averageTime * 1.5
                failTime = averageTime * 2.0
                print(f"{doyleFile.file}: 1 entry in db {averageTime:.1f} -> warn {warnTime:.01f} fail {failTime:.01f}")

            else:
                # calculate mean and standard deviation
                m = statistics.mean(times)
                sd = statistics.stdev(times)

                # reject all numbers outside 3*stdev
                ll = m - 3 * sd
                ul = m + 3 * sd
                tf = [x for x in times if x < ul and x > ll]

                # calculate again, upper limit is mean + 3*stdev
                mf = statistics.mean(tf)
                sdf = statistics.stdev(tf)

                averageTime = mf
                warnTime = mf + 1 * sdf
                failTime = mf + 3 * sdf
                print(f"{doyleFile.file}: {m:.01f} d{sd:.01f} ({len(times)}) -> {mf:.01f} d{sdf:.01f} ({len(tf)}) -> warn {warnTime:.01f} fail {failTime:.01f}")

        except:
            print(f"Gathering times failed with exception: {traceback.format_exc()}")

        return (averageTime, warnTime, failTime)

    def getDoyleHistory(self, doyleServer, count):
        res = Queue()
        self.reqs.put(("getDoyleHistory", (doyleServer, count), res))

        # we got all entries from the database, now also compute what percentage of the time the server was busy
        return res.get()

    def _getDoyleHistory(self, doyleServer, count):
        start = timer()

        # let SQL order by first execution time and limit the output to the number of entries requested
        c = self.db.cursor()
        c.execute(f'SELECT xbetree,xbegroup,xbeproject,xbebuildid,target,firstexecutiontime,lastexecutiontime FROM {DoyleFileDb.TABLE_NAME_TESTS} WHERE firstexecutiontime IS NOT NULL AND server LIKE "{doyleServer}" ORDER BY firstexecutiontime DESC LIMIT {count}')
        entries = c.fetchall()
        c.close()

        end = timer()
        print(f"Got {len(entries)} on {doyleServer} from db, took {(end - start):.04f}s")
        return entries

    def addQueuedCount(self, timestamp, count):
        self.reqs.put(("addQueuedCount", (timestamp, count), None))

    def getQueuedChartData(self, date):
        res = Queue()
        self.reqs.put(("getQueuedChartData", (date), res))
        return res.get()

    def getServerList(self):
        res = Queue()
        self.reqs.put(("getServerList", None, res))
        return res.get()

    def _getServerList(self):
        """ Get a list of servers that have executed doyle tests."""
        start = timer()

        c = self.db.cursor()
        c.execute("SELECT DISTINCT server FROM executed_tests ORDER BY server ASC")
        result = c.fetchall()
        serverList = [s[0] for s in result]
        serverList.remove("")
        serverList.remove("Startup")
        c.close()

        end = timer()
        print(f"Got {len(serverList)} servers from db, took {end - start}s")
        return serverList

    def _removeUselessItems(self):
        """ Remove all items that have no first or last execution time."""
        c = self.db.cursor()
        c.execute(f"DELETE FROM {DoyleFileDb.TABLE_NAME_TESTS} WHERE firstexecutiontime IS NULL OR lastexecutiontime IS NULL")
        c.close()
        self.db.commit()

    def _removeOldTests(self):
        """ Go over the database and limit for each test the number of records to the 100 most recent tests."""
        start = timer()

        # first get a list of all unique tests
        c = self.db.cursor()
        c.execute(f"SELECT DISTINCT xbetree,xbegroup,xbeproject,target FROM {DoyleFileDb.TABLE_NAME_TESTS}")
        allTests = c.fetchall()
        c.close()

        # keep some counts
        numberOfTests = len(allTests)
        numberOfTestsCleaned = 0
        numberOfRowsDeleted = 0

        # now for each test in the list
        for test in allTests:

            # get the execution time of the 100th instance of this test
            c = self.db.cursor()
            c.execute(f'SELECT firstexecutiontime FROM {DoyleFileDb.TABLE_NAME_TESTS} WHERE xbetree IS "{test[0]}" AND xbegroup IS "{test[1]}" AND xbeproject="{test[2]}" AND target IS "{test[3]}" ORDER BY firstexecutiontime DESC LIMIT 1 OFFSET 100')
            result = c.fetchall()
            c.close()

            # we will get no result when there are less than 100 instances
            if len(result) == 1:
                numberOfTestsCleaned = numberOfTestsCleaned + 1
                keepFirstExecutionTime = result[0][0]
                print(f"{'.'.join(test)} -> purge older than {keepFirstExecutionTime}")

                # delete the records that executed before the selected time and get the count of deleted records
                c = self.db.cursor()
                c.execute(f'DELETE FROM {DoyleFileDb.TABLE_NAME_TESTS} WHERE xbetree IS "{test[0]}" AND xbegroup IS "{test[1]}" AND xbeproject="{test[2]}" AND target IS "{test[3]}" AND firstexecutiontime<="{keepFirstExecutionTime}"')
                c.execute("SELECT changes()")
                result = c.fetchall()
                if len(result) > 0:
                    numberOfRowsDeleted = numberOfRowsDeleted + result[0][0]
                c.close

        self.db.commit()

        # compact the database
        c = self.db.cursor()
        c.execute("VACUUM")
        c.close
        self.db.commit()

        end = timer()
        print(f"Removed {numberOfRowsDeleted} rows from {numberOfTestsCleaned} of {numberOfTests} distinct tests, took {(end - start):.04f}s")
        return (numberOfRowsDeleted, numberOfTestsCleaned, numberOfTests)

    def cleanupDatabase(self):
        res = Queue()
        self.reqs.put(("cleanupDatabase", None, res))
        return res.get()

    def _cleanupDatabase(self):
        self._removeUselessItems()
        self._removeOldTests()

    def backupDatabase(self):
        self.reqs.put(("backupDatabase", None, None))

    def _backupDatabase(self):
        try:
            # backup to db on local folder, cannot create a db on a share
            backupFileName = f"doyledb-{time.strftime('%Y%m%d-%H%M%S')}.db"
            tmpFile = os.path.join(self.dbFilePath, backupFileName)
            print(f"Backing up database to {tmpFile}")
            backup_db = sqlite3.connect(tmpFile)
            self.db.backup(backup_db)
            backup_db.close()
            print(f"Backing up database done")

            # now move the file to where it should have been
            tgtFile = os.path.join(self.dbBackupPath, backupFileName)
            shutil.move(tmpFile, tgtFile)
            print(f"Moved backup file to {tgtFile}")
        except:
            print(f"Backing up database failed: {traceback.format_exc()}")
