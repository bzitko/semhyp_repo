from typing import List, Tuple, Dict
from .text import Token, Span, Doc
from .hyper.hyperedge import Atom, UniqueAtom, Hyperedge as Edge
import warnings

def alpha_condition(tok: Token) -> bool:
    return ((tok.head.dep not in {"prep"} and 
             tok.dep in {"case", "det", "predet", 
                         "amod", "nummod", "nmod", "quantmod", "compound", 
                         "aux", "auxpass", "prt", "neg"}) 
             or
            (tok.dep in {"advmod", "npadvmod"} and 
             tok.head.pos not in {"VERB", "AUX", "MD"}) 
             or
            (tok.head.pos == tok.pos == "X"))

ALPHA_PRIORS = {"prt": 3,
                "aux": 2,
                "auxpass": 2,
                "neg": 2,

                "compound": 5,
                "nmod": 5,
                "advmod": 4,
                "amod": 4,
                "nummod": 4,
                "quantmod": 3,
                "det": 4,
                "predet": 1,
               }

BETA_PRIORS = {"mark": -1,
               "cc": -2,               
               "conj": -3,
               "preconj": -4,
            #    "prep": -5,
            #    "agent": -5,
              }

def make_token_sequence(sent: Span) -> List[Tuple[int, int, int]]:
    """
    Creates a token sequence for a given sentence, assigning values based on
    syntactic distance, tree depth, and predefined priors for linguistic elements.

    This function utilizes three helper functions:
    1. `_get_dist(tok)`: Computes the syntactic distance between a token and its head
       by either directly comparing indices or counting sibling tokens.
    2. `_get_depth(tok)`: Determines the depth of a token in the dependency tree
       by counting the number of head relations between the token and the root.
    3. `_get_prior(tok)`: Assigns a prior value to a token based on its syntactic
       category. Special handling is given to tokens under certain conditions, such
       as conjunctions and dependency relationships.

    Args:
        sent (Span): A sentence (as a `Span` object) from a document.

    Returns:
        list: A list of token features, including syntactic distance, tree depth, and prior value.
    """
    def _get_dist(tok: Token) -> int:
        if alpha_condition(tok):
            return abs(tok.i - tok.head.i)
        
        if tok.dep == "mark":  # (so(as 
            return abs(tok.i - tok.head.i)
        
        dist = 0
        for child in tok.head.children:
            if alpha_condition(child):
                continue
            if child == tok:
                return dist
            dist += 1
        return dist
    
    def _get_depth(tok: Token) -> int:
        depth = 0
        temp = tok
        sent_root = tok.sent.root
        while temp != sent_root:
            temp = temp.head
            depth += 1
        return depth
    
    def _get_prior(tok: Token) -> int:
        if alpha_condition(tok):
            return ALPHA_PRIORS.get(tok.dep, 0)
        
        beta = BETA_PRIORS.get(tok.dep, 0)

        # Vidi "The speed, power and versatility of computer..."
        # konjunkcije se nalaze iza "of"
        if beta == 0 and tok.head.i < tok.i and tok.head.pos not in {"VERB", "AUX"}:
            conjs = tok.head.conjuncts
            if conjs:
                last = max(conjs)
                if last.i < tok.i:
                    return min(BETA_PRIORS.values()) - 1

        return beta

    def _get_tok_attrs(tok: Token) -> Tuple[int, int, int]:
        dist = _get_dist(tok)
        prior = _get_prior(tok)
        depth = _get_depth(tok)
        return ((-depth, -prior, dist), tok)
    
    return sorted(_get_tok_attrs(tok)
                  for tok in sent
                  if tok.dep != "punct")

SRL_ROLES = {"ADJ": "a", 
             "ADV": "r", 
             "CAU": "c", 
             "COM": "o", 
             "DIR": "d", 
             "DIS": "s",
             "EXT": "e", 
             "GOL": "g", 
             "LOC": "l", 
             "LVB": "b",
             "MNR": "m", 
             "MOD": "f",
             "NEG": "n",
             "PNC": "p",
             "PRD": "h", 
             "PRP": "i", 
             "PRR": "k",
             "V": "v",
             "TMP": "t",}

