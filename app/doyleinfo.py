import datetime
import operator
import os
import sys
import threading
import time
import traceback

# for measuring how long execution takes
from timeit import default_timer as timer

from app.doylefilecache import DoyleFileCache
from app.doylefolder import DoyleFolder, DoyleFolderType
from app.doylefiledb import DoyleFileDb
from app.doylefile import DoyleFile

serverBlackList = ['DOYLE-CORDOVA', 'VM-DOYLE-YUI']

doyleBasePaths = ['/mnt/udrive/Doyle', r'U:\Doyle', '']


class DoyleResult:

    def __init__(self):
        self.lock = threading.Lock()
        self.clear('The information is still being gathered.')

    def clear(self, message):
        self.errorMsg = message
        self.servers = []
        self.serversAlerted = []
        self.executingTests = []
        self.executingTestsAlert = False
        self.queuedTests = []
        self.queuedTestsAlert = False

    def copyFrom(self, newResult):
        with self.lock:
            self.errorMsg = newResult.errorMsg
            self.servers = newResult.servers[:]
            self.serversAlerted = newResult.serversAlerted[:]
            self.executingTests = newResult.executingTests[:]
            self.executingTestsAlert = newResult.executingTestsAlert
            self.queuedTests = newResult.queuedTests[:]
            self.queuedTestsAlert = newResult.queuedTestsAlert


