import unittest
from film20.account.signup_tests import SignupTestCase

def suite():
    suite = unittest.TestSuite()
    suite.addTest(SignupTestCase('test_signup_all_valid'))
    suite.addTest(SignupTestCase('test_signup_wrong_answer'))
    suite.addTest(SignupTestCase('test_signup_email_validation'))
    return suite