PROTO_ROLES = {"PPT" : "1",
               "PAG" : "0",
               "GOL" : "g",
               "PRD" : "h",
               "MNR" : "m",
               "DIR" : "d",
               "LOC" : "l",
               "VSP" : "q",
               "EXT" : "e",
               "CAU" : "c",
               "COM" : "o",
               "PRP" : "i",
               "TMP" : "t",
               "ADV" : "r",
               "ADJ" : "j",
               "REC" : "u"}

DEP_ROLES = {"nsubj": "s",
             "csubj": "s",
             "nsubjpass": "p",
             "csubjpass": "p",
             "expl": "e",
             "agent": "a",
             "acomp": "c",
             "attr": "c",
             "dobj": "o",
             "pobj": "o",
             "prt": "o",
             "oprd": "o",
             "dative": "i",
             "advcl": "x",
             "prep": "x", 
             "npadvmod": "x",
             "advmod": "x",
             "parataxis": "t",
             "intj": "j",
             "xcomp": "r",
             "ccomp": "r"}

ENTITIES = {"CARDINAL": "c", 
            "DATE": "d", 
            "EVENT": "e", 
            "FAC": "f", 
            "GPE": "g", 
            "LANGUAGE": "u", 
            "LAW": "w", 
            "LOC": "l", 
            "MONEY": "$", 
            "NORP": "n", 
            "ORDINAL": "#", 
            "ORG": "o", 
            "PERCENT": "%", 
            "PERSON": "p", 
            "PRODUCT": "r", 
            "QUANTITY": "q", 
            "TIME": "t", 
            "WORK_OF_ART": "a"}

def _convert_srl_role(label: str) -> str:
    if label[-1].isdigit():
        return label[-1]
    
    role = label.split("-")[-1]
    
    return SRL_ROLES.get(role, "?")


def _get_verb_args_by_srl_and_dep(verb: Token) -> Tuple[Dict[Token, str], Dict[Token, str]]:
    deps = {"case", "det", "predet", 
            "amod", "nummod", "nmod", "quantmod", "compound", 
            "aux", "auxpass", "prt", "neg", 
            "cc", "mark", 
            "dep", "punct", "meta"}
    
    verbs = {verb}

    if verb.doc.srl:
        # check for LVB
        lvbs = {span.root 
                for span in verb.sent.srl.get(verb, [])
                if span.label == "ARGM-PRR"}
        verbs.update(lvbs)

        srl_toks = {span.root: span.label 
                    for v in verbs 
                    for span in verb.sent.srl.get(v, [])
                    if span.root != v and 
                        span.label != "ARGM-LVB" and 
                        span.label != "ARGM-MOD" and 
                        (span.root.dep not in deps or 
                         (v.head == span.root and v.dep in {"relcl", "acl"}))}
    else:
        srl_toks = {}

    dep_toks = {tok: tok.dep
                for v in verbs
                for tok in v.children 
                if tok.dep not in deps}
    
    return srl_toks, dep_toks

def _get_predicate_roles(verb: Token) -> str:
    srl_toks, dep_toks = _get_verb_args_by_srl_and_dep(verb)
    toks = sorted(set(srl_toks) | set(dep_toks))
    
    srl_args, proto_args, dep_args, lr_args = [], [], [], []
    for tok in toks:        
        srl_arg = "-"
        if tok in srl_toks:
            label = srl_toks[tok]
            srl_arg = _convert_srl_role(label)
        srl_args.append(srl_arg)           
            
        proto_arg = "-"
        if tok in srl_toks:
            if False and verb.has_extension("roles"):
                label = srl_toks[tok]
                if not verb.roles:
                    proto_arg = "!"
                elif label not in verb.roles:
                    proto_arg = srl_arg
                else:
                    proto_arg = PROTO_ROLES.get(verb.roles[label], srl_arg) 
            else:
                proto_arg = "!"
        proto_args.append(proto_arg)
        
        dep_arg = "-"
        if tok in dep_toks:
            dep_arg = DEP_ROLES.get(dep_toks[tok], "?")
        dep_args.append(dep_arg)

        lr_arg = "l" if tok.i < verb.i else "r"
        lr_args.append(lr_arg)

    # cleaning up mistakes
    i = len(dep_args) - 1
    while i >= 0:
        if dep_args[i] == "?" and srl_args[i] == "-" and proto_args[i] == "-":
            dep_args.pop(i)
            srl_args.pop(i)
            proto_args.pop(i)
            lr_args.pop(i)
        i -= 1

    # finishing

    

    dep_roles = "".join(dep_args)
    srl_roles = "".join(srl_args)
    proto_roles = "".join(proto_args)
    proto_roles = srl_roles
    lr_roles = "".join(lr_args)

    if srl_roles.replace("-", ""):
        available_roles = [dep_roles, srl_roles]
    else:
        available_roles = [dep_roles]

    return ":".join(available_roles)

