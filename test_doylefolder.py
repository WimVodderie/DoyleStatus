import unittest
from app import doylefolder

class mocked_cache:
    def getDoyleFile(subdir,file):
        pass

class TestDoyleFolder(unittest.TestCase):

    def setUp(self):
        self.d = doylefolder.DoyleFolder(doylefolder.DoyleFolderType.queueFolder,'./tests/doylefolder/')

    def test_init(self):
        self.assertEqual(len(self.d.items),0)
        self.assertEqual(self.d.count,0)

    def test_update(self):
        self.d.update(mocked_cache)
        self.assertEqual(len(self.d.items),0)
        self.assertEqual(self.d.count,0)


if __name__ == '__main__':
    unittest.main()