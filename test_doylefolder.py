from app import doylefolder


class mocked_cache:
    def getDoyleFile(subdir, file):
        pass


class TestDoyleFolder:

    def test_init(self):
        d = doylefolder.DoyleFolder(doylefolder.DoyleFolderType.queueFolder, "./tests/doylefolder/")
        assert len(d.items) == 0
        assert d.count == 0

    def test_update(self):
        d = doylefolder.DoyleFolder(doylefolder.DoyleFolderType.queueFolder, "./tests/doylefolder/")
        d.update(mocked_cache)
        assert len(d.items) == 0
        assert d.count == 0