def _get_concept_features(tok: Token) -> str:
    if tok.tag.startswith("NN"):
        if tok.tag.endswith("S"):
            return "p"
        return "s"
    return ""

def _get_verb_features(token: Token) -> str:
    tense = '-'
    verb_form = '-'
    aspect = '-'
    mood = '-'
    person = '-'
    number = '-'
    verb_type = '-'

    if token.tag == 'VB':
        verb_form = 'i'  # infinitive
    elif token.tag == 'VBD':
        verb_form = 'f'  # finite
        tense = '<'  # past
    elif token.tag == 'VBG':
        verb_form = 'p'  # participle
        tense = '|'  # present
        aspect = 'g'  # progressive
    elif token.tag == 'VBN':
        verb_form = 'p'  # participle
        tense = '<'  # past
        aspect = 'f'  # perfect
    elif token.tag == 'VBP':
        verb_form = 'f'  # finite
        tense = '|'  # present
    elif token.tag == 'VBZ':
        verb_form = 'f'  # finite
        tense = '|'  # present
        number = 's'  # singular
        person = '3'  # third person

    features = (tense, verb_form, aspect, mood, person, number, verb_type)
    features = ''.join(features).rstrip("-")

    if token.roles: #TODO: pogledaj pipe roleset
        predicate_roles = {srl_role[3:]: proto_role
                           for srl_role, proto_role in token.roles.items()}
    else:
        predicate_roles = {}

    predicate_roles = "".join(sorted(predicate_roles))

    if predicate_roles:
        return features + ":" + predicate_roles
    else:
        return features
    
def _get_entity_features(tok: Token, *rest) -> str:
    if tok.ent.tag: # and tok.ent_type_ != tok.head.ent_type_:
        ent = ENTITIES.get(tok.ent.tag, "")
        if not rest:
            return ent
        if all(ENTITIES.get(t.ent.tag, "") == ent for t in rest):
            return ent
    return ""

def _get_appos_features(tok: Token) -> str:
    """
    - (r)estrictive / (n)ot restrictive
    - (c)omma / (b)racket / (q)uote / (n)one
    """
    start, stop = (tok.head.i, tok.i) if tok.i > tok.head.i else (tok.i, tok.head.i)

    puncts = {child.text 
              for child in tok.head.children 
              if start < child.i < stop and child.dep == "punct"}

    punct = puncts.pop() if len(puncts) == 1 else "n"
    if punct in "\"'`´‘’“”":
        punct = "q"  # quote - restrictive
    elif punct in "()[]\{\}":
        punct = "b"  # bracket - not restrictive
    elif punct in ",;":
        punct = "c"  # comma - not restrictive 

    return punct
    
def _get_trigger_subtype(tok: Token) -> str:
    if not tok.srl:
        return ""

    role = tok.srl.get(tok.head, "").split("-")[-1]
    if role == "TMP":
        return "t"
    if role == "LOC":
        return "l"
    return ""

def _get_directional_roles(tok: Token) -> str:
    if not alpha_condition(tok):
        return ""
    if tok.i < tok.head.i:
        return "<"
    elif tok.i > tok.head.i:
        return ">"
    return ""

def _get_conj_closure(tok: Token) -> Token:
    while tok.dep == "conj":
        tok = tok.head
    return tok

