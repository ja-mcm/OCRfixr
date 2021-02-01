"""Main module."""
import re
import string
import importlib_resources


ocrfixr = importlib_resources.files("ocrfixr")
word_set = (ocrfixr / "data" / "SCOWL_70.txt").read_text().split()
word_set = set(word_set)

common_words = (ocrfixr / "data" / "SCOWL_20.txt").read_text().split()
common_words = set(common_words)


class unsplit:                       
    def __init__(self, text, return_fixes = "F"):
        self.text = text
        self.return_fixes = return_fixes

        
### DEFINE ALL HELPER FUNCTIONS
# ------------------------------------------------------
# Find all split words in a passage.


    def _LIST_SPLIT_WORDS(self):
        tokens = re.split(" |(?<!-)\n", self.text)
        tokens = [l.strip() for l in tokens] 
        
        # pick up anything with a -\n string in it (except items with trailing "words" that are all numbers - these are end of page hyphens)
        regex = re.compile(".+[^-](-\n).+")
        has_newline = [x for x in tokens if regex.match(x)]
        
        split_words = has_newline
           
        return(split_words)

        

    def __DECIDE_HYPHEN(self, text):
        # Define word segments (full, 1st half, 2nd half)
        text = text
        no_punct = text.replace("^[[:punct:]]+|[[:punct:]]+$", "")
        no_hyphen = no_punct.replace("-\n", "")
        W0 = no_hyphen
        W1 = re.findall(".*(?=-\n)", no_punct)[0]
        W2 = re.findall("(?<=-\n).*", no_punct)[0]
        
        # Define possible adjustments
        remove_hyphen = text.replace("-\n", "") + "\n"
        keep_hyphen = text.replace("-\n", "-") + "\n"
        unsure_hyphen = text.replace("-\n", "-*") + "\n"
        end_pg_hyphen = text.replace("-\n", "-*\n") + " "

        
        
        # Define tests of "wordiness"
        W0_real = W0 in word_set
        W0_common = W0 in common_words
        W1_real = W1 in word_set
        W2_real = W2 in word_set
        Has_proper = all([W1.istitle() == False, W2.istitle() == True])
        Has_num = any(filter(str.isdigit, W1) or filter(str.isdigit, W2))
        End_pg = "--File" in W2 or W2.isdigit() == True

        # Decides whether a split word should retain its hyphen
        # To accomplish this, OCRfixr checks the hyphenated word against the accepted word list:
        # - If word IS recognized without the hyphen, and both word halves are NOT recognized, REMOVE THE HYPHEN. (ex: dis-played --> displayed)
        # - If word IS recognized without the hyphen, and both word halves ARE recognized, KEEP THE HYPHEN and add a * directly after the hyphen, to flag for the editor that OCRfixr is uncertain (ex. English-man --> English-*man)
        #   - However, if that unhyphenated word is very common, then just REMOVE THE HYPHEN, even if both halves of the word are valid (ex. with-in --> within)
        # - If word is NOT recognized without the hyphen, and both word halves ARE recognized, KEEP THE HYPHEN. (ex: well-meaning --> well-meaning)
        # - If word is NOT recognized without the hyphen, and both word halves are NOT recognized, REMOVE THE HYPHEN. These are assumed to be proper nouns.(ex: McAl-ister --> McAlister)
        #   - However, if the unrecognizable word is actually a number, then keep the hyphen (ex: 55-\n56 --> 55-56\n)
        #     OR, if the second word half is uppercased (likely a proper noun), then KEEP THE HYPHEN (ex. proto-Corinthian --> proto-Corinthian)
        # - Lastly, if the hyphenated word is at the end of the page (the word is split across pages), then KEEP THE HYPHEN and indicate with a *. This overrides all other previous rules
            # TODO: Also add a leading * to the first word on the following page
            # -*\n+[0-9]?-+File:\s[0-9]+.png-+\n[A-z]+ ----> replace .png-+\n with .png-+\n*

        if End_pg == True:
            return(end_pg_hyphen)
        else:
            if W0_real == True:
                if W0_common == True:
                    return(remove_hyphen)
                elif all([W1_real, W2_real]):
                    return(unsure_hyphen)
                else:
                    return(remove_hyphen)
                   
            else:    
                if all([W1_real, W2_real]) or Has_num == True or Has_proper == True: 
                    return(keep_hyphen)
                else:
                    return(remove_hyphen)

    
    # note that multi-replace will replace ALL instances of a split word. Hyphenation is NOT context-specific, it is rule-based
    def _MULTI_REPLACE(self, fixes):
        #if there are no fixes, just return the original text
        if len(fixes) == 0 :
            return(self.text)
        else:
        # otherwise, replace all split words with the approved replacement word from the dict, 
            #fixes = dict((re.escape(k), v) for k, v in fixes.items()) 
            #pattern = re.compile("|".join(fixes.keys()))
            #text_corrected = pattern.sub(lambda m: fixes[re.escape(m.group(0))], self.text)
            #return(text_corrected)
            text_corrected = self.text
            for i, j in fixes.items():
                text_corrected = re.sub(re.escape(i) + "(\s|\n)?", j, text_corrected)
            return(text_corrected)
    
     
    def _FIND_REPLACEMENTS(self, splits):
        new_word = [] 
        # for each split word, decide how to hyphenate it, then add to a dict
        for i in splits:
            new_word.append(self.__DECIDE_HYPHEN(i))
            
        fixes = dict(zip(splits, new_word))
                
        return(fixes)
    
    
    # Define method for un-splitting words
    def fix(self):
        split = self._LIST_SPLIT_WORDS()
        
        # if no split words, just return the original text, adding empty set {} if user requested return_fixes
        if len(split) == 0:
            if self.return_fixes == "T":
                unchanged_text = [self.text, {}]
            else:
                unchanged_text = self.text
            return(unchanged_text)
        
        # Based on user input, either outputs just the full corrected text, or also itemizes the changes
        else:
            fixes = self._FIND_REPLACEMENTS(split)
            correction = self._MULTI_REPLACE(fixes)
            
            if self.return_fixes == "T":
                full_results = [correction, fixes]
            else:
                full_results = correction
            return(full_results)

