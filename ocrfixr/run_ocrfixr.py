#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
from transformers import logging
logging.set_verbosity_error()
import sys
import re
from tqdm import tqdm

def main():
  
    parser = argparse.ArgumentParser(prog ='run_ocrfixr',
                                     description ='Provides context-based spellcheck suggestions for input text.')
    
  
    parser.add_argument('text', 
                         help ='path to text you want to spellcheck')
    parser.add_argument('outfile', 
                         help ='path to output file')
    parser.add_argument('-Warp10', action ='store_const', const = True,
                        default = False, dest ='Warp10',
                         help ="option to ignore the most common misspells, which are likely correct words.")
    

    args = parser.parse_args()
    
    ### Read in file ============================================================
    # read in full file to check if the text has split words (which will cause false misreads to show up)
    # -- do this first to throw error early if file is invalid
    print("---- Loading text....")
    Full_Book = open(sys.argv[1], 'r').read()
    
    if len(re.findall("[A-z]-\n", Full_Book)) > 30:
        print("---- This file appears to have words split across lines, which can cause issues with the spellchecker")
        print("---- Merging split words back together...")
        from ocrfixr import unsplit
        fixed_text = unsplit(Full_Book).fix()
        data = fixed_text.split("\n")
    else:
        data = Full_Book.split("\n")
    
        
    from ocrfixr import spellcheck
    
    # Add line numbers
    q = []
    for (number, line) in enumerate(data):
        q.append('%d:  %s' % (number + 1, line))
        
     
        
    ### WARP10 Option ============================================================
    # Have OCRfixr ignore any word (>3 characters long) that pops up 10+ times
    # This allows for unrecognized words that are likely correct to be left alone, since they show up consistently in the text
    # OCRfixr runs fewer check cycles = faster execution
    
    if args.Warp10 == True:
        print("---- Engaging Warp10!")
        from collections import Counter

        M = spellcheck(Full_Book)._LIST_MISREADS()
        M = [word for word in M if len(word) > 3]
        counts = dict(Counter(M))
        counts = dict(sorted(counts.items(), key=lambda item: -item[1]))
        over_ten = {key:value for (key,value) in counts.items() if value >= 10}
        
        print("---- To speed things up, OCRfixr will ignore the following unrecognized words that popped up 10 or more times in the text:")
        if len(over_ten) == 0:
            print("NO WORDS IGNORED!")
        else:
            for k, v in over_ten.items():
                print(k, '-->', v)
        ignored_words = list(over_ten.keys())
    

    else:
        ignored_words = []    
    
    ### Run spellcheck on each line ==================================================
    print("---- Running spellcheck....")
    
    suggestions = []
    for i in tqdm(q):
        fixes = spellcheck(i, changes_by_paragraph = "T", ignore_words = ignored_words).fix()
        if fixes == "NOTE: No changes made to text":
            pass
        else:
            for x in fixes.split("\n"):
                suggestions.append(''.join((' '.join(re.findall('^[0-9]+:', i)), x)))
    

   ### Output file ============================================================
    print("---- File has been written to " + sys.argv[2])
    
    file=open(args.outfile,'w')
    for items in suggestions:
        file.writelines(items+'\n')
    file.close()