def build_type_and_subtype(tok: Token) -> str:
    if tok.dep == "conj":
        closure = _get_conj_closure(tok)
        if tok.tag == closure.tag:  # and tok.pos not in {"VERB"}:
            return build_type_and_subtype(closure)
            
    if tok.dep == "amod":
        if tok.tag == "JJR":
            return "Mc"
        if tok.tag == "JJS":
            return "Ms"
        return "Ma"
    if tok.dep == "nummod":
        return "M#"
    if tok.dep == "nmod":
        if tok.pos == "X":
            return "Cm"
        return "M"
    if tok.dep == "det":
        if tok.tag == "WDT":
            return "Mw"
        return "Md"
    if tok.dep == "neg":
        return "Mn"
    if tok.dep in {"aux", "auxpass"}:
        if tok.tag == "TO":
            return "Mi"
        if tok.tag == "MD":
            return "Mm"
        return "Mv"
    if tok.dep == "advmod":
        if tok.tag == "RBR":
            return "M="
        if tok.tag == "RBS":
            return "M^"
        if tok.tag == "WRB":
            return "Mw"
        return "M"
    if tok.dep == "predet":
        return "M"
    if tok.dep == "quantmod":
        return "M"
    if tok.dep == "prt":
        return "Ml.r"
    if tok.dep == "expl":
        return "Me"
    
    if tok.dep == "npadvmod" and tok.head.dep in {"mark", "prep"}:
        return "M"
    
    if tok.dep == "cc":
        return "J"
    if tok.dep == "preconj":
        return "J"
    
    if tok.dep == "poss":
        if tok.tag == "PRP$":
            return "Mp"
        if tok.tag == "PRP":
            return "Ci"
        if tok.pos not in {"NOUN", "PROPN"}:
            return "Mp"
    
    if tok.dep == "case":
        return "Bp"

    if tok.dep == "agent":
        return "T" + _get_trigger_subtype(tok)
    
    if tok.dep == "prep":
        if tok.head.pos not in {"VERB", "AUX", "MD"} and tok.head.dep not in {"prep"}:
#             if tok.head.dep == "acomp":
#                 return "Jr.ma"
            return "Br"
        
        return "T" + _get_trigger_subtype(tok)

    if tok.dep == "mark":
        return "T" + _get_trigger_subtype(tok)
    
    if tok.dep == "acomp":
        return "Ca"
    
    if tok.pos == "NOUN":
        return "Cc"
    if tok.pos == "PROPN":
        return "Cp"
    if tok.pos == "PRON":
        if tok.tag[0] == "W":
            return "Cw"
        return "Ci"
    if tok.pos == "NUM":
        return "C#"
    if tok.pos == "DET":
        return "Cd"
    
    if tok.pos == "ADJ":
        return "M"
    if tok.pos == "ADP":
        return "T" + _get_trigger_subtype(tok)
    
    if tok.pos == "SCONJ":
        return "T" + _get_trigger_subtype(tok)
    
    if tok.pos in {"VERB", "AUX", "MD"}:
        for child in reversed(list(tok.rights)):
            if child.dep == "punct":
                if child.text in ".,;:":
                    return "Pd"
                if child.text == "?":
                    return "P?"
                if child.text == "!":
                    return "P!"

        return "P"

    return "C"

def build_part(tok: Token) -> str:
    t = build_type_and_subtype(tok)
    r = f = e = ""
    
    if t[0] == "P":
        r = _get_predicate_roles(tok)
        f = _get_verb_features(tok)
        e = _get_entity_features(tok)
    elif t[0] == "C":
        r = _get_directional_roles(tok)
        f = _get_concept_features(tok)
        e = _get_entity_features(tok)
    elif t[0] == "M":
        r = _get_directional_roles(tok)
        f = _get_concept_features(tok)
        e = _get_entity_features(tok)
    elif t[0] != "P":
        e = _get_entity_features(tok)
    
    parts = [t, r, f, e]
    while not parts[-1]:
        parts.pop()
    return parts


## 3. PARSER

def build_unique_atom(text, *parts):
    return UniqueAtom(text, *parts)

