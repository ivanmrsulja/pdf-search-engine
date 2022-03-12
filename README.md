# pdf-search-engine
Simple CLI search engine for searching PDF files.

To run the program, run ```python engine.py <document_name.pdf>``` in your console, ```<document_name.pdf>``` being the placeholder for the document you want to process. If you want all the features (like ranking results by page reference) to be operational, it is advised to use this tool only on documents written in english language
 as some of the references are derived from common phrases such as ('see page 12', 'on page 123'...).

Once you run the program, you will have to wait for the program to index the document, this can take anywhere from 1 to 10 seconds depending on your document size (the software is tested only on documents that are from 1 to 2000 pages long). When the indexing process is completed,
a search input line ```>>``` will show up, enabling you to enter a search phrase and run it by pressing ```ENTER```.

After entering a search query, this tool will give you all the relevant results which will be paged and sorted with regards to custom-made ranking with all the important parts highlighted (parts containing inserted words/phrases).
The ranking takes into account the number of words present on a page, word repetition, page references, whether a certain phrase (or part of phrase) is present and logical operations that are included into the query.

The phrases are entered between ```""```, for example: ```"red black trees"```.

Logical operators that are supported are: AND, OR and NOT. To include them in search queries simply type them in in all capital letters, with at least one white-space
character that separates them from other words, for example:

```
python AND sequence
            dictionary NOT list
            python OR dictionary NOT word
```
It is also possible to group parts of the expression together using braces ```()``` to bypass priority that the logical operators have above others.

Spell check, as well as an alternative word reccomendation system is also implemented and it is being evaluated for each word or phrase present in the query, alternative words will be displayed if there are no or too few search results present.

