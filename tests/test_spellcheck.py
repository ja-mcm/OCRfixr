#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Dec  4 14:25:59 2020

@author: jack
"""
import unittest
from ocrfixr import spellcheck

class TestStringMethods(unittest.TestCase):
    
    def test_returns_orig_text_if_no_errors(self):
        self.assertEqual(spellcheck("this text has no issues").replace(), "this text has no issues")


    def test_finds_easy_errors(self):
        self.assertEqual(spellcheck("cut the shiit").replace(), "cut the shit")
        self.assertEqual(spellcheck("The birds flevv south").replace(), "The birds flew south")

    def test_keeps_trailing_punctuation(self):
        self.assertEqual(spellcheck("Days there were when small trade came to the stoie. Then the young clerk read.").replace(), "Days there were when small trade came to the store. Then the young clerk read.")


    def test_handles_empty_text(self):
        self.assertEqual(spellcheck("").replace(), "")


#    def test_spellcheck_speed_acceptable(self):
    
    
    

if __name__ == '__main__':
    unittest.main()