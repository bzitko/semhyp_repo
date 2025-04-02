"""
This module defines the Doc class for handling documents in the semhyp package.

Classes:
    Doc: A class for handling documents, providing methods for token and span management.

Imports:
    Vocab: The Vocab class for handling vocabulary.
    Token: The Token class for handling individual tokens.
    Span: The Span class for handling spans within documents.
"""
from .vocab import Vocab
from .token import Token
from .span import Span

class Doc:
    """
    A class for handling documents, providing methods for token and span management.

    Attributes:
        STR_ANNOS (tuple): A tuple of string annotation types.
        NONE_ANNOS (tuple): A tuple of annotation types that can be None.
        vocab (Vocab): The vocabulary associated with the document.
        ents (tuple): A tuple of named entities in the document.
        srl (dict): A dictionary of semantic role labels in the document.
    """
    STR_ANNOS = ("lemma", "pos", "tag", "dep", "head") 
    NONE_ANNOS = ("roleset", "synset")

    def __init__(self, words, spaces=None):
        """
        Initializes a Doc object with words and optional spaces.

        Args:
            words (list of str): The words in the document.
            spaces (list of bool, optional): A list indicating whether each word is followed by a space. Defaults to None.

        Example:
            >>> doc = Doc(["Hello", "world"], [True, False])
            >>> print(doc[0].text)
            Hello
        """
        self.vocab = Vocab()
        
        tokens = []
        if spaces is None:
            spaces = [True] * len(words)
        for i, (word, space) in enumerate(zip(words, spaces)):
            self.vocab.put_text(word)
            tok = Token(self, word, space)
            tok.i = i
            tokens.append(tok)
        self._tokens = tuple(tokens)

        self.ents = tuple()
        self.srl = {}

    def __len__(self):
        """
        Returns the number of tokens in the document.

        Returns:
            int: The number of tokens in the document.

        Example:
            >>> doc = Doc(["Hello", "world"])
            >>> len(doc)
            2
        """        
        return len(self._tokens)

    def __iter__(self):
        """
        Returns an iterator over the tokens in the document.

        Returns:
            iterator: An iterator over the tokens in the document.

        Example:
            >>> doc = Doc(["Hello", "world"])
            >>> for token in doc:
            ...     print(token.text)
            Hello
            world
        """        
        return iter(self._tokens)

    def __getitem__(self, i):
        """
        Returns the token or span of tokens at the specified index or slice.

        Args:
            i (int or slice): The index or slice of tokens to retrieve.

        Returns:
            Token or Span: The token or span of tokens at the specified index or slice.

        Example:
            >>> doc = Doc(["Hello", "world"])
            >>> print(doc[0].text)
            Hello
            >>> span = doc[0:2]
            >>> print([token.text for token in span])
            ['Hello', 'world']
        """        
        if isinstance(i, slice):
            num_tokens = len(self._tokens)
            start = i.start or 0
            end = i.stop or num_tokens
            if start < 0:
                start = num_tokens + start
            if end < 0:
                end = num_tokens + end
            return Span(self, start, end)
        return self._tokens[i]

    def __unicode__(self):
        return "".join([t.text_with_ws for t in self])

    def __str__(self):
        return self.__unicode__()

    def __repr__(self):
        return self.__str__()
    
    @property
    def sents(self):
        """
        Returns the sentences in the document as a list of Span objects.

        Returns:
            list of Span: The sentences in the document.

        Example:
            >>> doc = Doc(["Hello", ".", "How", "are", "you", "?"])
            >>> for sent in doc.sents:
            ...     print([token.text for token in sent])
            ['Hello', '.']
            ['How', 'are', 'you', '?']
        """        
        sent_start = 0
        sent_counter = 1
        for t in self:
            if t.is_sent_start and t.i > sent_start:
                # print(sent_start, t.i)
                yield Span(self, sent_start, t.i, str(self[sent_start].sent_i))
                sent_start = t.i
                sent_counter += 1
        if self._tokens and sent_start < self[-1].i:
            # print(sent_start, self[-1].i)
            yield Span(self, sent_start, self[-1].i + 1, str(self[sent_start].sent_i))
            sent_counter += 1
