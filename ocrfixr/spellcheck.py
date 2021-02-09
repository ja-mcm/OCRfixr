"""Main module."""
import re
import string
import ast
import importlib_resources
from transformers import pipeline
from textblob import Word



ocrfixr = importlib_resources.files("ocrfixr")
word_set = (ocrfixr / "data" / "SCOWL_70.txt").read_text().split()
word_set = set(word_set)
common_scannos = (ocrfixr / "data" / "common_scannos.txt").read_text()
common_scannos = ast.literal_eval(common_scannos)



# Set BERT to look for the 15 most likely words in position of the misspelled word
unmasker = pipeline('fill-mask', model='bert-base-uncased', top_k=15)


class spellcheck:                       
    def __init__(self, text, changes_by_paragraph = "F", return_fixes = "F", ignore_words = None, interactive = "F", common_scannos = "F"):
        self.text = text
        self.changes_by_paragraph = changes_by_paragraph
        self.return_fixes = return_fixes
        self.ignore_words = ignore_words or []
        self.interactive = interactive
        self.common_scannos = common_scannos

        
### DEFINE ALL HELPER FUNCTIONS
# ------------------------------------------------------
# Find all mispelled words in a passage.

    def _SPLIT_PARAGRAPHS(self, text):
        # Separate string into paragraphs - this keeps local context for BERT, just in smaller chunks 
        # If needed, split up excessively long paragraphs - BERT model errors out when >512 words, so break long paragraphs at 500 words
        tokens = re.findall('[^\n]+\n{0,}|(?:\w+\s+[^\n]){500}',text)
        return(tokens)

    
    def _LIST_MISREADS(self):
        tokens = re.split("[ \n]", self.text)
        tokens = [l.strip() for l in tokens] 
        
        # Drop hyphenated words, those with apostrophes (which may be intentional slang), words that are just numbers, and words broken across lines
        # Note: This does risk missing valid misreads, but our goal is to avoid "bad" corrections
        # Also, drop all items with leading caps (ie. proper nouns)
        # Also, drop all words with trailing numbers flanked by punctuation, indicating a footnote reference (money.4, item[1]) rather than a misspelling
        # Also, drop any 1-character "words" 

        no_hyphens = re.compile(".*-.*|.*'.*|[0-9]+")
        no_caps = re.compile('[^A-Z][a-z0-9]{1,}')
        no_footnotes = re.compile('.*[0-9]{1,}[\]|)]?$')
        
        words = [x for x in tokens if not no_hyphens.match(x) and no_caps.match(x) and not no_footnotes.match(x) and len(x) > 1]

        # then, remove punct from each remaining token (such as trailing commas, periods, quotations ('' & ""), but KEEPING contractions). 
        no_punctuation = [l.strip(string.punctuation) for l in words]
        words_to_check = no_punctuation
        
        # if a word is not in the SCOWL 70 word list (or the user-supplied ignore_words), it is assumed to be a misspelling.
        full_word_set = word_set.union(set(self.ignore_words))
        
        
        misread = []
        for i in words_to_check:
            if i not in full_word_set:
                misread.append(i)
        
        if self.common_scannos == "T":
            # add in common_scannos (needed for scannos with leading caps, which were dropped in the token processing step)
            for i in tokens:
                if i in common_scannos:
                    misread.append(i)
                
        L0 = len(tokens)
        L1 = len(misread)
        
        # throw away any paragraphs where > 30% of the words are unrecognized - this makes context-generation spotty AND likely indicates a messy post-script/footnote, or even another language. This limits trigger-happy changes to messy text.
        if L0 < 1:
            misread = misread
        elif L1/L0 > 0.30 and L0 > 10:
            misread = []
            
        return(misread)

        
    
    # Return the list of possible spell-check options. These will be used to look for matches against BERT context suggestions
    def __SUGGEST_SPELLCHECK(self, text):
        textblob_suggest = Word(text).spellcheck()
        suggested_words = [x[0] for x in textblob_suggest]  # textblob outputs a list of tuples - extract only the first part of the 2 element tuple (suggestion , percentage)
        return(suggested_words)
        
    
    # Suggest a set of the 15 words that best fit given the context of the misread    
    def __SUGGEST_BERT(self, text):
        context_suggest = unmasker(text)
        suggested_words = [x.get("token_str") for x in context_suggest]
        return(suggested_words)
    
    
    # Ensure that list items are correctly converted down without the [] 
    def __LIST_TO_STR(self, LIST):
        listToStr = ' '.join(map(str, LIST)) 
        return(listToStr)
    
        
    # Create [MASK] objects for each misspelling in the sentence. If the same word is misspelled multiple times, only [MASK] the first one.
    def __SET_MASK(self, orig_word, replacement, orig_text):
        updated_text = orig_text.replace(str(orig_word), str(replacement), 1)
        return(updated_text)
    
    
    # note that multi-replace will replace ALL instances of a mispell, not just the first one (ie. spell-check is NOT instance-specific to each mispell, it is misspell-specific). Therefore, it should be run on small batches of larger texts to limit potential issues.
    def _MULTI_REPLACE(self, fixes):
        # if there are no fixes, just return the original text
        if len(fixes) == 0 :
            return(self.text)
        else:
        # otherwise, replace all dict entries with the approved replacement word
            text_corrected = self.text
            for i, j in fixes.items():
                text_corrected = re.sub(re.escape(i), j, text_corrected)
            return(text_corrected)
    
    
    def ___INSERT_NEWLINES(self, string):
        return(re.sub("([^\n]{64})", "\\1\n", string, 0, re.DOTALL))
    
    
    def _CREATE_DIALOGUE(self, context, old_word, new_word):
        
        import tkinter as tk
        from tkinter import ttk
        
        def ___PRESS_IGNORE():
            global proceed
            proceed = False
            root.destroy()
            ### TODO - add IGNORE ALL for repeated misreads of the same word (>2 times in text) - should only ask ONCE
            
        def ___PRESS_UPDATE():
            global proceed
            proceed = True
            root.destroy()    
            ### TODO - add ACCEPT ALL for repeated misreads of the same word (>2 times in text) - should only ask ONCE
            ### TODO - create exit-valve from interactive mode, where user can stop generation of pop-up windows. This should cancel all further updates to the text.


        root = tk.Tk()
        root.title('Spellcheck Suggestion') 
        
        content = ttk.Frame(root, padding=(3,3,12,15))
        frame = ttk.Frame(content, borderwidth=5, relief="ridge", width=500, height=75)
        context = ttk.Label(content, text=self.___INSERT_NEWLINES(context))
        intro = ttk.Label(content, text="Found possible replacement for:")
        old_entry = ttk.Label(content, text=old_word,font = ('arial', 18, 'bold'))
        suggest = ttk.Label(content, text="Suggested:")
        new_entry = ttk.Label(content, text=new_word, font = ('arial', 18, 'bold'))
        update = ttk.Button(content, text="Update", command = ___PRESS_UPDATE)
        ignore = ttk.Button(content, text="Ignore", command = ___PRESS_IGNORE)
        
        content.grid(column=0, row=0, sticky=(tk.N, tk.S, tk.E, tk.W))
        frame.grid(column=0, row=0, columnspan=3, rowspan=5, sticky=(tk.N, tk.S, tk.E, tk.W))
        context.grid(column=0, row=0, sticky=(tk.N, tk.S, tk.E, tk.W), pady=5, padx=5)
        intro.grid(column=3, row=0, columnspan=2, sticky=(tk.N, tk.W), padx=5)
        old_entry.grid(column=3, row=1, columnspan=2, sticky=(tk.N,tk.E,tk.W), pady=5, padx=5)
        suggest.grid(column=3, row=2, columnspan=2, sticky=(tk.N, tk.S, tk.E, tk.W), padx=5)
        new_entry.grid(column=3, row=3, columnspan=2, sticky=(tk.N, tk.S, tk.E, tk.W), pady=5, padx=5)
        update.grid(column=3, row=5)
        ignore.grid(column=4, row=5)
        
        root.columnconfigure(0, weight=1)
        root.rowconfigure(0, weight=1)
        content.columnconfigure(0, weight=3)
        content.columnconfigure(1, weight=3)
        content.columnconfigure(2, weight=3)
        content.columnconfigure(3, weight=1)
        content.columnconfigure(4, weight=1)
        content.rowconfigure(1, weight=1)
        
        root.mainloop()
        
        
    # Creates a dict of valid replacements for misspellings. If bert and pyspellcheck do not have a match for a given misspelling, it makes no changes to the word.
    # When common_scannos is activated, these select words bypass the spellcheck/context check
    def _FIND_REPLACEMENTS(self, misreads):
        SC = [] 
        mask = []
        additional_changes = {}
        
        # for each misread, get all spellcheck suggestions from textblob
        # TODO - skip the BERT check step if no spellcheck suggestion exists for a given word, since we'll never use the BERT output in that case
        
        for i in misreads:
            if self.common_scannos == "T" and i in common_scannos:
                # if misread is a common scanno, then add that entry to a separate dict that will be merged back in later. This bypasses the BERT check step.
                add_scanno = dict((k, v) for k, v in common_scannos.items() if k in i)
                additional_changes.update(add_scanno)
            else:
                # otherwise, do the spellcheck + context check
                SC.append(self.__SUGGEST_SPELLCHECK(i))
                mask.append(self.__SET_MASK(i,'[MASK]', self.text))
        # for each misread, get all context suggestions from bert
        bert = []
        for b in mask:
            bert.append(self.__SUGGEST_BERT(b))
    
            # then, see if spellcheck & bert overlap
            # if they do, set that value for the find-replace dict
            # if they do not, then keep the original misspelling in the find-replace dict (ie. make no changes to that word)
            # if user indicated "common_scannos" = T, AND the word is in the common scanno list, then ignore the BERT context match step - common scannos will always get a find-replace, since they are in theory unambiguously tied to only one possible correct value
                   
            
            
        corr = []
        fixes = []
        x = 0
        while x < len(bert):
            overlap = set(bert[x]) & set(SC[x])
            corr.append(overlap)
            # if there is a single word that is both in context and pyspellcheck - update with that word
            if len(overlap) == 1:
                corr[x] = self.__LIST_TO_STR(corr[x])                
            # if no overlapping candidates OR > 1 candidate, keep misread as is
            else:
                corr[x] = ""
            x = x+1
    
        fixes = dict(zip(misreads, corr))
        fixes.update(additional_changes)
        
        # Remove all dict entries with "" values (ie. no suggested change)
        for key in list(fixes.keys()):
            if fixes[key] == "":
                del fixes[key]
        
        # Remove all dict entries where replacement is same as initial problematic text
        keys = [k for k, v in fixes.items() if k == v]
        for x in keys:
            del fixes[x]
                
        if self.interactive == "T":
            for key, value in fixes.items():
                
                #### ----> INSERT interactive FUNCTION HERE
                # create dialogue box containing: context, old_word, new_word
                # if user selects IGNORE, then just return "", which means no replacement is made
                # otherwise, the suggested change is retained in the fixes dict
                
                self._CREATE_DIALOGUE(self.text, key, value)
                if proceed == False:
                    no_fix = {key: ""}
                    fixes.update(no_fix)

        # Remove all dict entries with "" values (ie. no suggested change)
        for key in list(fixes.keys()):
            if fixes[key] == "":
                del fixes[key]
                
        return(fixes)
    
    
    # Define method for fixing a single string - note: the final function will fragment long strings into paragraphs
    def SINGLE_STRING_FIX(self):
        misreads = self._LIST_MISREADS()
        
        # if no misreads, just return the original text
        if len(misreads) == 0:
            if self.changes_by_paragraph == "T":
                unchanged_text = []
            else:
                unchanged_text = [self.text,{}]
            return(unchanged_text)
        
        # otherwise, look for candidates for replacement and update text where plausible matches are found
        # Based on user input, either outputs just the full corrected text, or also itemizes the changes
        else:
            fixes = self._FIND_REPLACEMENTS(misreads)
            correction = self._MULTI_REPLACE(fixes)
            # for any text that has no updates, remove from changes_by_paragraph output
            if self.changes_by_paragraph == "T" and len(fixes) == 0:
                full_results = []
            else:    
                full_results = [correction, fixes]
            return(full_results)


    # Final OCR contextual spellchecker
    def fix(self):
        open_list = []
        for i in self._SPLIT_PARAGRAPHS(self.text):
            open_list.append(spellcheck(i,changes_by_paragraph= self.changes_by_paragraph, interactive = self.interactive, common_scannos = self.common_scannos).SINGLE_STRING_FIX())  
        
        if self.changes_by_paragraph == "T":
            open_list = list(filter(None, open_list))
            if len(open_list) == 0:
                return("NOTE: No changes made to text")
            else:
                return(open_list)
        else:
            # collapse all corrected paragraphs
            corrections = [x[0] for x in open_list]
            corrected_text = []
            for i in corrections:
                corrected_text.append(i)
            final_text = ''.join(corrected_text)
            
            if self.return_fixes == "T":
                # collapse all spell corrections into a single dict
                fixes = [x[1] for x in open_list]
                word_changes = dict(j for i in fixes for j in i.items())
                # package up corrected text with the dict of word changes
                full_results = [final_text, word_changes]
                return(full_results)
            else:
                return(final_text)


