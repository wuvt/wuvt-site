import unittest

def suite():
    test_suite = unittest.TestSuite()
    test_suite.addTest(unittest.makeSuite(register_dj.RegisterDJTestCase))
    return test_suite
    
mySuite = suite()
runner = unittest.TextTestRunner()
runner.run(mySuite)