def is_atom(edge):
    return isinstance(edge, (Atom, UniqueAtom))

def contains_atom(edge, atom):
    if isinstance(edge, (Atom, UniqueAtom)):
        return edge == atom
    
    return any(contains_atom(item, atom) for item in edge)    

def edgify(edge):
    if isinstance(edge, (Atom, UniqueAtom)):
        return edge
    return Edge([edgify(arg) for arg in edge])    


def _get_half_empty_toks(verb):
    
    is_toks = []
    
    srl_toks, dep_toks = _get_verb_args_by_srl_and_dep(verb)

    toks = sorted(set(srl_toks) | set(dep_toks))
    
    for i, tok in enumerate(toks):
        if tok in srl_toks and tok not in dep_toks:
            is_toks.append((i, tok, "dep"))
        elif tok not in srl_toks and tok in dep_toks:
            is_toks.append((i, tok, "srl"))
    return is_toks

def _build_empty_atom(label, typesubtype, roles="", morph="", ents=""):
    parts = [typesubtype, roles, morph, ents]
    while parts and parts[-1] == "":
        parts.pop()
    return build_unique_atom(label, *parts)

def _main_parse(sent, with_lemma=False, with_synset=False, debug=False):
    beta = {}
    types = {}
    atom2tok = {}
    tok2atom = {}
    trace = []
    hist = {}
    
    token_seq = [item[1] for item in make_token_sequence(sent)]
    #print(token_seq)
    #token_seq[1], token_seq[-2] = token_seq[-2], token_seq[1]
    #print(token_seq)

    for child in token_seq:
        parts = build_part(child)

        label = child.lemma if with_lemma else child.text.lower()
        if with_synset and child.synset:
            label = child.synset

        atom = build_unique_atom(label, *parts)
        atom2tok[atom] = child
        tok2atom[child] = atom
        beta[child] = atom
        hist[child] = [atom]
        types[child] = atom.type()[0]

    predicates = {}
    conjs = {}
    cases = set()

    for child in token_seq:
        rel = child.dep
        parent = child.head
        
        if debug:
            trace.append({"1. token": (child, rel, parent)})
            

        if child not in beta:
            warnings.warn(f"{child} is probably punct.")
        
        child_edge = beta[child]
        child_type = types[child]
        parent_edge = beta.get(parent, build_unique_atom("?"))
        parent_type = types.get(parent, "")
        
        
        if debug:
            trace[-1]["2. parent_edge"] = parent_edge
            trace[-1]["3. child_edge"] = child_edge
            
        if ((rel in {"nsubj", "nsubjpass", "dobj", "dative", "oprd",
                     "acomp", "attr", "expl", "csubj", "csubjpass",
                     "parataxis", "intj"}) or 
            (rel in {"ccomp", "xcomp", "advcl"} and parent.dep not in {"acomp", "advmod", "attr"}) or
            (parent.pos in {"VERB", "AUX", "MD"} and rel in {"advmod", "prep", "npadvmod"} and not alpha_condition(_get_conj_closure(parent)))):

            if child_type == "P" and child not in predicates:
                predicates[child] = beta[child] = child_edge = [child_edge]  

            if parent in predicates:
                beta[parent] = parent_edge + [child_edge]
            else:
                beta[parent] = [parent_edge] + [child_edge]
            predicates[parent] = beta[parent]
                
        elif rel in {"ccomp", "xcomp", "advcl"} and parent.dep == "acomp":
            empty = _build_empty_atom("+", "Br", "am", ents=_get_entity_features(parent, child))
            if child_type == "P" and child not in predicates:
                predicates[child] = beta[child] = child_edge = [child_edge]
            beta[parent] = [empty, parent_edge, child_edge]
            # beta[parent] = Edge([build_unique_atom(":", "J"), parent_edge, child_edge])
        elif rel in {"ccomp", "xcomp", "advcl"} and parent.dep == "advmod":
            if child_type == "P" and child not in predicates:
                predicates[child] = beta[child] = child_edge = [child_edge]
            beta[parent] = [parent_edge, child_edge]
            #beta[parent] = Edge([build_unique_atom("+", "Br.ma"), parent_edge, child_edge])
        elif rel in {"ccomp", "xcomp", "advcl"} and parent.dep == "attr":
            empty = _build_empty_atom("+", "Br", "am", ents=_get_entity_features(parent, child))
            if child_type == "P" and child not in predicates:
                predicates[child] = beta[child] = child_edge = [child_edge]
            beta[parent] = [empty, parent_edge, child_edge]

        elif rel == "prep":
            if parent.dep == child.dep:
                # special case
                empty = _build_empty_atom(":", "J", ents=_get_entity_features(parent, child))
                if is_atom(child_edge):
                    beta[parent] = [empty, parent_edge, child_edge]
                else:
                    beta[parent] = [empty, parent_edge] + child_edge
            else:
                if is_atom(child_edge):
                    beta[parent] = [parent_edge] + [child_edge]
                else:
                    beta[parent] = [child_edge[0]] + [parent_edge] + child_edge[1:]
                
        elif rel == "agent":
            if is_atom(parent_edge):
                beta[parent] = [parent_edge] + [child_edge]
            else:
                if parent in predicates:
                    beta[parent] = parent_edge + [child_edge]
                else:
                    beta[parent] = [parent_edge, child_edge]
            predicates[parent] = beta[parent]
            
        elif rel == "mark":
            beta[parent] = [child_edge, parent_edge]
            
        elif rel in {"pobj", "pcomp"}:
            beta[parent] = [parent_edge, child_edge]
        
        elif rel in {"amod"} and parent.dep == "prep":  
            if child.i > parent.i:
                beta[parent] = [parent_edge, child_edge] # as fast as possible
            else:
                #beta[parent] = Edge([parent_edge, child_edge])
                beta[parent] = [child_edge, parent_edge]
            
        elif rel in {"npadvmod"} and parent.dep in {"mark", "prep"}:
            beta[parent] = [child_edge, parent_edge]
            
            
        elif rel in {"det", "predet", "amod", "advmod", "nmod", "nummod", "npadvmod", "quantmod"}:
            if parent_type == child_type == "C":
                if parent.i < child.i:
                    empty = _build_empty_atom("+", "B", "ma", ents=_get_entity_features(parent, child))
                    beta[parent] = [empty, parent_edge, child_edge]
                else:
                    empty = _build_empty_atom("+", "B", "am", ents=_get_entity_features(parent, child))
                    beta[parent] = [empty, child_edge, parent_edge]
            elif parent_type == "C":
                beta[parent] = [child_edge, parent_edge]
            elif child_type == "C":   
                beta[parent] = [parent_edge, child_edge]
            else:
                if child.i < parent.i:
                    beta[parent] = [child_edge, parent_edge]
                else:
                    beta[parent] = [parent_edge, child_edge]
                
            
        elif rel in {"aux", "auxpass"}:
            beta[parent] = [child_edge, parent_edge]
            
        elif rel == "prt":
            beta[parent] = [child_edge, parent_edge]
            # beta[parent] = Edge([build_unique_atom(":", "J"), parent_edge, child_edge])
            
        elif rel == "neg":
            beta[parent] = [child_edge, parent_edge]
            
        elif rel == "case":
            beta[parent] = [child_edge, parent_edge]
            cases.add(parent)
            
        elif rel == "poss":
            if child in cases:
                beta[parent] = child_edge + [parent_edge]
            else:
                beta[parent] = [child_edge, parent_edge]
            
        elif rel == "appos":
            empty = _build_empty_atom("+", "Ba", "ma", morph=_get_appos_features(child), ents=_get_entity_features(parent, child))
            beta[parent] = [empty, parent_edge, child_edge]
            
        elif rel in "compound":
            empty = _build_empty_atom("+", "B", "am", ents=_get_entity_features(parent, child))
            beta[parent] = [empty, child_edge, parent_edge]
            
        elif rel in {"acl", "relcl"}:
            if child not in predicates:
                predicates[child] = beta[child] = child_edge = [child_edge]
            empty = _build_empty_atom("+", "Jr", "ma", ents=_get_entity_features(parent, child))
            beta[parent] = [empty, parent_edge, child_edge]

        elif rel == "conj":
            # check if child is an atom predicate (no args)
            # if is_atom(child_edge) and types.get(child) == "P":
            #     child_edge = predicates[child] = beta[child] = [child_edge]
            if child_type == "P" and child not in predicates and child not in conjs:
                predicates[child] = beta[child] = child_edge = [child_edge]              
            if parent_type == "P" and parent not in predicates and parent not in conjs:
                predicates[parent] = beta[parent] = parent_edge = [parent_edge]              

            if parent in conjs and child in conjs:                
                if parent.i < child.i:
                    beta[parent] = parent_edge + [child_edge]
                else:
                    beta[parent] = child_edge + [parent_edge]
                    
            elif parent in conjs and child not in conjs:
                if child.i < parent.i:
                    beta[parent] = [parent_edge[0]] + [child_edge] + parent_edge[1:]
                else:
                    beta[parent] = parent_edge + [child_edge]
                conjs[child] = child_edge

            elif parent not in conjs and child in conjs:
                if parent.i < child.i:
                    beta[parent] = [child_edge[0]] + [parent_edge] + list(child_edge[1:])
                else:
                    beta[parent] = child_edge[0] + [parent_edge]
                conjs[parent] = parent_edge
                    
            elif parent not in conjs and child not in conjs:
                empty = _build_empty_atom(":", "J", ents=_get_entity_features(parent, child))
                beta[parent] = [empty, parent_edge, child_edge]
                conjs[parent] = parent_edge
                conjs[child] = child_edge
                
        elif rel == "cc":
            if parent_type == "P" and parent not in predicates and parent not in conjs:
                predicates[parent] = beta[parent] = parent_edge = [parent_edge]              

            beta[parent] = [child_edge] + [parent_edge]
            conjs[parent] = parent_edge

        elif rel == "preconj":
            beta[parent] = [child_edge] + [parent_edge]
            
        elif rel in {"dep", "meta"}:
            if not parent_type == "P":
                empty = _build_empty_atom(":", "J", ents=_get_entity_features(parent, child))
                beta[parent] = [empty, parent_edge, child_edge]
            
        if parent in hist and parent in beta:
            hist[parent].append(beta[parent])
            
        if debug:
            trace[-1]["4. new_edge"] = beta[parent]
            
    # process relation edge with argument not connected by dependency (hidden)
    found_hidden_dep = False
    for verb in predicates:  # predicates are ordered by their traversal 
        half_empty_toks = _get_half_empty_toks(verb)

        if not half_empty_toks:
            continue

        for i, tok, kind in half_empty_toks:
            # find token edge
            if verb not in tok2atom:
                warnings.warn(f"Hyperedge parser: verb {verb} hasn't dedicated hyperedge!")
                continue
            verb_atom = tok2atom[verb]

            if tok not in hist:
                warnings.warn(f"Hyperedge parser: token {tok} hasn't dedicated hyperedge!")
                continue
            for tok_edge in reversed(hist[tok]):
                if not contains_atom(tok_edge, verb_atom):
                    break
                    
            # find verb edge
            verb_edge = predicates[verb] # beta[verb]

            if is_atom(verb_edge):                
                warnings.warn(f"Hyperedge parser: hyperedge {verb_edge} is atom!")
                #verb_edge = beta[verb] = predicates[verb] = [verb_edge]
                continue
                        
            found_hidden_dep = True
            if kind == "dep":                
                verb_edge.insert(i + 1, tok_edge)
            elif kind == "srl":
                pass
    
    # Edgify
    for tok in beta:
        beta[tok] = edgify(beta[tok])

    parse_result = {"main_edge": beta[sent.root],
                    #"hidden_dep": found_hidden_dep,
                    "atom2token": atom2tok,
                    "beta": beta,
                    #"predicates": predicates
                   }
    if debug:
        parse_result.update({"debug": trace})
    return parse_result