# TODO - make tkinter play nicely with CLI python
# TODO - can we somehow negate the warm-up time for the transformers unmasker? (+ associate warning)?
# TODO - spellcheck is getting slow (unit test > 1 second for a multi-mistake sentence) - optimize steps to boost speed
# TODO - add "stealth scanno" logic to common_scannos --- this would be based on another list of scannos that yield valid words (for example: 'arid' --> 'and', 'be' --> 'he')
# TODO - add branch to interactive menu which would follow up any suggestions ignored and ask user if they want to Ignore All (for any misspell occurring >2 times in the text)
# TODO - likewise, add branch to interactive menu which would follow up any accepted suggestions that are in the common_scannos list (for any misspell occurring >2 times in the text)
# TODO - add top_k feature, which allows user to broaden the acceptable BERT context check. So, for higher k value, less-likely context candidates are included, increasing the number of fix suggestions but also possibly false positives (this is most useful in combination with using interactive review)
# TODO - need to ignore the first word of a new page, since these can be split words across pages (this may also just be tied up in the unsplit functionality, where this word should have a leading * to denote a split word)
# TODO - remove odd find-replaces that end up inserting the same word back in again ----->  ['adjustment of the dress, the hair, &c., in which\n', {'c': 'c'}]]
# TODO - check for mashed up words ("anhour" --> "an hour") BEFORE concluding they are misspells -- BERT/Spellcheck really can't handle these well, as I quickly found a case where OCRfixr incorrectly changed the text   --->   Walker of the Secret Service book is a great test for this!


# Note: find-replace is not instance-specific, it is paragraph specific..."yov" will be replaced with "you" in all instances found in that section of text. It would be rare, but this may cause issues when a repeated scanno is valid & not valid within the same paragraph
# Note: OCRfixr ignores all words with leading uppercasing, as these are assumed to be proper nouns, which fall outside of the scope of what this approach can accomplish.

       
