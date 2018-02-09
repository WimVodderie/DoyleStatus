import operator
import os
from queue import Queue
import statistics
import sqlite3
import threading

# for measuring how long execution takes
from timeit import default_timer as timer

dataBasePaths = ['/home/dfe01/doyle.db', 'doyle.db']


class DoyleFileDb(threading.Thread):

    TABLE_NAME = 'executed_tests'

    def __init__(self):
        super(DoyleFileDb, self).__init__()
        self.reqs = Queue()
        self.start()

    def run(self):
        # check the possible locations of the database, first one wins
        for dataBasePath in dataBasePaths:
            if os.path.isfile(dataBasePath):
                print('Getting database at %s' % dataBasePath)
                break
        # if not found it could be a new database so we stay with the last tried path
        if not os.path.isfile(dataBasePath):
            print('Creating new database at %s' % dataBasePath)
        self.db = sqlite3.connect(dataBasePath, detect_types=sqlite3.PARSE_DECLTYPES)

        # check if table exists
        c = self.db.cursor()
        c.execute('SELECT name FROM sqlite_master WHERE type="table" AND name="%s"' % DoyleFileDb.TABLE_NAME)
        result = c.fetchall()
        c.close()
        # create table if it does not exist yet
        if len(result) == 0 or DoyleFileDb.TABLE_NAME not in result[0]:
            cmd = 'CREATE TABLE %s (file char(100) PRIMARY KEY, target char(100) NOT NULL, type char(10), server char(64) NOT NULL, queue char(64), xbetree char(32) NOT NULL, xbegroup char(64) NOT NULL, xbeproject char(100) NOT NULL, xbebuildid INTEGER, tfsbuildid INTEGER, queuedtime TIMESTAMP, firstexecutiontime TIMESTAMP, lastexecutiontime TIMESTAMP)' % DoyleFileDb.TABLE_NAME
            print(cmd)
            self.db.execute(cmd)
            self.db.commit()

        while True:
            req, arg, res = self.reqs.get()

            if req == 'loadFile':
                res.put(self._loadFile(arg))
            if req == 'addFile':
                self._addFile(arg)
            if req == 'updateFile':
                self._updateFile(arg)
            if req == 'getExecutionTimes':
                res.put(self._getExecutionTimes(*arg))
            if req == 'getExpectedExecutionTime':
                res.put(self._getExpectedExecutionTime(arg))
            if req == 'getDoyleHistory':
                res.put(self._getDoyleHistory(*arg))
            if req == '--close--':
                break

    def loadFile(self, doyleFile):
        res = Queue()
        self.reqs.put(('loadFile', doyleFile, res))
        return res.get()

    def _loadFile(self, doyleFile):
        # try to get entry from database
        c = self.db.cursor()
        c.execute('SELECT * FROM %s WHERE file IS "%s"' % (DoyleFileDb.TABLE_NAME, doyleFile.file))
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

            print('%s: loaded from db' % doyleFile.file)
            return True
        else:
            return False

    def addFile(self, doyleFile):
        self.reqs.put(('addFile', doyleFile, None))

    def _addFile(self, doyleFile):
        ''' Add a doyleFile object to the database.'''
        c = self.db.cursor()
        c.execute('INSERT INTO %s (file,target,type,server,queue,xbetree,xbegroup,xbeproject,xbebuildid,tfsbuildid,queuedtime) VALUES (?, ?, ? ,? ,? ,? ,? ,? ,? ,? ,? )' % DoyleFileDb.TABLE_NAME, (doyleFile.file,
                                                                                                                                                                                                     doyleFile.target, doyleFile.type, doyleFile.server, doyleFile.queue, doyleFile.xbetree, doyleFile.xbegroup, doyleFile.xbeproject, doyleFile.xbebuildid, doyleFile.tfsbuildid, doyleFile.queuedTime, ))
        self.db.commit()
        print('%s: inserted in db' % doyleFile.file)

    def updateFile(self, doyleFile):
        self.reqs.put(('updateFile', doyleFile, None))

    def _updateFile(self, doyleFile):
        ''' Update the parts of the doyleFile that change.'''
        # only update the database when something has changed
        if doyleFile.firstExecutionTime!=None and doyleFile.lastExecutionTime!=None and doyleFile.server!=None:
            c = self.db.cursor()
            c.execute('UPDATE %s SET firstexecutiontime=?,lastexecutiontime=?,server=?  WHERE file IS "%s"' % (
                DoyleFileDb.TABLE_NAME, doyleFile.file), (doyleFile.firstExecutionTime, doyleFile.lastExecutionTime, doyleFile.server, ))
            self.db.commit()
            print('%s: saved to db (exec time %s -> %s @ %s)' %
                (doyleFile.file, doyleFile.firstExecutionTime, doyleFile.lastExecutionTime, doyleFile.server))

    def getExecutionTimes(self, xbetree, xbegroup, xbeproject, target):
        res = Queue()
        self.reqs.put(('getExecutionTimes', (xbetree, xbegroup, xbeproject, target), res))
        return res.get()

    def _getExecutionTimes(self, xbetree, xbegroup, xbeproject, target):
        ''' Get a list of excecution times (in seconds) from the db for the given test (xbetree may be None or '').'''
        start = timer()

        c = self.db.cursor()
        if xbetree == None or xbetree == '':
            c.execute('SELECT firstexecutiontime,lastexecutiontime FROM %s WHERE firstexecutiontime IS NOT NULL AND xbegroup="%s" AND xbeproject="%s" AND target="%s"' % (
                DoyleFileDb.TABLE_NAME, xbegroup, xbeproject, target))
        else:
            c.execute('SELECT firstexecutiontime,lastexecutiontime FROM %s WHERE firstexecutiontime IS NOT NULL AND xbetree="%s" AND xbegroup="%s" AND xbeproject="%s" AND target="%s"' % (
                DoyleFileDb.TABLE_NAME, xbetree, xbegroup, xbeproject, target))
        entries = c.fetchall()
        c.close()

        # transform to seconds
        times = [(x[1] - x[0]).total_seconds() for x in entries]
        # filter the tests that lasted less than 10 seconds, this happens when a test detects that it should not execute after all
        times = [x for x in times if x > 10.0]

        end = timer()
        print('Got %s (%s useful) from db, took %.4fs' % (len(entries), len(times), (end - start)))

        return times

    def getExpectedExecutionTime(self, doyleFile):
        res = Queue()
        self.reqs.put(('getExpectedExecutionTime', doyleFile, res))
        return res.get()

    def _getExpectedExecutionTime(self, doyleFile):
        ''' Get the past execution times from the db and predict how long this test may take. Returns average, warning and fail execution times for it.'''

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
                print('%s: 0 entries in db -> warn %s fail %s' % (doyleFile.file, warnTime, failTime))

            elif len(times) == 1:
                # cannot do statistics when there is only 1 data point
                averageTime = times[0]
                warnTime = averageTime * 1.5
                failTime = averageTime * 2.0
                print('%s: 1 entry in db %s -> warn %s fail %s' % (doyleFile.file, averageTime, warnTime, failTime))

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
                print('%s: %s d%s (%s) -> %s d%s (%s) -> warn %s fail %s' %
                      (doyleFile.file, m, sd, len(times), mf, sdf, len(tf), warnTime, failTime))

        except:
            print('Gathering times failed with exception: %s' % traceback.format_exc())

        return (averageTime, warnTime, failTime)

    def getDoyleHistory(self, doyleServer, count):
        res = Queue()
        self.reqs.put(('getDoyleHistory', (doyleServer, count), res))
        return res.get()

    def _getDoyleHistory(self, doyleServer, count):
        start = timer()

        c = self.db.cursor()
        c.execute('SELECT xbetree,xbegroup,xbeproject,xbebuildid,target,firstexecutiontime,lastexecutiontime FROM %s WHERE firstexecutiontime IS NOT NULL AND server LIKE "%s"' % (
            DoyleFileDb.TABLE_NAME, doyleServer))
        entries = c.fetchall()
        c.close()

        # get all entries that lasted at least 10 seconds
        entriesFiltered = [x for x in entries if (x[6] - x[5]).total_seconds() > 10.0]

        # sort on firstexecutiontime (item 5 in the tuple)
        entriesSorted = sorted(entriesFiltered, key=operator.itemgetter(5), reverse=True)

        # take the number of requested entries
        entriesSorted = entriesSorted[0:count]

        end = timer()
        print('Got %s of %s on %s from db, took %.4fs' % (len(entriesSorted), len(entriesFiltered), doyleServer, (end - start)))

        return entriesSorted

    def removeUselessItems(self):
        # remove all items that have no first and last execution time
        c = self.db.cursor()
        c.execute('DELETE FROM %s WHERE firstexecutiontime IS NULL AND lastexecutiontime IS NULL' % DoyleFileDb.TABLE_NAME)
        self.db.commit()
