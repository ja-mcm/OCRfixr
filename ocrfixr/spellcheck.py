"""Main module."""
import re
import string
from pandas import DataFrame
from nltk.corpus import brown
from nltk.tokenize import WhitespaceTokenizer, RegexpTokenizer
from transformers import pipeline
from textblob import Word


# Define dictionary of accepted words
word_set = set(brown.words())

# Set BERT to look for the 15 most likely words in position of the misspelled word
unmasker = pipeline('fill-mask', model='bert-base-uncased', topk=15)


class spellcheck:                       
    def __init__(self, text, return_fixes = "F"):
        self.text = text
        self.return_fixes = return_fixes
        
### DEFINE ALL HELPER FUNCTIONS
# ------------------------------------------------------
# Find all mispelled words in a passage.

    def _SPLIT_PARAGRAPHS(self, text):
        # Separate string into paragraphs - this keeps local context for BERT, just in smaller chunks 
        # If needed, split up excessively long paragraphs - BERT model errors out when >512 words, so break long paragraphs at 500 words
        tokens = RegexpTokenizer('[^\n]+\n{0,}|(?:\w+\s+[^\n]){500}').tokenize(text)
        return(tokens)
 

    def _LIST_MISREADS(self):
        tokens = WhitespaceTokenizer().tokenize(self.text)
        # First, drop hyphenated words, and those broken across lines
        regex = re.compile('.*-.*')
        no_hyphens = [x for x in tokens if not regex.match(x)]
        # Also, drop all items with leading caps (ie. proper nouns)
        regex = re.compile('[^A-Z][a-z0-9]{1,}')
        no_caps = [x for x in no_hyphens if regex.match(x)]
        # then, remove punct from each remaining token (such as trailing commas, periods, quotations ('' & ""), but KEEPING contractions). 
        no_punctuation = [l.strip(string.punctuation) for l in no_caps]
        words_to_check = no_punctuation
        
        # if a word is not in the master corpus from nltk, it is assumed to be a misspelling.
        misread = []
        for i in words_to_check:
            if i not in word_set:
                misread.append(i)
        
        return(misread)
    # test1 for tokenizer: "'I'm not sure', Adam said. 'I can't see it. The wind-n\ow is half-shut.'" --- should result in no misreads << CORRECT >>
    # test2 for tokenizer: "Hello, I'm a maile model." --- should result in "maile" being flagged. << CORRECT >>
    
    # NEED TO: remove "3-in-a-rows" --- these help limit issues where inserts of text in foreign language is present, esp in footnotes
    
    
    # Return the list of possible spell-check options. These will be used to look for matches against BERT context suggestions
    def __SUGGEST_SPELLCHECK(self, text):
        textblob_suggest = Word(text).spellcheck()
        suggested_words = [x[0] for x in textblob_suggest]  # textblob outputs a list of tuples - extract only the first part of the 2 element tuple (suggestion , percentage)
        return(suggested_words)
    
    # NOTE: originally done via pyspellcheck spell.candidates. textblob is roughly 3x faster (checking ~40 words takes 5 seconds vs 15 seconds)
    # textblob often suggests different corrections. Mostly, pyspellcheck seems to have more, but more tend to be gibberish words, while textblob keeps to more conventional words. This may be an issue with old texts, where words are bit more eccentric
    # TODO - Confirm no degradation in accuracy / capability of overall spellcheck
    
    
    
    # Suggest a set of the 15 words that best fit given the context of the misread
    def __SUGGEST_BERT(self, text):
        context_suggest = unmasker(text)
        suggested_words = DataFrame(context_suggest).token_str
        return(suggested_words)
    
    
    # Ensure that list items are correctly converted down without the [] 
    def __LIST_TO_STR(self, LIST):
        listToStr = ' '.join(map(str, LIST)) 
        return(listToStr)
    
        
    # Create [MASK] objects for each misspelling in the sentence. If the same word is misspelled multiple times, only [MASK] the first one.
    def __SET_MASK(self, orig_word, replacement, orig_text):
        updated_text = orig_text.replace(str(orig_word), str(replacement), 1)
        return(updated_text)
    # TODO - need the misspelling (orig_word) to be case-appropriate. pyspellcheck does not do this, so I will need to find another package to replace spell.unknown/spell.candidates
    
    
    # note that multi-replace will replace ALL instances of a mispell, not just the first one (ie. spell-check is NOT instance-specific to each mispell, it is misspell-specific). Therefore, it should be run on small batches of larger texts to limit potential issues.
    def _MULTI_REPLACE(self, fixes):
        # if there are no fixes, just return the original text
        if len(fixes) == 0 :
            return(self.text)
        else:
        # otherwise, replace all dict entries with the approved replacement word
            fixes = dict((re.escape(k), v) for k, v in fixes.items()) 
            pattern = re.compile("|".join(fixes.keys()))
            text_corrected = pattern.sub(lambda m: fixes[re.escape(m.group(0))], self.text)
            return(text_corrected)
    
    
    # Creates a dict of valid replacements for misspellings. If bert and pyspellcheck do not have a match for a given misspelling, it makes no changes to the word.
    def _FIND_REPLACEMENTS(self, misreads, get = "fixes"):
        SC = [] 
        mask = []
        # for each misread, get all spellcheck suggestions from textblob
        for i in misreads:
            SC.append(self.__SUGGEST_SPELLCHECK(i))
            mask.append(self.__SET_MASK(i,'[MASK]', self.text))
            # for each misread, get all context suggestions from bert
        bert = []
        for b in mask:
            bert.append(self.__SUGGEST_BERT(b))
    
            # then, see if spellcheck & bert overlap
            # if they do, set that value for the find-replace dict
            # if they do not, then keep the original misspelling in the find-replace dict (ie. make no changes to that word)
            
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
            return(self.text)
        
        # otherwise, look for candidates for replacement and 
        # Based on user input, either outputs the full corrected text, or simply list the misreads + their fixes (if found)
        else:
            fixes = self._FIND_REPLACEMENTS(misreads)
            if self.return_fixes == "T":
                return(fixes)
            else:
                correction = self._MULTI_REPLACE(fixes)
                return(correction)
    # TODO - re-define the return_fixes debug option - should collapse all into a single dict. This probably should also be a second object that is returned in a single function call, since it isn't a big object, and would save having to run the time-consuming code twice to see 1) the changed words and 2) the final result


    # Final OCR contextual spellchecker
    def replace(self):
        open_list = []
        for i in self._SPLIT_PARAGRAPHS(self.text):
            open_list.append(spellcheck(i).SINGLE_STRING_FIX())
        final_text = ''.join(open_list)
        return(final_text)



# TODO - check for mashed up words ("anhour" --> "an hour") BEFORE concluding they are misspells -- BERT/Spellcheck really can't handle these well, as I quickly found a case where OCRfixr incorrectly changed the text  
# Note:  find-replace is not instance-specific, it is misspell specific..."yov" will be replaced with "you" in all instances found in the text otherwise. Paragraph tokenization allows for this decision to be made on a per-instance basis...roughly :)  
# Note: OCRfixr ignores all words with leading uppercasing, as these are assumed to be proper nouns, which fall outside of the scope of what this approach can accomplish.

       
