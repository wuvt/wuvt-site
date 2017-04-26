#!/usr/bin/python3
#
# Script: log_track_test.py
# Author: Emmet Hobgood (ehobgood)
#
# This script will test Trackman's ability to log tracks

import unittest as ut
from selenium import webdriver
from selenium.webdriver.common.by import By

class LogTrackTestCase(ut.TestCase):
    driver = webdriver.Firefox()
    
    def setUp(self):
        self.driver.get("http://localhost:9090/trackman")
        
    def tearDown(self):
        pass
        
    @classmethod
    def tearDownClass(self):
        pass
        
if __name__ == "__main__":
    ut.main()