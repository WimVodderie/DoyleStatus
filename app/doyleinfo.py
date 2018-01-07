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
        self.lock = threading.Lock()
        self.queueFolder = DoyleFolder(DoyleFolderType.queueFolder, self.queuesPath)
        self.serverFolder = DoyleFolder(DoyleFolderType.serverFolder, self.serversPath)
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
        self.doyleServerAges = {}
        self.serversForAllQueues = []
        self.serverReport = []
        self.dataException = None
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
        try:
            self.lock.acquire()
            start = timer()

            self._clean()

            self.queueFolder.update(self.cache)
            self.serverFolder.update(self.cache)

            self.cache.removeUnusedEntries()

            self.serverConfigs = self.getServerConfigs(self.serversPath)

            # find out which doyleservers are still running
            for server, files, dummy in self.serverFolder.items:
                aliveFile = os.path.join(self.serversPath, server, 'alive.dat')
                if os.path.isfile(aliveFile):
                    age = datetime.datetime.now() - datetime.datetime.fromtimestamp(os.path.getmtime(aliveFile))
                    self.doyleServerAges[server] = age

            # build a list of servers that should be handling the queues
            for queue, files, dummy in self.queueFolder.items:
                if len(files):
                    if queue.upper() in self.serverConfigs:
                        self.serversForAllQueues.extend(self.serverConfigs[queue.upper()])
            self.serversForAllQueues = list(set(self.serversForAllQueues))

            # compile a list of servers to report
            for server, files, upgradePending in self.serverFolder.items:
                # should we display info about this server
                serverMessages = []
                lineColor = 'color:Black'

                # there are files executing on this server
        #        if len(files)>0:
        #            serverMessages.append('Executing')
                # server has an upgrade pending
                if upgradePending == True:
                    serverMessages.append('Server has an upgrade pending')
                    lineColor = 'color:Orange'

                # server should be busy but is not
                if len(files) == 0 and server in self.serversForAllQueues:
                    serverMessages.append('Server should be busy but is not')
                    lineColor = 'color:Red'

                # check if doyle server is active
                doyleServerAge = '---'
                if server not in serverBlackList:
                    if server not in self.doyleServerAges:
                        serverMessages.append('DoyleServer status unknown')
                    else:
                        age = self.doyleServerAges[server]
                        if age > datetime.timedelta(minutes=5):
                            doyleServerAge = self.ageToString(age)
                            serverMessages.append('DoyleServer Not Running')
                            lineColor = 'color:Red'

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
        #                lineColor='color:Red'

                if len(serverMessages) > 0:
                    self.serverReport.append((doyleServerAge, server, serverMessages, lineColor))

            # check if we should switch on the blue light
#            blueLightOn=0
#            for server,files,dummy in self.serverFolder.items:
#               for doyleFile in files:
#                    age=datetime.datetime.now()-doyleFile.firstExecutionTime
#                    if age.total_seconds() > doyleFile.expectedExecutionTime[2]:
#                        blueLightOn=100
#            xmlrpc.client.ServerProxy('http://10.0.60.57:8000').blue(blueLightOn)

