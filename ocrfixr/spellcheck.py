"""Main module."""
from transformers import logging
logging.set_verbosity_error()
import re
import string
import ast
import importlib_resources
from collections import Counter
from transformers import pipeline
from symspellpy import SymSpell, Verbosity
from metaphone import doublemetaphone
import pkg_resources


### Load in project resources
# Full word list
ocrfixr = importlib_resources.files("ocrfixr")
word_set = (ocrfixr / "data" / "SCOWL_70.txt").read_text(encoding='utf-8').split()
word_set = set(word_set)

# List of words NOT in SCOWL 70 that we should ignore anyways
ignore_misreads = (ocrfixr / "data" / "ignore_these_misspells.txt").read_text(encoding='utf-8').split()
ignore_set_from_pkg = set(ignore_misreads)

# dict of common scannos to check for (bypasses the context check, since these are clear mappings)
common_scannos = (ocrfixr / "data" / "scannos_common.txt").read_text(encoding='utf-8')
common_scannos = ast.literal_eval(common_scannos)
common = set(common_scannos)

# dict of specifically tricky scannos to check for - misspellings that create real words (arid - and)
stealth_scannos = (ocrfixr / "data" / "scannos_stealth.txt").read_text(encoding='utf-8')
stealth_scannos = ast.literal_eval(stealth_scannos)
stealth = set(stealth_scannos)

# dict of OCRfixr suggestions that are known to be bad. This list prevents them from ever being suggested.
ignore_suggestions = (ocrfixr / "data" / "ignore_these_suggestions.txt").read_text(encoding='utf-8')
ignore_suggestions = ast.literal_eval(ignore_suggestions)
#ignore_suggestions = set(ignore_suggestions)

# setup symspell spellchecker parameters
sym_spell = SymSpell(max_dictionary_edit_distance=2, prefix_length=7)
dictionary_path = pkg_resources.resource_filename(
    "symspellpy", "frequency_dictionary_en_82_765.txt")
# term_index is the column of the term and count_index is the
# column of the term frequency
sym_spell.load_dictionary(dictionary_path, term_index=0, count_index=1)


# Set BERT to look for the 30 most likely words in position of the misspelled word
unmasker = pipeline('fill-mask', model='bert-base-uncased', top_k=30)


class spellcheck:                       
    def __init__(self, text, changes_by_paragraph = "F", return_fixes = "F", ignore_words = None, interactive = "F", common_scannos = "T", top_k = 15, return_context = "F", suggest_unsplit = "T"):
        self.text = text
        self.changes_by_paragraph = changes_by_paragraph
        self.return_fixes = return_fixes
        self.ignore_words = ignore_words or []
        self.interactive = interactive
        self.common_scannos = common_scannos
        self.top_k = top_k
        self.return_context = return_context
        self.suggest_unsplit = suggest_unsplit


        
