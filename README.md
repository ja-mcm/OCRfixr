# OCRfixr

## OVERVIEW 
This project aims to automate the boring work of manually correcting OCR output from Distributed Proofreaders' book digitization projects


## CORRECTING MISREADS
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
| Spellcheck | stone, __store__, stoke, stove, stowe, stole, soie |
| BERT context | market, shop, town, city, __store__, table, village, door, light, markets, surface, place, window, docks, area |

Since there is match for both a plausible spellcheck replacement and that word reasonably matches the context of the sentence, OCRfixr updates the word. 

Corrected text:
> _"Days there were when small trade came to the __store__. Then the young clerk read._"


### Avoiding "Damn You, Autocorrect!"
By design, OCRfixr is change-averse:
- If spellcheck/context do not line up, no update is made.
- Likewise, if there is >1 word that lines up, no update is made.
- Only the top 15 context suggestions are considered, to limit low-probability matches.
- Proper nouns (anything starting with a capital letter) are not evaluated for spelling.

Word context is drawn from all sentences in the current paragraph, to maximize available information, while also not bogging down the BERT model. 


## Credits
__TextBlob__ powers spellcheck suggestions, and __transformers__ does the heavy lifting for BERT context modelling.
All book data comes from Distributed Proofreaders. Support them here: <https://www.pgdp.net/c/>