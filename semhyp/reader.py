import re

from .text import Doc, Span

from collections import namedtuple

ColumnInfo = namedtuple("ColumnInfo", "i, name, type")
COLUMN_DATA = {"sent_i": (0, "sent_i", int),
               "tok_i":  (1, "tok_i", int),
               "word":  (2, "word", str),
               "space": (3, "space", str),
               "lemma": (4, "lemma", str),
               "pos":    (5, "pos", str),
               "tag":   (6, "tag", str),
               "dep":   (7, "dep", str),
               "head":  (8, "head.i", int),
               "ner":    (9, "ent", str),
               "roleset": (10, "roleset", str),
               "srl":     (11, "srl", str),
               "coref":   (12, "coref", str),
               "synset":  (13, "synset", str),}

COLUMN_DATA = {col: ColumnInfo(*item) for col, item in COLUMN_DATA.items()}

REGEXS = {"ner": r"[BI]-(CARDINAL|DATE|EVENT|FAC|GPE|LANGUAGE|LAW|LOC|MONEY|NORP|ORDINAL|ORG|PERCENT|PERSON|PRODUCT|QUANTITY|TIME|WORK_OF_ART)",
          "roleset": r"\w+\.\d\d",
          "srl": r"[BI](-[RC])?-(ARG0|ARG1|ARG2|ARG3|ARG4|ARG5|ARG6|ARGM-ADJ|ARGM-ADV|ARGM-CAU|ARGM-COM|ARGM-DIR|ARGM-DIS|ARGM-DSP|ARGM-EXT|ARGM-GOL|ARGM-LOC|ARGM-MNR|ARGM-MOD|ARGM-PNC|ARGM-PRD|ARGM-PRP|ARGM-REC|ARGM-TMP|V)",
          "coref": r"[BI]-(MAIN|REF)\d+",
          "synset": r"\w+\.\w\.\d\d",}

for name in REGEXS:
    REGEXS[name] = re.compile(REGEXS[name])

def _convert_rows_to_columns(rows):
    """
    Converts a list of rows into a dictionary of columns.

    Args:
        rows (list of list): The rows to convert.

    Returns:
        dict: A dictionary where keys are column indices and values are lists of column values.
    """    
    if not rows:
        return {}
    columns = {col_i: [] for col_i in range(len(rows[0]))}

    for items in rows:
        for col_i, item in enumerate(items):
            columns[col_i].append(item) 
    return columns

def _discover_column_types(columns):
    """
    Discovers the types of columns based on their content.

    Args:
        columns (dict): A dictionary where keys are column indices and values are lists of column values.

    Returns:
        dict: A dictionary where keys are column indices and values are inferred types (ner, roleset, srl, coref, synset).
    """    
    column_type_by_i = {}
    for col_i, items in columns.items():
        for item in items:
            for name, regex in REGEXS.items():
                if regex.fullmatch(item):
                    column_type_by_i[col_i] = name
                    break    
    return column_type_by_i

def _column_to_spans(sent_start, column):
    """
    Converts a column of tags into spans.

    Args:
        sent_start (int): The starting index of the sentence.
        column (list of str): The column of tags to convert.

    Returns:
        list of tuple: A list of spans, where each span is represented as a tuple (start_index, end_index, label).
    """    
    span_start = label = None
    spans = []
    column = [tag if tag.startswith(("B-", "I-")) else "O" for tag in column]
    for row_i, item in enumerate(column + ["O"]):
        if item.startswith(("B", "O")):
            if span_start is not None:
                spans.append((sent_start + span_start, sent_start + row_i, label))
            if item.startswith("B"):
                span_start = row_i
                label = item[2:]
            else:
                span_start = label = None
    return spans

def _column_to_set_ids(sent_start, column):
    """
    Converts a column of roleset or synset IDs into a list of tuples with their positions.

    Args:
        sent_start (int): The starting index of the sentence.
        column (list of str): The column of set IDs to convert.

    Returns:
        list of tuple: A list of tuples, where each tuple contains the position and the roleset or synset ID.
    """    
    set_ids = []
    for row_i, item in enumerate(column):
        if item != "-":
            set_ids.append((sent_start + row_i, item))
    return set_ids

