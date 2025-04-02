"""
This module initializes the text processing components for the semhyp package.

Imports:
    Doc: The Doc class for handling documents.
    Span: The Span class for handling spans within documents.
    Token: The Token class for handling individual tokens.
    IOBTag: Utility for handling IOB tagging.

Constants:
    ANNOS (tuple): A tuple of annotation types available for text processing.
    TOK_ANNOS (tuple): A tuple of token-level annotation types.
    SPAN_ANNOS (tuple): A tuple of span-level annotation types.
"""
from .doc import Doc
from .span import Span
from .token import Token

from .util import IOBTag

ANNOS = ("text", "lemma", "pos", "tag", "ent", "roleset", "srl", "coref", "synset")
TOK_ANNOS = ("text", "lemma", "pos", "tag", "roleset", "synset")
SPAN_ANNOS = ("ent", "srl", "coref")
