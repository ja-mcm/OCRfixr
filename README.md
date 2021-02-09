# OCRfixr

## OVERVIEW 
This project aims to automate the boring work of manually correcting OCR output from Distributed Proofreaders' book digitization projects


## 1) CORRECTING MISREADS
OCRs can sometimes mistake similar-looking characters when scanning a book. For example, "l" and "1" are easily confused, potentially causing the OCR to misread the word "learn" as "1earn".

As written in book: 
> _"The birds flevv south"_

Corrected text:
> _"The birds flew south"_

### How OCRfixr Works:
OCRfixr fixes misreads by checking __1) possible spell corrections__ against the __2) local context__ of the word. For example, here's how OCRfixr would evaluate the following OCR mistake:

As written in book: 
> _"Days there were when small trade came to the __stoie__. Then the young clerk read._"

| Method | Plausible Replacements |
| --------------- | --------------- | 
| Spellcheck (TextBlob) | stone, __store__, stoke, stove, stowe, stole, soie |
| Context (BERT) | market, shop, town, city, __store__, table, village, door, light, markets, surface, place, window, docks, area |

Since there is match for both a plausible spellcheck replacement and that word reasonably matches the context of the sentence, OCRfixr updates the word. 

Corrected text:
> _"Days there were when small trade came to the __store__. Then the young clerk read._"


### Using OCRfixr

The package can be installed using [pip](https://pypi.org/project/OCRfixr/). 

```bash
pip install OCRfixr
```

By default, OCRfixr only returns the original string, with all changes incorporated:
```python
>>> from ocrfixr import spellcheck

>>> text = "The birds flevv south"
>>> spellcheck(text).fix()
'The birds flew south'
```

Use __return_fixes__ to also include all corrections made to the text:
```python
>>> spellcheck(text, return_fixes = "T").fix()
['The birds flew south', {'flevv': 'flew'}]
```

For longer texts, use __changes_by_paragraph__ to show each change in local context. This will only display the paragraphs that had updates made to them, for ease of review: 
```python
>>> text = "The birds flevv down\n south, bvt wefe quickly apprehended\n by border patrol agents"
>>> spellcheck(text, changes_by_paragraph = "T").fix()
[["The birds flew down\n",{"flevv":"flew"}], 
[" south, but were quickly apprehended\n", {"bvt":"but", "wefe":"were"}]]
```

_(Note: OCRfixr resets its BERT context window at the start of each new paragraph, so splitting by paragraph may be a useful debug feature)_


### Interactive Mode
OCRfixr also has an option for the user to interactively accept/reject suggested changes to the text:

```python
>>> text = "The birds flevv down\n south, bvt wefe quickly apprehended\n by border patrol agents"
>>> spellcheck(text, interactive = "T").fix()
```

<img width="723" alt="Suggestion 1" src="https://user-images.githubusercontent.com/67446041/107133270-7918c300-68b4-11eb-9de5-5b6282510c16.png">

Each suggestion provides the local context around the garbled text, so that the user can determine if the suggestion fits.

<img width="723" alt="Suggestion 2" src="https://user-images.githubusercontent.com/67446041/107133306-da409680-68b4-11eb-8a4c-69a8e034775c.png">

```python
>>> ### User accepts change to "flevv", but rejects change to "quikly" in GUI
'The birds flew down\n south and were quikly apprehended'
```

This returns the text with all accepted changes reflected. All rejected suggestions are left as-is in the text.


### Avoiding "Damn You, Autocorrect!"
By design, OCRfixr is change-averse:
- If spellcheck/context do not line up, no update is made.
- Likewise, if there is >1 word that lines up for spellcheck/context, no update is made.
- Only the top 15 context suggestions are considered, to limit low-probability matches.
- Proper nouns (anything starting with a capital letter) are not evaluated for spelling.

Word context is drawn from all sentences in the current paragraph, to maximize available information, while also not bogging down the BERT model. 



## 2) UNSPLITTING WORDS
Sometimes, books split words across lines with a hyphen. These need to be correctly pieced back together into a single word before a new line is started.

To glue words back together that are split across lines, OCRfixr checks the hyphenated word against the same word list to see if the newly reunited halves created a valid word, along with a few other rules. OCRfixr then decides if the split word needs that hyphen or not.

By default, OCRfixr only returns the original string, with all changes incorporated:
```bash
>>> from ocrfixr import unsplit

>>> text = "He saw the red pirogue, adrift and afire in the mid-\ndle of the river!"
>>> print(text)
'He saw the red pirogue, adrift and afire in the mid-
dle of the river!'

>>> print(unsplit(text).fix())
'He saw the red pirogue, adrift and afire in the middle
of the river!
```

As before, use __return_fixes__ to also include all corrections made to the text.

This method does not use __changes_by_paragraph__, as unsplit is rules-based rather than context-specific. There is no paragraph-specific context window. 


## Credits

- __TextBlob__ powers spellcheck suggestions
- __transformers__ does the heavy lifting for BERT context modelling. 
- SCOWL word list is Copyright 2000-2019 by Kevin Atkinson.
- All book data comes from Distributed Proofreaders. Support them here: <https://www.pgdp.net/c/>