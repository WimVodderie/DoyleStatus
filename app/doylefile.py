import datetime
import os

from app import doylefiledb


class DoyleFile:
    ''' This class tracks all the info about a doyle test. Part of it is kept/loaded from the database, part is updated.'''

    # 'static' database connection
    doyleFileDb = None

    def __init__(self, path, file):
        self.path = path
        self.file = file
        self.filePath = os.path.join(self.path, self.file)
        self.target = ''
        self.type = '-'
        self.server = ''
        self.queue = ''
        self.xbetree = ''
        self.xbegroup = ''
        self.xbeproject = ''
        self.xbebuildid = 0
        self.tfsbuildid = 0

        self.queuedTime = None
        self.firstExecutionTime = None
        self.lastExecutionTime = None

        self.expectedExecutionTime = None

    def dump(self):
        print('path       %s' % self.path)
        print('file       %s' % self.file)
        print('filePath   %s' % self.filePath)
        print('target     %s' % self.target)
        print('type       %s' % self.type)
        print('server     %s' % self.server)
        print('queue      %s' % self.queue)
        print('xbetree    %s' % self.xbetree)
        print('xbegroup   %s' % self.xbegroup)
        print('xbeproject %s' % self.xbeproject)
        print('xbebuildid %s' % self.xbebuildid)
        print('tfsbuildid %s' % self.tfsbuildid)
        print('queued     %s' % self.queuedTime)
        print('first exec %s' % self.firstExecutionTime)
        print('last exec  %s' % self.lastExecutionTime)

    def load(self):
        # try to load from the database
        if DoyleFile.doyleFileDb.loadFile(self) == False:
            # not in the db yet, load from file and add to the database
            self._loadFromFile()
            DoyleFile.doyleFileDb.addFile(self)
        # update queued time (even if we got it from the database)
        self.queuedTime = datetime.datetime.fromtimestamp(os.path.getmtime(self.filePath))
        self.queue = os.path.split(self.path)[-1]

    def _loadFromFile(self):
        for line in open(self.filePath):
            if line.startswith('export XBEHOME='):
                xbeHomeParts = str.replace(line[16:-2], '\\\\', '/').split('/')
                if len(xbeHomeParts) == 4:
                    # test refers to W drive
                    self.xbetree = xbeHomeParts[1]
                    self.xbegroup = xbeHomeParts[2]
                    self.xbeproject = xbeHomeParts[3]
                    self.xbebuildid = 0
                else:
                    # test refers to U drive
                    self.xbetree = xbeHomeParts[3]
                    self.xbegroup = xbeHomeParts[4]
                    self.xbeproject = xbeHomeParts[5]
                    self.xbebuildid = int(xbeHomeParts[6])
            if line.startswith('typeset DOYLETARGET'):
                self.target = line[21:-2]
            if line.startswith('# TargetName: '):
                self.target = line[14:-1]
            if line.startswith('export tfsbuildid='):
                self.tfsbuildid = int(line[19:-2])
            if line.startswith('# ScriptFile:'):
                self.type = line.split(';')[-1][0]
        print('%s: loaded from file (%s)' % (self.file, str.join(
            '/', [self.xbetree, self.xbegroup, self.xbeproject, str(self.xbebuildid)])))

    def update(self, path):  # do not use self.path because is probably the path the test was queued to
        if self.firstExecutionTime == None:
            self.firstExecutionTime = datetime.datetime.fromtimestamp(os.path.getmtime(path))
        self.lastExecutionTime = datetime.datetime.now()
        if self.expectedExecutionTime == None:
            self.expectedExecutionTime = DoyleFile.doyleFileDb.getExpectedExecutionTime(self)
        self.server = os.path.split(path)[-1]
        print('%s: updated (exec time %s -> %s @ %s)' % (self.file, self.firstExecutionTime, self.lastExecutionTime, self.server))

    def save(self):
        # update db
        DoyleFile.doyleFileDb.updateFile(self)