### DEFINE ALL HELPER FUNCTIONS
# ------------------------------------------------------
    
    def _SPLIT_PARAGRAPHS(self, text):
        # Separate string into paragraphs - this keeps local context for BERT, just in smaller chunks 
        # If needed, split up excessively long paragraphs - BERT model errors out when >512 words, so break long paragraphs at 500 words
        tokens = re.findall('[^\n]+\n{0,}|(?:\w+\s+[^\n]){500}',text)
        return(tokens)

    # Find all mispelled words in a passage.
    def _LIST_MISREADS(self):
        tokens = re.split("[ \n]", self.text)
        tokens = [l.strip() for l in tokens] 
        
        # Drop hyphenated words, those with apostrophes (which may be intentional slang), words that are just numbers, and words broken across lines. Note: This does risk missing valid misreads, but our goal is to avoid making "bad" corrections above all else
        # Also, drop all items with leading caps (ie. proper nouns)
        # Also, drop all words with trailing numbers flanked by punctuation, indicating a footnote reference (money.4, item[1]) rather than a misspelling
        # Also, drop any 1-character "words" 

        no_hyphens = re.compile(".*-.*|.*'.*|.*\.{3,}.*|.*’.*|[0-9]+")
        no_caps = re.compile('[^A-Z]{2,}')
        no_footnotes = re.compile('.*[0-9]{1,}[^A-z]?$')
        no_roman_nums = re.compile('[xlcviXLCVI.:,-;]+$')
        no_eth_endings = re.compile('.*eth|.*est$')
        no_format_tags = re.compile('</?[a-z]>.*|.*</?[a-z]>')
        no_list_items = re.compile('.*\\)|.*\\]')
        all_nums = re.compile('^[0-9]{1,}$')

        words = [x for x in tokens if not no_hyphens.match(x) and no_caps.match(x) and not no_footnotes.match(x) and not no_roman_nums.match(x) and not no_eth_endings.match(x) and not no_format_tags.match(x) and not no_list_items.match(x)]

        # then, remove punct from each remaining token (such as trailing commas, periods, quotations ('' & ""), but KEEPING contractions). 
        no_punctuation = [l.strip(string.punctuation+"”“’‘") for l in words]
        words_to_check = [x for x in no_punctuation if len(x) > 1 and not all_nums.match(x)]
        
        
        # if a word is not in the SCOWL 70 word list, it is assumed to be a misspelling.
        unrecognized = []
        for i in words_to_check:
            if i not in word_set:
                unrecognized.append(i)
        
        
        # throw away any paragraphs where > 30% of the words are unrecognized - this makes context-generation spotty AND likely indicates a messy post-script/footnote, or even another language. This limits trigger-happy changes to messy text.
        L1 = len(tokens)
        L0 = len(unrecognized)
        if L0/L1 > 0.30 and L1 > 10:
            unrecognized = []
        else: 
            unrecognized = unrecognized
      
        
        # Allow user to specify terms to NOT look at (for example, known slang in the text) = ignore_set_from_user
        # plus, remove problematic words = ignore_set_from_pkg, 
        # this contains a small set of problematic terms that aren't "words" (example: th, as in "7 th")
        # as well as the 2,000 most-common words in the following languages: Latin, Greek, French, German, Spanish
        ignore_set_from_user = set(self.ignore_words)
        
        misread = []
        for i in unrecognized:
            if i not in ignore_set_from_pkg and i not in ignore_set_from_user:
                misread.append(i)

        # add scannos to misreads, if option is selected        
        if self.common_scannos == "T":
            # add in common_scannos with leading caps (which were dropped in the token processing step)
            # add in stealth_scanno candidates (correctly spelled words that match entries in the stealth_scanno dict) - these were also dropped in the token processing step
            for i in tokens:
                if i not in misread and i in common or i in stealth:
                    misread.append(i)
            
        return(misread)


    def _CT_MISREADS(self):
        all_misreads = Counter(self._LIST_MISREADS())
        multi_misreads = { k: v for k, v in all_misreads.items() if v > 2 }
        return(multi_misreads)
        
    
    # Return the list of possible spell-check options. These will be used to look for matches against BERT context suggestions
    def __SUGGEST_SPELLCHECK(self, text):
        suggested_words = []
        
        # Confirm word isn't a mashup ("anhour" --> "an hour")
        Num_spaces = []
        for i in sym_spell.lookup_compound(text, max_edit_distance=0):
            Num_spaces.append(getattr(i, "term"))

        # If it is not flagged as a possible mashup, then ask for plausible replacement words for the full misspelled word                
        if str(Num_spaces).count(' ') == 0:
            for i in sym_spell.lookup(text, Verbosity.CLOSEST, max_edit_distance=2):
                term = getattr(i, "term")
                if len(term) > 1:
                    suggested_words.append(term)
        
        # If symspell suggests that the misspell should actually be be 2 words, then pass the multi-word phrase
        else:
            mw = Num_spaces.pop()
            
            # If the mashup has a comma in it, add a comma to the suggestion
            if "," in text:
                mw = re.sub(" ", ", ", mw)
            suggested_words.append(mw)
            
        return(suggested_words)
        
    
    # Suggest a set of the 15 words that best fit given the context of the misread    
    def __SUGGEST_BERT(self, text, number_to_return = 15):
        context_suggest = unmasker(text)
        suggested_words = [x.get("token_str") for x in context_suggest][:number_to_return]
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
        return(re.sub("([^\n]{64})([^\s]{1,})", "\\1\\2\n", string, 0, re.DOTALL))
    
    
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

        
    # Creates a dict of valid replacements for misspellings. If bert and symspell do not have a match for a given misspelling, it makes no changes to the word.
    # When common_scannos is activated, that limited list of words bypass the spellcheck/context check
    def _FIND_REPLACEMENTS(self, misreads):
        SC = [] 
        bert = []
        punct_split_fixes = {}
        common_scanno_fixes = {}
        
        # for each misread, get all spellcheck suggestions
        for i in misreads:
            # if misread is a common scanno, then add that entry to a separate dict that will be merged back in later. This bypasses the BERT check step.
            if self.common_scannos == "T" and i in common:
                add_scanno = dict((k, v) for k, v in common_scannos.items() if k == i)
                common_scanno_fixes.update(add_scanno)
            
            # for stealth scannos - these are valid (yet incorrect) words. So, instead of SUGGEST_SPELLCHECK (which would return the same word supplied), take the value from the stealth_scanno dict, which is the desired word to check for in BERT context (arid --> and)
            elif self.common_scannos == "T" and i in stealth:
                SC.append(stealth_scannos.get(i).split(" "))
                SB = self.__SUGGEST_BERT(text = self.__SET_MASK(i,'[MASK]', self.text), 
                                                number_to_return = self.top_k)
                
                # if the original stealth scanno also makes sense in context, then don't record the suggestion
                if i not in SB:
                    bert.append(SB)
            
            # for all other unrecognized words, get all spellcheck suggestions from symspell
            else:
                spellcheck = self.__SUGGEST_SPELLCHECK(i)
                # Make sure there is a valid spellcheck suggestion (symspell returns the original string if not)
                if spellcheck == i:
                    # if no spellcheck suggestion given, remove from misreads (ie. dont bother checking BERT context - it won't get used)
                    misreads.delete(i)
                else: 
                   # For multi-word phrases....
                    if self.suggest_unsplit == "T" and len(spellcheck) == 1 and str(spellcheck).count(' ') == 1:
                        
                        # if the phrase was already separated by a comma or period ("shall.cultivate"), skip the BERT context check
                        # just confirm that both word halves are valid
                        if "." in i or "," in i:
                            mw = ''.join(spellcheck)                           
                            fw = re.findall("^[^\s,]+", mw).pop()
                            sw = re.findall("[^\s]+$", mw).pop()
                            
                            if fw in word_set and sw in word_set:
                                # if first letter after period split is uppercased, retain it and add a period ('ended.He' --> 'ended. He')
                                if len(re.findall("\.{1,}([A-Z][a-z]+)", i)) > 0:
                                    fw = fw + '. '
                                    sw = str.title(sw)
                                    mw = fw + sw

                                add_splitto = {i:mw}
                                punct_split_fixes.update(add_splitto)

                    
                        # If symspell has to pick an arbitrary cutoff between the words ("anhour"), check the suggestion using BERT context
                        # Feed in the first word into the text, then confirm whether second word fits the context of the sentence using BERT. If so, the two word phrase will be accepted as a valid correction
                        else:
                            # tee up symspell suggestion for comparison to BERT suggestion
                            SC.append(spellcheck)  
                            
                            mw = ''.join(spellcheck)
                            fw = re.findall("^[^\s]+", mw).pop()
                            SB = self.__SUGGEST_BERT(text = self.__SET_MASK(i, fw + ' [MASK]', self.text), 
                                                            number_to_return = self.top_k)   
                            
                            # Tack the first word onto the results for each BERT context suggestion. These are compared against the multi-word phrase provided by sympell
                            SBi = []
                            for x in SB:
                                SBi.append(fw + ' ' + x)
                            
                            bert.append(SBi)
                              

                    else:    
                        SC.append(spellcheck)  

                        # otherwise, just mask the misspelled word for BERT context check, which will be compared against symspell
                        bert.append(self.__SUGGEST_BERT(text = self.__SET_MASK(i,'[MASK]', self.text), 
                                                        number_to_return = self.top_k))
    
        # then, see if spellcheck & bert overlap
        # if they do, set that value for the find-replace dict
        # if they do not, then keep the original misspelling in the find-replace dict (ie. make no changes to that word)
        # if user indicated "common_scannos" = T AND the word is in the common scanno list, then ignore the BERT context match step - common scannos will always get a find-replace, since they are in theory unambiguously tied to only one possible correct value            
          
        corr = []
        fixes = []
        x = 0
        while x < len(bert):
            overlap = set(bert[x]) & set(SC[x])
            corr.append(overlap)
            # if there is a single word that is both in context and symspellpy - update with that word
            if len(overlap) == 1:
                corr[x] = self.__LIST_TO_STR(corr[x])                
            # if no overlapping candidates OR > 1 candidate, keep misread as is
            else:
                corr[x] = ""
            x = x+1
            
            
        fixes = dict(zip(misreads, corr))
        
        try:
            for key, value in fixes.copy().items():
                # if it's a simple "remove an 's' from the end", (kissings --> kissing) then delete that fix
                if value + "s" == key:
                    del fixes[key]
                # if it's an o -> e ending fix (bo --> be), ignore the soundex check
                elif key[len(key)-1] == "o" and value[len(value)-1] == "e":
                    pass
                # ignore soundex check for mashups (anhour --> an hour). Found by looking for a space (' ') in the replacement suggestion                
                elif value.count(' ') == 1:
                    pass
                # Check whether the find-replace candidate is a homophone - these suggestions are ignored, to avoid flagging intentional (stylistic) homophones (ie. without / widout)
                # soundex check = double metaphone
                elif doublemetaphone(key)[0] == doublemetaphone(value)[0]:
                    del fixes[key]
        # If soundex can't parse the character, just skip the check
        except Exception:
            pass
          
        # Add the common scannos to the mix
        fixes.update(common_scanno_fixes)
        fixes.update(punct_split_fixes)
    
    
        # Remove all dict entries where replacement is same as initial problematic text
        no_change = [k for k, v in fixes.items() if k == v]
        for x in no_change:
            del fixes[x]
                
        # Remove all dict entries that are in the list of known bad suggestions
        overlap = dict(fixes.items() & ignore_suggestions.items())
        for x in overlap:
            del fixes[x]
        
            
        if self.interactive == "T":
            # Remove all dict entries with "" values (ie. no suggested change) --- this cleans up the suggestions the user sees
            for key in list(fixes.keys()):
                if fixes[key] == "":
                    del fixes[key]
                    
            for key, value in fixes.items():
                
                #### INTERACTIVE FUNCTION
                # create dialogue box containing: context, old_word, new_word
                # if user selects IGNORE, then just return "", which means no replacement is made
                # otherwise, the suggested change is retained in the fixes dict
                
                self._CREATE_DIALOGUE(self.text, key, value)
                if proceed == False:
                    no_fix = {key: ""}
                    fixes.update(no_fix)

        # Remove all dict entries with "" values (ie. no suggested change).
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
            if self.changes_by_paragraph == "T":
                if len(fixes) == 0:
                    full_results = []
                else:
                    full_results = []
                    # TODO - Need to make this iterate through all items in the fixes dict (currently only does the first)
                    for key, value in fixes.items():    
                        txt = re.sub('^[0-9]+: ', '', self.text)
                        loc = txt.find(key) - 1
                        if self.return_context == "T":
                            full_results.append('{0} Suggest \'{1}\' for \'{2}\' | {3}'.format(loc, value, key, self.text))
                        else:
                            full_results.append('{0} Suggest \'{1}\' for \'{2}\''.format(loc, value, key))
            else:    
                full_results = [correction, fixes]
            return(full_results)


    # Final OCR contextual spellchecker
    def fix(self):
            
        open_list = []
        
        # run spellcheck against each paragraph separately
        for i in self._SPLIT_PARAGRAPHS(self.text):
            open_list.append(spellcheck(i,changes_by_paragraph= self.changes_by_paragraph, interactive = self.interactive, common_scannos = self.common_scannos, top_k = self.top_k, return_context = self.return_context, suggest_unsplit = self.suggest_unsplit).SINGLE_STRING_FIX())          

        
        if self.changes_by_paragraph == "T":
            open_list = list(filter(None, open_list))
            if len(open_list) == 0:
                return("NOTE: No changes made to text")
            else:
                return('\n'.join(sum(open_list, [])))
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
                word_changes = list(j for i in fixes for j in i.items()) 
                counts = dict(Counter(word_changes))
                counts = dict(sorted(counts.items(), key=lambda item: -item[1]))
                # package up corrected text with the dict of word changes
                full_results = [final_text, counts]
                return(full_results)
            else:
                return(final_text)



