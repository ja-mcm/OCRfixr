#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Dec  4 14:25:59 2020

@author: jack
"""
import unittest
import time
from ocrfixr import spellcheck

# Define timing function
def time_func(func, *args): #*args can take 0 or more 
  start_time = time.time()
  func(*args)
  end_time = time.time()
  return(end_time-start_time)

def sc(text):
    return(spellcheck(text).replace())

class TestStringMethods(unittest.TestCase):
    
    def test_finds_misreads(self):
        self.assertEqual(spellcheck("Hello, I'm a maile model.")._LIST_MISREADS(), ['maile'])
        self.assertEqual(spellcheck("'I'm not sure', Adam said. 'I can't see it. The wind-n\ow is half-shut.'")._LIST_MISREADS(), [])
    
    
    def test_ignore_words(self):
       self.assertEqual(spellcheck("I don't understand your aceent", ignore_words = ['aceent'])._LIST_MISREADS(), [])
       self.assertEqual(spellcheck("I don't understand your aceent")._LIST_MISREADS(), ['aceent'])

    
    def test_returns_orig_text_if_no_errors(self):
        self.assertEqual(spellcheck("this text has no issues").replace(), "this text has no issues")


    def test_finds_easy_errors(self):
        self.assertEqual(spellcheck("cut the shiit").replace(), "cut the shit")
        self.assertEqual(spellcheck("The birds flevv south").replace(), "The birds flew south")


    def test_keeps_trailing_punctuation(self):
        self.assertEqual(spellcheck("Days there were when small trade came to the stoie. Then the young clerk read.").replace(), "Days there were when small trade came to the store. Then the young clerk read.")


    def test_handles_empty_text(self):
        self.assertEqual(spellcheck("").replace(), "")


    def test_retains_paragraphs(self):
        self.assertEqual(spellcheck("The birds flevv down\n south").replace(), "The birds flew down\n south")
        self.assertEqual(spellcheck("The birds flevv down\n\n south").replace(), "The birds flew down\n\n south")   
        self.assertEqual(spellcheck("The birds\n flevv down south").replace(), "The birds\n flevv down south")         # context is paragraph-specific, so OCRfixr doesn't see "birds" as relevant. This is designed behavior.


    def test_return_fixes_flag(self):
        self.assertEqual(spellcheck("The birds flevv down\n south",return_fixes = "T").replace(), ["The birds flew down\n south",{"flevv":"flew"}])
        self.assertEqual(spellcheck("The birds flevv down\n south and were quikly apprehended",return_fixes = "T").replace(), ["The birds flew down\n south and were quickly apprehended",{"flevv":"flew", "quikly":"quickly"}])


    def test_spellcheck_contains_uppercase(self):
        self.assertEqual(spellcheck("He falls ilL.").replace(), "He falls ill.")


    def test_spellcheck_speed_acceptable(self):
        # GOALS
        # 0 misspells = < 0.01 seconds
        # 1 misspell = < 0.10 seconds
        # additional misspells "cost" the same amount of time (ie. execution scales linearly)
        self.assertLessEqual(time_func(sc,"this text has no issues"), 0.01)
        self.assertLessEqual(time_func(sc,"He falls ilL."), 0.2) 
        self.assertLessEqual(time_func(sc,"I am sure yov will f1nd all the rnistakes in this sentence"), 1)


# TODO

# MASHUPS
# This one currently fails - OCRfixr sometimes mis-handles mashed up words
#    def test_fixes_mashed_words(self):
#       self.assertEqual(spellcheck("It seemed a long time as we sat there in the darkness waiting for the train; but it was perhaps, in fact, less than half anhour.").replace(), "It seemed a long time as we sat there in the darkness waiting for the train; but it was perhaps, in fact, less than half an hour.")

# EXTRA SPACES
# This one currently fails - OCRfixr doesn't see the relevant character due to the extra space, and duplicates it
#    def test_fixes_extra_spaces(self):
#       self.assertEqual(spellcheck("But suppose I spare your lif e--will you help me to escape?").replace(), "But suppose I spare your life--will you help me to escape?")





if __name__ == '__main__':
    unittest.main()