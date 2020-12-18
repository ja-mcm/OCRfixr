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


    def test_reunites_paragraphs(self):
        self.assertEqual(spellcheck("The birds flevv down\n south").replace(), "The birds flew down\n south")
        self.assertEqual(spellcheck("The birds flevv down\n\n south").replace(), "The birds flew down\n\n south")        


# Need to test for reasonable runtime across a variety of inputs
#    def test_spellcheck_speed_acceptable(self):
#       TODO: 1 change = < 0.10 seconds
#       TODO: >1 change = < 0.25 seconds
#       TODO: 1 paragraph = 1 second

# MASHUPS - TODO
# This one currently fails - OCRfixr does not know how to handle mashed up words
#    def test_fixes_mashed_words(self):
#       self.assertEqual(spellcheck(spellcheck("John O'Dell was very polite and cold as ice and dry assand.").replace(), "John O'Dell was very polite and cold as ice and dry as sand.")
#       self.assertEqual(spellcheck(spellcheck("It seemed a long time as we sat there in the darkness waiting for the train; but it was perhaps, in fact, less than half anhour.").replace(), "It seemed a long time as we sat there in the darkness waiting for the train; but it was perhaps, in fact, less than half an hour.")
     

# UPPERCASE - TODO
# This one currently fails - OCRfixr does not know how to handle uppercase letters in misspellings (due to quirk in pyspellcheck's spell.unknown) 
#    def test_spellcheck_uppercase(self):
#       self.assertEqual(spellcheck(spellcheck("Others attach the frogs, whole, to the exterior of the jaws:29 and with some it is the practice to boil ten frogs, in three sextarii of vinegar, down to one-third, and to use the decoction as a streDgthener of loose teeth.)").replace(), "Others attach the frogs, whole, to the exterior of the jaws:29 and with some it is the practice to boil ten frogs, in three sextarii of vinegar, down to one-third, and to use the decoction as a strengthener of loose teeth.)")




if __name__ == '__main__':
    unittest.main()