#            raise Exception("testing failure to update")

            end = timer()
            print('Gathering info took %.4fs (hit %s / new %s / gone %s)' %
                  ((end - start), self.cache.hitCount, self.cache.addCount, self.cache.removeCount))

        except:
            print('Gathering info failed with exception: %s' % traceback.format_exc())
            self.dataException = traceback.format_exc()

        finally:
            self.lock.release()

    def getExecution(self):
        ''' Get information about the executing tests and the servers. '''

        errorMsg = None
        rowsExe = []
        rowsServer = []

        try:
            self.lock.acquire()

            if self.dataException == None:
                for server, files, dummy in self.serverFolder.items:
                    for doyleFile in files:
                        age = datetime.datetime.now() - doyleFile.firstExecutionTime
                        style = 'color:Black' if age.total_seconds() < doyleFile.expectedExecutionTime[1] else 'color:Orange' if age.total_seconds() < doyleFile.expectedExecutionTime[2] else 'color:Red'
                        row = [style,
                            '%s (%s)' % (self.ageToString(age), self.ageToString(datetime.timedelta(seconds=doyleFile.expectedExecutionTime[0]))),
                            server,
                            '#{0}'.format(doyleFile.tfsbuildid) if doyleFile.tfsbuildid != 0 else '#----',
                            ('/'.join([doyleFile.xbetree, doyleFile.xbegroup, doyleFile.xbeproject, '{0:04}'.format(doyleFile.xbebuildid)]), doyleFile.file,
                            'file:///u:/pgxbe/releases/' + '/'.join([doyleFile.xbetree, doyleFile.xbegroup, doyleFile.xbeproject, '{0:04}'.format(doyleFile.xbebuildid)]) + '/xbe_release.log'),
                            doyleFile.type,
                            doyleFile.target]
                        rowsExe.append(row)

                for item in self.serverReport:
                    style = item[3]
                    row = [item[3], item[0], item[1], ', '.join(item[2])]
                    rowsServer.append(row)
            else:
                errorMsg=self.dataException

        except:
            print('Gathering execution information failed with exception: %s' % traceback.format_exc())
            errorMsg = 'Gathering execution information failed with exception: %s' % traceback.format_exc()

        finally:
            self.lock.release()

        return {'errorMsg': errorMsg, 'exes': rowsExe, 'servers': rowsServer}

    def getQueued(self):
        ''' Get information about the queued tests. '''

        errorMsg = None
        rowsQueued = []

        try:
            self.lock.acquire()

            if self.dataException == None:
                for queue, files, dummy in self.queueFolder.items:
                    if len(files):
                        if queue.upper() in self.serverConfigs:
                            serverString = ','.join(self.serverConfigs[queue.upper()])
                        else:
                            serverString = 'No servers listening on this queue !!'

                        for doyleFile in files:
                            age = datetime.datetime.now() - doyleFile.queuedTime
                            style = 'color:Black' if age.total_seconds() < 2 * 24 * 3600 else 'color:Red'
                            row = [style,self.ageToString(age),
                                   (queue, serverString),
                                   '#{0}'.format(doyleFile.tfsbuildid) if doyleFile.tfsbuildid != 0 else '#----',
                                   ('/'.join([doyleFile.xbetree, doyleFile.xbegroup, doyleFile.xbeproject,
                                              '{0:04}'.format(doyleFile.xbebuildid)]), doyleFile.file),
                                   doyleFile.type,
                                   doyleFile.target]
                            rowsQueued.append(row)

                # sort on tfsbuildid
                rowsQueued = sorted(rowsQueued, key=operator.itemgetter(3))

            else:
                errorMsg = self.dataException

        except:
            print('Gathering queue information failed with exception: %s' % traceback.format_exc())
            errorMsg = 'Gathering queue information failed with exception: %s' % traceback.format_exc()

        finally:
            self.lock.release()

        return {'errorMsg': errorMsg, 'queues': rowsQueued}

    def getCounts(self):
        ''' Get the number of entries executing and the number of entries queued. '''

        executing = '?'
        queued = '?'

        try:
            self.lock.acquire()
            if self.dataException == None:
                executing = self.serverFolder.count
                queued = self.queueFolder.count

        except:
            print('Getting counts failed with exception: %s' % traceback.format_exc())

        finally:
            self.lock.release()

        return {'executing': self.serverFolder.count, 'queued': self.queueFolder.count}

    def getHistory(self, doyleServer):
        ''' Get a list of what was excecuted on a given doyleServer.'''

        entriesSorted = self.doyleFileDb.getDoyleHistory(doyleServer)

        # prepare the list for the HTML template
        toDisplay = []
        for x in entriesSorted:
            toDisplay.append((x[5], self.ageToString(x[6] - x[5]), x[0], '\\'.join([x[1], x[2], str(x[3])]), x[4]))

        return {'history': toDisplay}