class DoyleInfo(threading.Thread):
    ''' Main class that keeps and updates test info for queues and servers.'''

    def __init__(self):
        # determine where to look: either u:\doyle or /mnt/udrive/doyle
        for doyleBasePath in doyleBasePaths:
            if os.path.isdir(doyleBasePath):
                print('Getting doyle info from %s' % doyleBasePath)
                self.queuesPath = os.path.join(doyleBasePath, 'TestQueues')
                self.serversPath = os.path.join(doyleBasePath, 'TestServers')
                break
        if not os.path.isdir(doyleBasePath):
            sys.exit('cannot access TestQueues and TestServers!')

        self.cache = DoyleFileCache()
        self.queueFolder = DoyleFolder(DoyleFolderType.queueFolder, self.queuesPath)
        self.serverFolder = DoyleFolder(DoyleFolderType.serverFolder, self.serversPath)

        self.result = DoyleResult()
        self._clean()

        # create database and pass it (as a static) to DoyleFile
        self.doyleFileDb = DoyleFileDb()
        DoyleFile.doyleFileDb = self.doyleFileDb

        threading.Thread.__init__(self)
        self.start()

    def run(self):
        while True:
            self._update()
            time.sleep(50)

    def _clean(self):
        self.serverConfigs = []
        self.serversForAllQueues = []
        self.cache.resetUsedCount()

    def ageToString(self, age):
        if age.days > 0:
            ageString = '%sd' % age.days
        elif age.seconds > 3600:
            ageString = '{0:.1f}h'.format(age.seconds / 3600)
        elif age.seconds > 60:
            ageString = '%sm' % int(age.seconds / 60)
        else:
            ageString = '%ss' % age.seconds
        return ageString

    def getServerConfigs(self, baseDir):
        start = timer()

        resultDict = {}
        for f in os.listdir(baseDir):
            if os.path.splitext(f)[1].lower() == '.cfg':
                serverName = os.path.splitext(f)[0].upper()
                for line in open(os.path.join(baseDir, f)):
                    queueName = line.strip(' \n').split('\\')[-1].upper()
                    if queueName in resultDict:
                        resultDict[queueName].append(serverName)
                    else:
                        resultDict[queueName] = [serverName]

        end = timer()
        print('Getting %s server configs took  %.4fs' % (len(resultDict), (end - start)))

        return resultDict

    def _update(self):
        ''' Re-read queue and server folders and build a new result.'''
        start = timer()
        try:
            self._clean()
            newResult = DoyleResult()

            self.queueFolder.update(self.cache)
            self.serverFolder.update(self.cache)
            self.cache.removeUnusedEntries()

            self.serverConfigs = self.getServerConfigs(self.serversPath)

            # build a list of servers that should be handling the queues
            for queue, files, dummy in self.queueFolder.items:
                if len(files):
                    if queue.upper() in self.serverConfigs:
                        self.serversForAllQueues.extend(self.serverConfigs[queue.upper()])
            self.serversForAllQueues = list(set(self.serversForAllQueues))

            # compile two lists with servers to report: the first list has all the servers, the second has only the servers that have non-default style
            # compile a list with all executing tests
            for server, files, upgradePending in self.serverFolder.items:
                # should we display info about this server
                serverMessages = []
                style = 'default'

                # there are files executing on this server
                if len(files) > 0:
                    serverMessages.append('Executing')

                # server has an upgrade pending
                if upgradePending == True:
                    serverMessages.append('Server has an upgrade pending')
                    style = 'warning'

                # server should be busy but is not
                if len(files) == 0 and server in self.serversForAllQueues:
                    serverMessages.append('Server should be busy but is not')
                    style = 'danger'

                # check if doyle server is active
                doyleServerAge = '---'
                if server not in serverBlackList:
                    aliveFile = os.path.join(self.serversPath, server, 'alive.dat')
                    if os.path.isfile(aliveFile):
                        age = datetime.datetime.now() - datetime.datetime.fromtimestamp(os.path.getmtime(aliveFile))
                        if age > datetime.timedelta(minutes=5):
                            doyleServerAge = self.ageToString(age)
                            serverMessages.append('DoyleServer Not Running')
                            style = 'danger'
                    else:
                        serverMessages.append('DoyleServer status unknown')

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
                    row = [style, doyleServerAge, server, ', '.join(serverMessages)]
                    if style != 'default':
                        newResult.serversAlerted.append(row)
                    newResult.servers.append(row)

                for doyleFile in files:
                    style = 'default'
                    age = datetime.datetime.now() - doyleFile.firstExecutionTime
                    if age.total_seconds() > doyleFile.expectedExecutionTime[2]:
                        style = 'danger'
                        newResult.executingTestsAlert = True
                    elif age.total_seconds() > doyleFile.expectedExecutionTime[1]:
                        style = 'warning'
                        newResult.executingTestsAlert = True
                    row = [style,
                           '%s (%s)' % (self.ageToString(age), self.ageToString(
                               datetime.timedelta(seconds=doyleFile.expectedExecutionTime[0]))),
                           server,
                           '#{0}'.format(doyleFile.tfsbuildid) if doyleFile.tfsbuildid != 0 else '#----',
                           ('/'.join([doyleFile.xbetree, doyleFile.xbegroup, doyleFile.xbeproject, '{0:04}'.format(doyleFile.xbebuildid)]),
                            doyleFile.file,
                            'file:///u:/pgxbe/releases/' + '/'.join([doyleFile.xbetree, doyleFile.xbegroup, doyleFile.xbeproject,
                                                                     '{0:04}'.format(doyleFile.xbebuildid)]) + '/xbe_release.log'),
                           doyleFile.type,
                           doyleFile.target]
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
                        serverString = ','.join(self.serverConfigs[queue.upper()])
                    else:
                        serverString = 'No servers listening on this queue !!'
                    for doyleFile in files:
                        age = datetime.datetime.now() - doyleFile.queuedTime
                        style = 'default'
                        if age.total_seconds() > 2 * 24 * 3600:
                            style = 'warning'
                            newResult.queuedTestsAlert = True
                        row = [style, self.ageToString(age),
                               (queue, serverString),
                               '#{0}'.format(doyleFile.tfsbuildid) if doyleFile.tfsbuildid != 0 else '#----',
                               ('/'.join([doyleFile.xbetree, doyleFile.xbegroup, doyleFile.xbeproject,
                                          '{0:04}'.format(doyleFile.xbebuildid)]), doyleFile.file),
                               doyleFile.type,
                               doyleFile.target]
                        newResult.queuedTests.append(row)

            # sort on tfsbuildid
            newResult.queuedTests = sorted(newResult.queuedTests, key=operator.itemgetter(3))

            # if we got here without exception, there is no error
            newResult.errorMsg = None

        except:
            print('Updating info failed with exception: %s' % traceback.format_exc())
            newResult.clear(traceback.format_exc())

        # replace current result with new result
        self.result.copyFrom(newResult)

        end = timer()
        print('Building info took %.4fs (hit %s / new %s / gone %s)' %
              ((end - start), self.cache.hitCount, self.cache.addCount, self.cache.removeCount))

    def getErrorMsg(self):
        ''' Get the error message if an error has occured during processing, will return None when no error has occured. '''
        with self.result.lock:
            return self.result.errorMsg

    def getExecution(self):
        ''' Get information about the executing tests and the servers. '''
        with self.result.lock:
            return self.result.executingTests

    def getQueued(self):
        ''' Get information about the queued tests. '''
        with self.result.lock:
            return self.result.queuedTests

    def getServers(self):
        ''' Get information about all the servers. '''
        with self.result.lock:
            return self.result.servers

    def getServersFailed(self):
        ''' Get information about the servers that have something to report. '''
        with self.result.lock:
            return self.result.serversAlerted

    def getCounts(self):
        ''' Get the number of entries executing and the number of entries queued. '''
        with self.result.lock:
            return {'executing': len(self.result.executingTests), 'executingAlert': self.result.executingTestsAlert,
                    'queued': len(self.result.queuedTests), 'queuedAlert': self.result.queuedTestsAlert,
                    'servers': len(self.result.servers), 'serversAlert': len(self.result.serversAlerted) != 0}

    def getHistory(self, doyleServer):
        ''' Get a list of what was excecuted on a given doyle server.'''

        # get the history for the given server
        entries = self.doyleFileDb.getDoyleHistory(doyleServer)

        # prepare the list for the HTML template
        toDisplay = []
        for x in entries:
            toDisplay.append((x[5], self.ageToString(x[6] - x[5]), x[0], '\\'.join([x[1], x[2], str(x[3])]), x[4]))

        return {'history': toDisplay}