def txt2data(txt):
    """
    Converts text data into a dictionary of columns.

    Args:
        txt (str): The text data to convert.

    Returns:
        dict: A dictionary where keys are column names and values are lists of column values.

    Example:
        >>> txt = "1\tThe\t_\t_\t_\t_\t_\t_\t_\t_\t_\t_\t_\t_\n2\tdog\t_\t_\t_\t_\t_\t_\t_\t_\t_\t_\t_\t_"
        >>> data = txt2data(txt)
        >>> print(data)
        {'sent_i': ['1', '2'], 'tok_i': ['1', '2'], 'word': ['The', 'dog'], 'space': ['_', '_'], 'lemma': ['_', '_'], 'pos': ['_', '_'], 'tag': ['_', '_'], 'dep': ['_', '_'], 'head': ['_', '_'], 'ner': ['_', '_'], 'roleset': ['_', '_'], 'srl': ['_', '_'], 'coref': ['_', '_'], 'synset': ['_', '_']}        
    """    
    data = {col: [] 
            for col in COLUMN_DATA 
            if COLUMN_DATA[col].name}

    rest_items = {} # key is sent_start, values are rows
    sent_start = 0
    tok_counter = 0
    for line in txt.split("\n"):
        if not line:
            continue
        if line[0].isnumeric():
            items = line.split()
            if items[COLUMN_DATA["tok_i"].i] == "0":
                sent_start = tok_counter
                rest_items[sent_start] = []

            data["word"].append(items[COLUMN_DATA["word"].i])
            data["space"].append("+" == items[COLUMN_DATA["space"].i])
            data["lemma"].append(items[COLUMN_DATA["lemma"].i])
            data["pos"].append(items[COLUMN_DATA["pos"].i])
            data["tag"].append(items[COLUMN_DATA["tag"].i])
            data["dep"].append(items[COLUMN_DATA["dep"].i])
            data["head"].append(sent_start + int(items[COLUMN_DATA["head"].i]))

            rest_items[sent_start].append(items[COLUMN_DATA["head"].i + 1:])
            tok_counter += 1


    for sent_start, rows in rest_items.items():
        columns = _convert_rows_to_columns(rows)
        column_type_by_i = _discover_column_types(columns)
        
        # extract data from columns
        for col_i in sorted(column_type_by_i):
            col_type = column_type_by_i[col_i]
            column = columns[col_i]
            if col_type in {"ner", "srl"}:
                spans = _column_to_spans(sent_start, column)
                data[col_type].append(spans)
            elif col_type in {"coref"}:
                spans = _column_to_spans(sent_start, column)
                data[col_type].append(spans)
            elif col_type in {"roleset", "synset"}:
                set_ids = _column_to_set_ids(sent_start, column)
                data[col_type] += set_ids

    data["sent_start"] = sorted(rest_items)
    return data

def data2doc(data):
    """
    Converts a dictionary of data into a Doc object.

    Args:
        data (dict): A dictionary where keys are column names and values are lists of column values.

    Returns:
        Doc: The content of the data as a Doc object.

    Example:
        >>> data = {
        ...     "word": ["The", "dog"],
        ...     "space": [" ", " "],
        ...     "sent_start": [0],
        ...     "ner": [[(0, 1, "O"), (1, 2, "O")]]
        ... }
        >>> doc = data2doc(data)
        >>> print(doc)
        The dog
    """    
    doc = Doc(data["word"], data["space"])

    available_token_str_annos = [anno for anno in Doc.STR_ANNOS if anno in data]
    for item in zip(doc, *[data[anno] for anno in available_token_str_annos]):
        tok, *annos = item
        for attr, val in zip(available_token_str_annos, annos):
            setattr(tok, attr, val)

    # determine sent starts
    for sent_i, sent_start in enumerate(data["sent_start"]):
        doc[sent_start]._is_sent_start = sent_i

    # put ent in doc
    doc.ent = []
    for ents in data.get("ner", []):
        for start, end, label in ents:
            ent = Span(doc, start, end, label)
            doc.ent.append(ent)
    doc.ent = tuple(doc.ent)

    # put srl in doc
    doc.srl = {}
    for srl_verb_args in data.get("srl", []):
        verb, args = None, []
        for start, end, label in srl_verb_args:
            arg = Span(doc, start, end, label)
            args.append(arg)
            if label == "V":
                verb = doc[start]
        doc.srl[verb] = tuple(args)

    # put coref in doc
    doc.coref = {}
    mains, refs = {}, {}
    for cluster in data.get("coref", []):
        for start, end, label in cluster:
            span = Span(doc, start, end, label)
            if label.startswith("MAIN"):
                i = int(label[4:])
                mains[i] = span
            elif label.startswith("REF"):
                i = int(label[3:])
                if i not in refs:
                    refs[i] = [span]
                else:
                    refs[i].append(span)

    for i, main in mains.items():
        doc.coref[i] =(main, ) + tuple(refs.get(i, []))

    # put roleset
    for i, roleset in data.get("roleset", []):
        doc[i].roleset = roleset

    # put synset
    for i, synset in data.get("synset", []):
        doc[i].synset = synset

    return doc

def read(filename, with_hypergraph=False):
    with open(filename, "r", encoding="utf8") as fp:
        txt = fp.read()
        data = txt2data(txt)
        doc = data2doc(data)
        
    if with_hypergraph:
        from .hyper import hedge
        graph = []
        for line in txt.split("\n"):
            if line.startswith("# hyperedge = "):
                line = line[14:].strip()
                graph.append(hedge(line))
        
        return doc, graph
    else:
        return doc