COREF_ROLES = {"PROPN": "p",
               "PRON":  "r", 
               "NOUN":  "c",}

def _aux_parse(doc_or_sent, with_lemma=False, with_synset=False):
    
    def replace_edge(edge, src, tgt):


        # if isinstance(edge, type(src)):
        #     if str(edge) == str(src): # TODO: Ovo nije dobro. Valjda će se popravit kada implementiram svoju klasu
        #         return tgt
        # elif is_atom(edge):
        #     return edge
        
        if isinstance(edge, type(src)) and edge == src:
            return tgt
        elif is_atom(edge):
            return edge

        edges = []
        for subedge in edge:
            e = replace_edge(subedge, src, tgt)
            edges.append(e)
        return Edge(edges)

    def find_span_root(span):
        # spacy's root of the span
        if span.root in beta:
            return span.root
        # first token which has an edge and head is not in span 
        for tok in span:
            if tok in beta and tok.head not in span:
                return tok
        # first token which has an edge 
        for tok in span:
            if tok in beta:
                return tok
        assert False

    def _get_all_atoms(edge):
        atoms = []
        def recursion(edge):
            if not is_atom(edge):
                for subedge in edge:
                    recursion(subedge)
            else:
                atoms.append(edge)
        return atoms

    def minimum_spanning_edge(edge, span):
        span_tokens = {tok for tok in span if tok in atom2token.values()}
        root_edge = edge
        stack = [root_edge]
        while stack:
            edge = stack.pop()
            edge_tokens = {atom2token[a] for a in _get_all_atoms(edge) if a in atom2token}
            if span_tokens == edge_tokens:
                return edge
            if not is_atom(edge):
                stack += list(reversed(edge))
        return root_edge                

    sent2edge = {}
    atom2token = {}
    beta = {}
    edges = []

    if isinstance(doc_or_sent, Doc):
        sentences = doc_or_sent.sents
        coreferences = doc_or_sent.coref
    else:
        sentences = [doc_or_sent]
        coreferences = {}
        for i, spans in doc_or_sent.coref.items():
            main, refs = None, []
            for span in spans:
                if span.label.startswith("MAIN"):
                    main = span
                elif span.label.startswith("REF"):
                    refs.append(span)
            if main and refs:
                coreferences[i]=(main, ) + tuple(refs)

    for sent in sentences:
        
        res = _main_parse(sent, with_lemma=with_lemma, with_synset=with_synset)
        atom2token.update(res["atom2token"])
        beta.update(res["beta"])
        sent2edge[sent] = beta[sent.root]

    
    for spans in coreferences.values():
        main, *refs = spans
        main_root = find_span_root(main)
        main_edge = beta[main_root]

        if not is_atom(main_edge) and main_edge[0].type() in ("J", "Br", "Bp", "Jr"):
            main_edge = minimum_spanning_edge(main_edge, main)

        for ref in refs:
            # if ref.label == "REF":
                if str(ref).lower() == str(main).lower():
                    continue
                ref_root = find_span_root(ref)
                ref_edge = beta[ref_root]

                if not is_atom(ref_edge) and ref_edge[0].type() in ("J", "Br", "Bp", "Jr"):
                    ref_edge = minimum_spanning_edge(ref_edge, ref)

                roles = COREF_ROLES.get(ref_root.pos, "?") + COREF_ROLES.get(main_root.pos, "?")
                coref_connector = build_unique_atom("+", "Jc", "rm", roles)
                coref_edge = Edge([coref_connector, ref_edge, main_edge])
                
                sent = ref.sent
                sent_edge = sent2edge[sent]
                sent2edge[sent] = replace_edge(sent_edge, ref_edge, coref_edge)

    #sent2edge = {sent: edgify(edge) for sent, edge in sent2edge.items()}
    return {"sent2edge": sent2edge,
            "atom2token": atom2token,
            "beta": beta}

def parse(doc_or_sent, with_lemma=False, with_synset=False):
    data = _aux_parse(doc_or_sent, with_lemma=with_lemma, with_synset=with_synset)
    if isinstance(doc_or_sent, Doc):
        graph = list(data["sent2edge"].values())
        return graph
    else:
        edge = data["sent2edge"][doc_or_sent]
        return edge



    
