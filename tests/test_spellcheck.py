#!/usr/bin/env python3
# -*- coding: utf-8 -*-

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
    return(spellcheck(text).fix())



class TestStringMethods(unittest.TestCase):
    
    def test_finds_misreads(self):
        self.assertEqual(spellcheck("Hello, I'm a maile model.")._LIST_MISREADS(), ['maile'])
        self.assertEqual(spellcheck("'I'm not sure', Adam said. 'I can't see it. The wind-n\ow is half-shut.'")._LIST_MISREADS(), [])
        self.assertEqual(spellcheck("income which represented the capital.1 And the")._LIST_MISREADS(), [])
        self.assertEqual(spellcheck("the nature both of the plan and purpose of his work8.")._LIST_MISREADS(), [])
        self.assertEqual(spellcheck("iron, &c. As I could not detect")._LIST_MISREADS(), [])
        self.assertEqual(spellcheck("571. (16) If lighted by a spiritual sun")._LIST_MISREADS(), [])
        self.assertEqual(spellcheck("been, that it violates certain axioms above stated, (18,) which have been")._LIST_MISREADS(), [])
        self.assertEqual(spellcheck("been, that it violates certain axioms above stated, (ee) which have been")._LIST_MISREADS(), [])
        self.assertEqual(spellcheck('333.   “The Journal du Magnetisme of the 10th of March, 1853, had')._LIST_MISREADS(), [])


    def test_ignore_words(self):
       self.assertEqual(spellcheck("I don't understand your aceent", ignore_words = ['aceent'])._LIST_MISREADS(), [])
       self.assertEqual(spellcheck("I don't understand your aceent")._LIST_MISREADS(), ['aceent'])

    
    def test_returns_orig_text_if_no_errors(self):
        self.assertEqual(spellcheck("this text has no issues").fix(), "this text has no issues")


    def test_finds_easy_errors(self):
        self.assertEqual(spellcheck("cut the shiit").fix(), "cut the shit")
        self.assertEqual(spellcheck("The birds flevv south").fix(), "The birds flew south")


    def test_keeps_trailing_punctuation(self):
        self.assertEqual(spellcheck("Days there were when small trade came to the stoie. Then the young clerk read.").fix(), "Days there were when small trade came to the store. Then the young clerk read.")


    def test_handles_empty_text(self):
        self.assertEqual(spellcheck("").fix(), "")
        
        
    def test_common_scannos(self):
        self.assertEqual(spellcheck("tle").fix(), "the")
        self.assertEqual(spellcheck("Tlie").fix(), "The")
        self.assertEqual(spellcheck("the context makes no sense to help iito fix this scanno").fix(), "the context makes no sense to help into fix this scanno")


    def test_stealth_scannos(self):
        self.assertEqual(spellcheck("the fox arid the hound ran round and round", common_scannos = "T").fix(), "the fox and the hound ran round and round")
        #self.assertEqual(spellcheck("then be went to the store to buy some bread", common_scannos = "T").fix(), "then he went to the store to buy some bread")


    def test_retains_paragraphs(self):
        self.assertEqual(spellcheck("The birds flevv down\n south").fix(), "The birds flew down\n south")
        self.assertEqual(spellcheck("The birds flevv down\n\n south").fix(), "The birds flew down\n\n south")   
        self.assertEqual(spellcheck("The birds\n flevv down south").fix(), "The birds\n flevv down south")         # context is paragraph-specific, so OCRfixr doesn't see "birds" as relevant. This is designed behavior.


    def test_return_fixes_flag(self):
        self.assertEqual(spellcheck("The birds flevv down\n south",return_fixes = "T").fix(), ["The birds flew down\n south",{("flevv","flew"):1}])
        self.assertEqual(spellcheck("The birds flevv down\n south and were quikly apprehended",return_fixes = "T").fix(), ["The birds flew down\n south and were quickly apprehended",{("flevv","flew"):1, ("quikly","quickly"):1}])


    def test_changes_by_paragraph_flag(self):
        self.assertEqual(spellcheck("The birds flevv down\n south, bvt wefe quickly apprehended\n by border patrol agents", changes_by_paragraph = "T").fix(), [["The birds flew down\n",{"flevv":"flew"}], [" south, but were quickly apprehended\n", {"bvt":"but", "wefe":"were"}]])
        # Case - no misspells in the text
        self.assertEqual(spellcheck("by border patrol agents", changes_by_paragraph = "T").fix(), "NOTE: No changes made to text")
        # Case - misspell in the text, but no replacement
        self.assertEqual(spellcheck("In fact, the effect of circine on the human body\n'", changes_by_paragraph = "T").fix(), "NOTE: No changes made to text")
    
        
    def test_spellcheck_contains_uppercase(self):
        self.assertEqual(spellcheck("He falls ilL.").fix(), "He falls ill.")


    def test_fixes_multiple_errors(self):
        self.assertEqual(spellcheck("I hope yov will f1nd all the rnistakes in this sentence. Otherwise, I wlll be very sad.").fix(), "I hope you will find all the rnistakes in this sentence. Otherwise, I will be very sad.")


    def test_spellcheck_speed_acceptable(self):
        # GOALS
        # 0 misspells = < 0.01 seconds  [V1.3 = 0.0025s]
        # 1 misspell = < 0.10 seconds   [V1.3 = 0.070s]
        # additional misspells "cost" the same amount of time (ie. execution scales linearly with # of misspells)  [V1.3 - this seems to hold true]
        self.assertLessEqual(time_func(sc,"this text has no issues"), 0.01)
        self.assertLessEqual(time_func(sc,"He falls ilL."), 0.2) 
        self.assertLessEqual(time_func(sc,"I hope yov will f1nd all the rnistakes in this sentence. Otherwise, I wlll be very sad."), 1)

# TODO

# MASHUPS
# This one currently fails - OCRfixr sometimes mis-handles mashed up words
#    def test_fixes_mashed_words(self):
#       self.assertEqual(spellcheck("It seemed a long time as we sat there in the darkness waiting for the train; but it was perhaps, in fact, less than half anhour.").fix(), "It seemed a long time as we sat there in the darkness waiting for the train; but it was perhaps, in fact, less than half an hour.")

# EXTRA SPACES
# This one currently fails - OCRfixr doesn't see the relevant character due to the extra space, and duplicates it
#    def test_fixes_extra_spaces(self):
#       self.assertEqual(spellcheck("But suppose I spare your lif e--will you help me to escape?").fix(), "But suppose I spare your life--will you help me to escape?")


if __name__ == '__main__':
    unittest.main()