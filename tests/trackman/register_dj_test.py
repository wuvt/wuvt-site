#!/usr/bin/python3
#
# Script: register_dj.py
# Author: Emmet Hobgood (ehobgood)
#
# This script will test Trackman's ability to properly register a new DJ

import unittest as ut
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

class RegisterDJTestCase(ut.TestCase):
    driver = webdriver.Firefox()
    
    def setUp(self):
        # Go to the trackman homepage
        self.driver.get("http://localhost:9090/trackman")
        self.driver.find_element(By.PARTIAL_LINK_TEXT, "Register New DJ").click()
        
    def test_bad_input(self):
        driver = self.driver
        
        # Set up unvalidated inputs
        on_air = driver.find_element(By.ID, "id_airname")
        on_air.send_keys("DJ McTestface")
        
        real_name = driver.find_element(By.ID, "id_name")
        real_name.send_keys("Testy McTestface")
        
        genres = driver.find_element(By.ID, "id_genres")
        genres.send_keys("Experimental")
        
        # Invalid email address
        email = driver.find_element(By.ID, "id_email")
        email.send_keys("badEmail")
        email.submit()
        self.assertIn("DJ Registration", driver.title)
        help_text = driver.find_element(By.CLASS_NAME, "help-block")
        self.assertIsNotNone(help_text)
        self.assertEqual("Invalid email address.", help_text.text)
        
        email = driver.find_element(By.ID, "id_email")
        email.clear()
        email.send_keys("good_email@example.com")
        
        # Invalid phone number
        phone = driver.find_element(By.ID, "id_phone")
        phone.send_keys("short")
        phone.submit()
        self.assertIn("DJ Registration", driver.title)
        help_text = driver.find_element(By.CLASS_NAME, "help-block")
        self.assertIsNotNone(help_text)
        self.assertEquals("Field must be between 10 and 12 characters long.", help_text.text)
        # TODO test bad phone number
        
    def test_data_required(self):
        driver = self.driver
        on_air = driver.find_element(By.ID, "id_airname")
        real_name = driver.find_element(By.ID, "id_name")
        email = driver.find_element(By.ID, "id_email")
        phone = driver.find_element(By.ID, "id_phone")
        genres = driver.find_element(By.ID, "id_genres")
        
        on_air.send_keys("Test McTestface")
        on_air.submit()
        curr = driver.switch_to_active_element()
        
        print(curr)
        print(real_name)
        self.assertEqual(curr, real_name)

    def test_trackman_register_dj(self):
        driver = self.driver
        
    def tearDown(self):
        pass
        
    @classmethod
    def tearDownClass(self):
        pass
        
if __name__ == "__main__":
    ut.main()