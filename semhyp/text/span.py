from collections import namedtuple


SpanBase = namedtuple("Span", ["doc", "start", "end", "label_"])

class Span(SpanBase):

    def __new__(cls, doc, start, end, label=None):
        return super().__new__(cls, doc, start, end, doc.vocab.put_text(label))
        
    def __getitem__(self, i):
        if i < 0:
            token_i = self.end + i
        else:
            token_i = self.start + i
        if self.start <= token_i < self.end:
            return self.doc[token_i]

    @property
    def label(self):
        return self.doc.vocab[self.label_]
    
    @property
    def root(self):
        for tok in self:
            if tok.head not in self or tok.head == tok:
                return tok

    def __contains__(self, tok):
        for i in range(self.start, self.end):
            if self.doc[i] == tok:
                return True
        return False

    def __iter__(self):
        for i in range(self.start, self.end):
            yield self.doc[i]

    @property
    def text(self):
        return "".join(self.doc[i].text_with_ws for i in range(self.start, self.end)).strip()

    def __unicode__(self):
        txt = "".join(self.doc[i].text_with_ws for i in range(self.start, self.end))
        txt = txt.strip()
        if self.label:
            txt = f"{self.label}: {txt}"
        return txt

    def __str__(self):
        return self.__unicode__()

    def __repr__(self):
        return self.__str__()
    
    def contains(self, span):
        return self.start <= span.start < span.end <= self.end
    
    @property
    def sent(self):
        return self.root.sent

    @property
    def ent(self):
        ents = []
        for ent in self.doc.ent:
            if  self.start <= ent.start < ent.end <= self.end:
                ents.append(ent)
        return tuple(ents)

    @property
    def srl(self):
        srl_verb_args = {}
        for verb, args in self.doc.srl.items():
            if verb in self and all(self.contains(arg) for arg in args):
                srl_verb_args[verb] = args
        return srl_verb_args


    @property
    def coref(self):
        coref_dict = {}
        for i, doc_spans in self.doc.coref.items():
            sent_spans = tuple(span for span in doc_spans if self.contains(span))
            if sent_spans:
                coref_dict[i] = sent_spans
        return coref_dict
