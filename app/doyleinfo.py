import datetime
import operator
import os
import sys
import threading
import time
import traceback
from dataclasses import dataclass

# for measuring how long execution takes
from timeit import default_timer as timer

from app.doylefilecache import DoyleFileCache
from app.doylefolder import DoyleFolder, DoyleFolderType
from app.doylefiledb import DoyleFileDb
from app.doylefile import DoyleFile
from app.doyleresult import DoyleResult

serverBlackList = ["DOYLE-CORDOVA", "VM-DOYLE-YUI", "VM-DOYLE-22"]

@dataclass
class FolderConfiguration:
    testFilesRoot:str
    databasePath:str
    databaseBackupPath:str

onLinuxReal = FolderConfiguration("/mnt/udrive/Doyle","/tmp","/mnt/udrive/Doyle/Databases")
onWindowsReal = FolderConfiguration("U:\\Doyle",".","U:\\Doyle\\Db")
onLinuxTest = FolderConfiguration("./TestData","/tmp","/tmp/Db")
onWindowsTest = FolderConfiguration(".\\TestData",".\\TestData",".\\TestData\\Db")

class DoyleInfo(threading.Thread):
    """ Main class that keeps and updates test info for queues and servers."""

    def __init__(self):

        # find out which folder configuration to take
        for config in [onLinuxReal,onWindowsReal,onLinuxTest,onWindowsTest]:
            print(f"Trying: {config}")
            print(f"isdir {config.testFilesRoot}: {os.path.isdir(config.testFilesRoot)}")
            print(f"isdir {config.databasePath}: {os.path.isdir(config.databasePath)}")


            if os.path.isdir(config.testFilesRoot) and os.path.isdir(config.databasePath):
                print(f"Getting doyle info from    : {config.testFilesRoot}")
                print(f"Storing database on        : {config.databasePath}")
                print(f"Storing database backup on : {config.databaseBackupPath}")
                self.folderConfig = config
                break
        else:
            sys.exit("None of the folder configurations lead to TestQueues and TestServers!")

        self.cache = DoyleFileCache()
        self.queueFolder = DoyleFolder(DoyleFolderType.queueFolder, os.path.join(self.folderConfig.testFilesRoot, "TestQueues"))
        self.serverFolder = DoyleFolder(DoyleFolderType.serverFolder, os.path.join(self.folderConfig.testFilesRoot, "TestServers"))

        self.result = DoyleResult()
        self._clean()

        # create file database and pass it (as a static) to DoyleFile
        self.doyleFileDb = DoyleFileDb(self.folderConfig.databasePath,self.folderConfig.databaseBackupPath)
        DoyleFile.doyleFileDb = self.doyleFileDb

        self.keepRunning = True
        self.cleanDatabaseRequested = False
        self.backupDatabaseRequested = False

        # keep track which servers should be busy and the first time this occured so we can report for how long it should have been busy
        self.shouldBeBusyServersFirstDetected = {}

        threading.Thread.__init__(self)
        self.start()

    def quit(self):
        # signal thread to stop
        print("Asking info thread to stop")
        self.keepRunning = False
        # wait for thread to stop
        print("Waiting for info thread to stop")
        self.join()
        # stop the database thread
        self.doyleFileDb.quit()

    def run(self):
        count = 20
        while self.keepRunning:
            if count >= 20:
                self._update()
                count = 0
            if self.cleanDatabaseRequested == True:
                self.result.clear("Busy cleaning the database, try again a bit later")
                self.doyleFileDb.cleanupDatabase()
                self.cleanDatabaseRequested = False

            if self.backupDatabaseRequested == True:
                self.result.clear("Backing up the database, try again a bit later")
                self.doyleFileDb.backupDatabase()
                self.backupDatabaseRequested = False

            count = count + 1
            time.sleep(1)

    def _clean(self):
        self.serverConfigs = []
        self.serversForAllQueues = []
        self.cache.resetUsedCount()

    def ageToString(self, age):
        # clocks may not be synchronized so age might be slightly negative - display that as 1s
        if age.total_seconds() < 0:
            ageString = "1s"
        elif age.days > 0:
            ageString = "%sd" % age.days
        elif age.seconds > 3600:
            ageString = "{0:.1f}h".format(age.seconds / 3600)
        elif age.seconds > 60:
            ageString = "%sm" % int(age.seconds / 60)
        else:
            ageString = "%ss" % age.seconds
        return ageString

    def getServerConfigs(self, baseDir):
        start = timer()

        resultDict = {}
        for f in os.listdir(baseDir):
            if os.path.splitext(f)[1].lower() == ".cfg":
                serverName = os.path.splitext(f)[0].upper()
                for line in open(os.path.join(baseDir, f)):
                    queueName = line.strip(" \n").split("\\")[-1].upper()
                    if queueName in resultDict:
                        resultDict[queueName].append(serverName)
                    else:
                        resultDict[queueName] = [serverName]

        end = timer()
        print("Getting %s server configs took  %.4fs" % (len(resultDict), (end - start)))

        return resultDict

    def _update(self):
        """ Re-read queue and server folders and build a new result."""
        start = timer()
        try:
            self._clean()
            newResult = DoyleResult()

            # update information from the queues and the servers
            self.queueFolder.update(self.cache)
            self.serverFolder.update(self.cache)

            # save all the doyleFiles that have not been referenced anymore
            unusedEntries = self.cache.removeUnusedEntries()
            for (file, doyleFile) in unusedEntries:
                doyleFile.save()

            self.serverConfigs = self.getServerConfigs(self.serverFolder.baseFolder)

            # build a list of servers that should be handling the queues
            for queue, files, dummy in self.queueFolder.items:
                if len(files):
                    if queue.upper() in self.serverConfigs:
                        self.serversForAllQueues.extend(self.serverConfigs[queue.upper()])
            self.serversForAllQueues = list(set(self.serversForAllQueues))

            # update the number of queued tests
            self.doyleFileDb.addCount(datetime.datetime.now(), self.queueFolder.count)

            # compile two lists with servers to report: the first list has all the servers, the second has only the servers that have non-default style
            # compile a list with all executing tests
            for server, files, upgradePending in self.serverFolder.items:
                # should we display info about this server
                doyleServerAge = "---"
                serverMessages = []
                style = "default"

                # there are files executing on this server
                if len(files) > 0:
                    serverMessages.append("Executing")

                # server has an upgrade pending
                if server not in serverBlackList:
                    if upgradePending == True:
                        serverMessages.append("Server has an upgrade pending")
                        style = "warning"

                # server should be busy but is not
                if server in self.serversForAllQueues and len(files) == 0:
                    if server not in self.shouldBeBusyServersFirstDetected:
                        self.shouldBeBusyServersFirstDetected[server] = datetime.datetime.now()
                        print(f"Server {server} because 'should be busy' at {datetime.datetime.now()}")
                    age = datetime.datetime.now() - self.shouldBeBusyServersFirstDetected[server]
                    if age > datetime.timedelta(minutes=5):
                        doyleServerAge = self.ageToString(age)
                        serverMessages.append("Server should be busy but is not")
                        style = "danger"
                else:
                    # server is not needed or server is busy so take it out of dictionary
                    if server in self.shouldBeBusyServersFirstDetected:
                        del self.shouldBeBusyServersFirstDetected[server]
                        print(f"Server {server} leaves 'should be busy' at {datetime.datetime.now()}")

                # check if doyle server is active
                if server not in serverBlackList:
                    aliveFile = os.path.join(self.serverFolder.baseFolder, server, "alive.dat")
                    if os.path.isfile(aliveFile):
                        age = datetime.datetime.now() - datetime.datetime.fromtimestamp(os.path.getmtime(aliveFile))
                        if age > datetime.timedelta(minutes=5):
                            doyleServerAge = self.ageToString(age)
                            serverMessages.append("DoyleServer Not Running")
                            style = "danger"
                    else:
                        serverMessages.append("DoyleServer status unknown")

                # check ping result
                #        if server not in serverBlackList:
                #            msg='Ping status unknown'
                #            for server2,alive in pingStates:
                #               if alive:
                #                   msg=''
                #                else:
                #                    msg='Ping Not Responding'
                #            if len(msg)>0:
                #                serverMessages.append(msg)
                #                style='danger'

                if len(serverMessages) > 0:
                    row = [style, doyleServerAge, server, ", ".join(serverMessages)]
                    if style != "default":
                        newResult.serversAlerted.append(row)
                    newResult.servers.append(row)

                for doyleFile in files:
                    style = "default"
                    age = datetime.datetime.now() - doyleFile.firstExecutionTime
                    if age.total_seconds() > doyleFile.expectedExecutionTime[2]:
                        style = "danger"
                        newResult.executingTestsAlert = True
                    elif age.total_seconds() > doyleFile.expectedExecutionTime[1]:
                        style = "warning"
                        newResult.executingTestsAlert = True
                    row = [
                        style,
                        "%s (%s)" % (self.ageToString(age), self.ageToString(datetime.timedelta(seconds=doyleFile.expectedExecutionTime[0]))),
                        (server, doyleFile.queue),
                        "#{0}".format(doyleFile.tfsbuildid) if doyleFile.tfsbuildid != 0 else "#----",
                        ("/".join([doyleFile.xbetree, doyleFile.xbegroup, doyleFile.xbeproject, "{0:04}".format(doyleFile.xbebuildid)]), doyleFile.file, "file:///u:/pgxbe/releases/" + "/".join([doyleFile.xbetree, doyleFile.xbegroup, doyleFile.xbeproject, "{0:04}".format(doyleFile.xbebuildid)]) + "/xbe_release.log",),
                        doyleFile.type,
                        doyleFile.target,
                    ]
                    newResult.executingTests.append(row)

            # check if we should switch on the blue light
            #            blueLightOn=0
            #            for server,files,dummy in self.serverFolder.items:
            #               for doyleFile in files:
            #                    age=datetime.datetime.now()-doyleFile.firstExecutionTime
            #                    if age.total_seconds() > doyleFile.expectedExecutionTime[2]:
            #                        blueLightOn=100
            #            xmlrpc.client.ServerProxy('http://10.0.60.57:8000').blue(blueLightOn)

            #            raise Exception("testing failure to update")

            # getQueued
            for queue, files, dummy in self.queueFolder.items:
                if len(files):
                    if queue.upper() in self.serverConfigs:
                        serverString = ",".join(self.serverConfigs[queue.upper()])
                    else:
                        serverString = "No servers listening on this queue !!"
                    for doyleFile in files:
                        age = datetime.datetime.now() - doyleFile.queuedTime
                        style = "default"
                        if age.total_seconds() > 2 * 24 * 3600:
                            style = "warning"
                            newResult.queuedTestsAlert = True
                        row = [
                            style,
                            self.ageToString(age),
                            (queue, serverString),
                            "#{0}".format(doyleFile.tfsbuildid) if doyleFile.tfsbuildid != 0 else "#----",
                            ("/".join([doyleFile.xbetree, doyleFile.xbegroup, doyleFile.xbeproject, "{0:04}".format(doyleFile.xbebuildid)]), doyleFile.file),
                            doyleFile.type,
                            doyleFile.target,
                        ]
                        newResult.queuedTests.append(row)

            # sort on tfsbuildid
            newResult.queuedTests = sorted(newResult.queuedTests, key=operator.itemgetter(3))

            # if we got here without exception, there is no error
            newResult.errorMsg = None

        except:
            print("Updating info failed with exception: %s" % traceback.format_exc())
            newResult.clear(traceback.format_exc())

        # replace current result with new result
        self.result.copyFrom(newResult)

        end = timer()
        print("Building info took %.4fs (hit %s / new %s / gone %s)" % ((end - start), self.cache.hitCount, self.cache.addCount, self.cache.removeCount))

    def getErrorMsg(self):
        """ Get the error message if an error has occured during processing, will return None when no error has occured. """
        with self.result.lock:
            return self.result.errorMsg

    def getExecution(self):
        """ Get information about the executing tests and the servers. """
        with self.result.lock:
            return self.result.executingTests

    def getQueued(self):
        """ Get information about the queued tests. """
        with self.result.lock:
            return self.result.queuedTests

    def getServers(self):
        """ Get information about all the servers. """
        with self.result.lock:
            return self.result.servers

    def getServersFailed(self):
        """ Get information about the servers that have something to report. """
        with self.result.lock:
            return self.result.serversAlerted

    def getCounts(self):
        """ Get the number of entries executing and the number of entries queued. """
        with self.result.lock:
            return {
                "executing": len(self.result.executingTests),
                "executingAlert": self.result.executingTestsAlert,
                "queued": len(self.result.queuedTests),
                "queuedAlert": self.result.queuedTestsAlert,
                "servers": len(self.result.servers),
                "serversAlert": len(self.result.serversAlerted) != 0,
                "serverRemarks": len(self.result.serversAlerted),
            }

    def getHistory(self, doyleServer):
        """ Get a list of what was excecuted on a given doyle server."""

        # get the history for the given server
        entries = self.doyleFileDb.getDoyleHistory(doyleServer, 100)

        # calculate how busy the server was during this period
        busyPercentage = 0
        if len(entries) > 1:
            busySeconds = 0
            totalSeconds = 0
            for e in entries:
                busySeconds = busySeconds + (e[6] - e[5]).total_seconds()
            totalSeconds = (entries[0][6] - entries[-1][5]).total_seconds()
            busyPercentage = (busySeconds * 100.0) / totalSeconds

        # prepare the list for the HTML template
        toDisplay = []
        for x in entries:
            toDisplay.append((x[5], self.ageToString(x[6] - x[5]), x[0], "\\".join([x[1], x[2], "{0:04}".format(x[3])]), x[4]))

        return {"history": toDisplay, "busyPercentage": busyPercentage}

    def startCleanDatabase(self):
        self.cleanDatabaseRequested = True

    def backupDatabase(self):
        self.backupDatabaseRequested = True