from app import doylefolder
from app import doylefile

import os
import tempfile

class mocked_cache:
    def __init__(self):
        self.getCount = 0
        self.addCount = 0

    def getDoyleFile(self, file):
        self.getCount = self.getCount + 1
        return None

    def addDoyleFile(self, file, doyleFile):
        self.addCount = self.addCount + 1


class mocked_db:
    def __init__(self):
        self.loadCount = 0
        self.addCount = 0

    def loadFile(self, file):
        self.loadCount = self.loadCount + 1
        return None

    def addFile(self, file):
        self.addCount = self.addCount + 1


class TestDoyleFolder:
    def setup(self):
        # create a root folder with 5 sub folders and 3 testfiles each
        self.tempRootDir = tempfile.TemporaryDirectory()
        self.tempChildDirs = []
        for _ in range(5):
            self.tempChildDirs.append(tempfile.TemporaryDirectory(dir=self.tempRootDir.name))
            for i in range(3):
                with open(os.path.join(self.tempChildDirs[-1].name,f"testfile-{i}.sh"),"wt") as f:
                    f.write('export XBEHOME="u:/pgxbe/releases/B999/InstallersDoyle/Kourou/42"\n')
                    f.write(f'# TargetName: TestCase{i*100}\n')
                    f.write(f'export tfsbuildid="12345"\n')
                    f.write('# ScriptFile: testfile;A.sh\n')
        self.d = doylefolder.DoyleFolder(doylefolder.DoyleFolderType.queueFolder, self.tempRootDir.name)
        doylefile.DoyleFile.doyleFileDb = mocked_db()

    def teardown(self):
        for td in self.tempChildDirs:
            td.cleanup()
        self.tempRootDir.cleanup()

    def test_init(self):
        assert len(self.d.items) == 0
        assert self.d.count == 0

    def test_update(self):
        m = mocked_cache()
        self.d.update(m)
        assert len(self.d.items) == 5
        assert self.d.count == 15
        assert m.getCount == 15
