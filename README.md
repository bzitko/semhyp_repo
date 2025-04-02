# SemHyP: Semantic Hypergraph Parser

SemHyP is a **semantic hypergraph parser** that takes **textual annotations** as input and produces a **semantic hypergraph** as output.  

The **mandatory** textual annotations are:  
* POS (Part-of-Speech) tags
* Dependency relations 

However, **SemHyP performs best** when the input also includes:  
* Semantic Role Labels (SRL)
* Coreference annotations
* Named entity

### Example: CoNLL-Style format used in SemHyP for textual annotations

```
# Patrick knew about IBM's plans, but he was ready to ignore them.
0  0  Patrick + Patrick PROPN NNP nsubj  1  B-PERSON -         B-ARG0 O      O      B-MAIN1 O       -
0  1  knew    + know    VERB  VBD ROOT   1  O        know.01   B-V    O      O      O       O       know.v.01
0  2  about   + about   ADP   IN  prep   1  O        -         B-ARG1 O      O      O       O       -
0  3  IBM     - IBM     PROPN NNP poss   5  B-ORG    -         I-ARG1 O      O      O       B-MAIN2 -
0  4  's      + 's      PART  POS case   3  O        -         I-ARG1 O      O      O       I-MAIN2 -
0  5  plans   - plan    NOUN  NNS pobj   2  O        -         I-ARG1 O      O      O       I-MAIN2 plan.n.01
0  6  ,       + ,       PUNCT ,   punct  1  O        -         O      O      O      O       O       -
0  7  but     + but     CCONJ CC  cc     1  O        -         O      O      O      O       O       -
0  8  he      + he      PRON  PRP nsubj  9  O        -         O      B-ARG1 B-ARG0 B-REF1  O       -
0  9  was     + be      AUX   VBD conj   1  O        be.01     O      B-V    O      O       O       -
0 10  ready   + ready   ADJ   JJ  acomp  9  O        -         O      B-ARG2 O      O       O       ready.a.01
0 11  to      + to      PART  TO  aux    12 O        -         O      I-ARG2 O      O       O       -
0 12  ignore  + ignore  VERB  VB  xcomp  10 O        ignore.01 O      I-ARG2 B-V    O       O       ignore.v.01
0 13  them    - they    PRON  PRP dobj   12 O        -         O      I-ARG2 B-ARG1 O       B-REF2  -
0 14  .       + .       PUNCT .   punct  9  O        -         O      O      O      O       O       -
```  

### Column Description
| Column | Annotation | Required |
|--------|------------|----------|
| 1  | Sentence ID    | Yes |
| 2  | Token ID (position in sentence) | Yes |
| 3  | Word | Yes |
| 4  | "+" if followed by whitespace | Yes |
| 5  | Lemma (base form) | No |
| 6  | UPOS (Universal POS tag) | Yes |
| 7  | XPOS (Language-specific POS tag) | Yes |
| 8  | Dependency label | Yes |
| 9  | Head token ID (dependency head) | Yes |
| 10 | Named Entity label | No |
| 11 | Predicate role (if available) | No |
| 12-14 | Semantic Role Labels (SRL) | No |
| 15-16 | Coreference information | No |
| 17 | Word sense (if available) | No |

## Datasets in This Repository

This repository contains the following example datasets with textual annotations:

* Patrick - toy dataset used to demonstrate SemHyP's functionality.
* Natural Language 2 Semantic Hypergraph (NL2SH) - benchmark dataset published [here](https://www.clarin.si/repository/xmlui/handle/11356/1822)

## Installation & Usage

Currently, SemHyP can be installed by **cloning this repository**. No additional Python packages are required.
