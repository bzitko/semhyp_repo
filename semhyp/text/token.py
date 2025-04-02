from .span import Span
from .util import IOBTag



class Token:

    def __init__(self, doc, word, space=True):
        self.i = None
        self.doc = doc
        self._text = self.doc.vocab.put_text(word)
        self._space = space
        self._is_sent_start = False

        for anno in self.doc.STR_ANNOS + self.doc.NONE_ANNOS:
            setattr(self, "_" + anno, None)

    @property
    def i_by_sent(self):
        sent_start = self.i
        while not self.doc[sent_start].is_sent_start:
            sent_start -= 1
        return self.i - sent_start
        
    @property
    def is_sent_start(self):
        return self._is_sent_start is not False
    
    @property
    def sent_i(self):
        if self.is_sent_start:
            return self._is_sent_start
        
        i = self.i - 1
        while i >= 0:
            if self.doc[i].is_sent_start:
                return self.doc[i]._is_sent_start
            i -= 1


    # @is_sent_start.setter
    # def is_sent_start(self, value):
    #     self._is_sent_start = value

    @property
    def text(self):
        return self.doc.vocab[self._text]
    
    @property
    def space(self):
        return self._space
    
    @property
    def lemma(self):
        return self.doc.vocab[self._lemma]
    
    @lemma.setter
    def lemma(self, value):
        self._lemma = self.doc.vocab.put_text(value)

    @property
    def pos(self):
        return self.doc.vocab[self._pos]
    
    @pos.setter
    def pos(self, value):
        self._pos = self.doc.vocab.put_text(value)

    @property
    def tag(self):
        return self.doc.vocab[self._tag]
    
    @tag.setter
    def tag(self, value):
        self._tag = self.doc.vocab.put_text(value)

    @property
    def dep(self):
        return self.doc.vocab[self._dep]
    
    @dep.setter
    def dep(self, value):
        self._dep = self.doc.vocab.put_text(value)

    @property
    def head(self):
        if self._head is not None:
            return self.doc[self._head]

    @head.setter
    def head(self, value):
        if isinstance(value, int):
            self._head = value
        elif isinstance(value, Token):
            self._head = value.i

    @property
    def text_with_ws(self):
        if self._space:
            return self.text + " "
        return self.text
    
    @property
    def sent(self):
        sent_start, sent_end = 0, len(self.doc)
        i = self.i
        while i > sent_start and not self.doc[i].is_sent_start:
            i -= 1
        sent_start = i

        i = self.i + 1
        while i < sent_end and not self.doc[i].is_sent_start:
            i += 1
        sent_end = i


        return Span(self.doc, sent_start, sent_end, label=str(self.doc[sent_start].sent_i))
    
    @property 
    def lefts(self):
        for child in self.sent:
            if child.i < self.i and child.head.i == self.i:
                yield child

    @property 
    def rights(self):
        for child in self.sent:
            if child.i > self.i and child.head.i == self.i:
                yield child

    @property
    def children(self):
        yield from self.lefts
        yield from self.rights

    @property
    def conjuncts(self):
        start = self
        while start.i != start.head.i:
            if start.dep == "conj":
                start = start.head
            else:
                break
        queue = [start]
        output = [start]
        for word in queue:
            for child in word.rights:
                if child.dep == "conj":
                    output.append(child)
                    queue.append(child)
        
        return tuple([w for w in output if w.i != self.i])    

    @property
    def roles(self):
        return {}
    
    def __lt__(self, other):
        return self.i < other.i

    def __unicode__(self):
        return self.text    
    
    def __str__(self):
        return self.__unicode__()

    def __repr__(self):
        return self.__str__()


    @property
    def ent(self):
        for ent in self.sent.ent:
            if self.i == ent.start:
                return IOBTag.begin(ent.label)
            elif ent.start < self.i < ent.end:
                return IOBTag.inside(ent.label)
        return IOBTag.other()

    @property
    def srl(self):
        tok_srl = {}
        for verb, args in self.sent.srl.items():
            if self == verb:
                tok_srl[verb] = IOBTag.create("B", "V")
            else:
                for arg in args:
                    if self.i == arg.start:
                        tok_srl[verb] = IOBTag.begin(arg.label)
                        break
                    elif arg.start < self.i < arg.end:
                        tok_srl[verb] = IOBTag.inside(arg.label)
                        break
                if verb not in tok_srl:
                    tok_srl[verb] = IOBTag.other()
        return tok_srl
    
    @property
    def coref(self):
        tok_coref = {}
        for i, spans in self.sent.coref.items():
            tok_coref[i] = IOBTag.other()
            for span in spans:
                if self in span:
                    iob = "B" if self.i == span.start else "I"
                    tok_coref[i] = IOBTag.create(iob, span.label)
                    break
        return tok_coref
    
    @property
    def coref2(self):
        tok_coref = {}
        for cluster in self.sent.coref:
            tok_coref[cluster.i] = IOBTag.other()
            for span in [cluster.main] + list(cluster.refs):
                if self in span:
                    iob = "B" if self.i == span.start else "I"
                    tok_coref[cluster.i] = IOBTag.create(iob, span.label)
                    break
        return tok_coref    
    
    @property
    def roleset(self):
        return self.doc.vocab[self._roleset]
    
    @roleset.setter
    def roleset(self, value):
        self._roleset = self.doc.vocab.put_text(value)

    @property
    def synset(self):
        return self.doc.vocab[self._synset]
    
    @synset.setter
    def synset(self, value):
        self._synset = self.doc.vocab.put_text(value)