# TODO - (ADD_DICTS) Need to add selectable foreign language dictionaries 
# TODO - (IGNORE_SPLIT_WORDS) need to ignore the first word of a new page, since these can be split words across pages (this may also just be tied up in the unsplit functionality, where this word should have a leading * to denote a split word)
# TODO - (ADD_STEALTHOS) Need to add additional common stealth scannos to OCRfixr
# TODO - (FULL_PARAGRAPHS) Need to allow BERT context to draw from all lines in a full paragraph (currently resets at each newline -- this corresponds to 1 line of text in a Gutenberg text, and likely leads to degraded spellcheck performance due to loss of context)
# TODO - (GutenBERT) fine-tune BERT model on Gutenberg texts, to improve relatedness of context suggestions
# TODO - (WARM_UP) can we somehow negate the warm-up time for the transformers unmasker?
    # pipelines = 7 secs
    # symspellpy dictionary load = 3 seconds


# Note: find-replace is not instance-specific, it is paragraph specific..."yov" will be replaced with "you" in all instances found in that section of text. It would be rare, but this may cause issues when a repeated scanno is valid & not valid within the same paragraph
# Note: OCRfixr ignores all words with leading uppercasing, as these are assumed to be proper nouns, which fall outside of the scope of what this approach can accomplish.


       
