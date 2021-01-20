#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import unittest
from ocrfixr import unsplit


class TestStringMethods(unittest.TestCase):
    
  
    def test_unhyphenates_proper_nouns(self):
        self.assertEqual(unsplit("McAli-\nster").fix(), "McAlister\n")
                                 

    def test_unhyphenates_split_up_words(self):
        self.assertEqual(unsplit("par-\nticular").fix(), "particular\n")
        self.assertEqual(unsplit("mid-\ndle").fix(), "middle\n")
        self.assertEqual(unsplit("vanish-\ning").fix(), "vanishing\n")
        self.assertEqual(unsplit("un-\nambiguous").fix(), "unambiguous\n")
        self.assertEqual(unsplit("re-\nturned").fix(), "returned\n")
        self.assertEqual(unsplit("deser-\ntion").fix(), "desertion\n")
        

    def test_leading_trailing_punc_is_ignored(self):
        self.assertEqual(unsplit("'white-\nwater").fix(), "'whitewater\n")
        self.assertEqual(unsplit("and he checked-\n|").fix(), "and he checked|\n")


    def test_handles_empty_text(self):
        self.assertEqual(unsplit("").fix(), "")


    def test_flags_words_that_are_ambiguous(self):
        self.assertEqual(unsplit("sports-\nman").fix(), "sports-*man\n")
        

    def test_overrides_ambiguous_flag_for_common_words(self):
        self.assertEqual(unsplit("with-\nin").fix(), "within\n")
        self.assertEqual(unsplit("out-\nside").fix(), "outside\n")
        self.assertEqual(unsplit("in-\nstead").fix(), "instead\n")
        self.assertEqual(unsplit("pass-\nage").fix(), "passage\n")
  
 
    def test_keeps_compound_words_hyphenated(self):
        self.assertEqual(unsplit("well-\nmeaning").fix(), "well-meaning\n")
        self.assertEqual(unsplit("square-\nshouldered").fix(), "square-shouldered\n")
        
        
    def test_return_fixes_flag(self):
        self.assertEqual(unsplit("He saw the red pirogue, adrift and afire in the mid-\ndle of the river!", return_fixes = 'T').fix(), ["He saw the red pirogue, adrift and afire in the middle\nof the river!", {"mid-\ndle":"middle\n"}])


    def test_returns_the_full_text(self):
       self.assertEqual(unsplit("He saw the red pirogue, adrift and afire in the mid-\ndle of the river!").fix(), "He saw the red pirogue, adrift and afire in the middle\nof the river!")


    def test_maintains_capitalization(self):
        self.assertEqual(unsplit("Ca-\nnoe").fix(), "Canoe\n")

        
    def test_words_do_not_combine_across_paragraphs(self):
        self.assertEqual(unsplit("'The search was re-\nsumed.\n\nThe sun was down").fix(), "'The search was resumed.\n\nThe sun was down")


    def test_correctly_handles_multi_hyphen_words(self):
        self.assertEqual(unsplit("six-\nteen-footer").fix(), "sixteen-footer\n")


    def test_correctly_handles_leading_trailing_punctuation(self):
        self.assertEqual(unsplit("test-\ning,").fix(), "testing,\n")
        self.assertEqual(unsplit("test-\ning,").fix(), "testing,\n")
        self.assertEqual(unsplit("father--\nwhom").fix(), "father--\nwhom")


    def test_doesnt_unhyphenate_numbers(self):
       self.assertEqual(unsplit("55-\n56,").fix(), "55-56,\n")


    def test_doesnt_collapse_descriptive_hyphens_on_proper_nouns(self):
        self.assertEqual(unsplit("proto-\nCorinthian").fix(), "proto-Corinthian\n")
        self.assertEqual(unsplit("Mc-\nAllister").fix(), "McAllister\n")


# TODO





if __name__ == '__main__':
    unittest.main()
    
    
