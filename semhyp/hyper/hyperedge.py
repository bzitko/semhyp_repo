from collections import namedtuple


atom_part_encoding = {
    '%': '%25',
    '/': '%2f',
    ' ': '%20',
    '(': '%28',
    ')': '%29',
    '.': '%2e',
    '*': '%2a',
    '&': '%26',
    '@': '%40',
    '\n': '%0a',
    '\r': '%0d',
}

def hatom(source):
    source = source.strip()
    label, *rest = source.split("/")
    if not rest:
        return Atom(label)
    
    parts = rest.pop().split(".")
    return Atom(label, *parts)


def hedge(source):
    print(source)
    source = source.replace("(", " ( ").replace(")", " ) ").strip()
    source = source.split()
    
    for i in range(len(source)):
        if source[i] not in "()":
            source[i] = hatom(source[i])

    stack = []
    for item in source:
        if item == ")":
            queue = []
            while stack[-1] != "(":
                queue.append(stack.pop())
            stack[-1] = Hyperedge(queue[::-1])
        else:
            stack.append(item)

    return stack.pop()


class Hyperedge(tuple):
    
    def __new__(cls, edges):
        return super(Hyperedge, cls).__new__(cls, tuple(edges))

    def type(self):
        """Returns the type of this edge as a string.
        Type inference is performed.
        """
        ptype = self[0].type()
        if ptype[0] == 'P':
            outter_type = 'R'
        elif ptype[0] == 'M':
            return self[1].type()
        elif ptype[0] == 'T':
            outter_type = 'S'
        elif ptype[0] == 'B':
            outter_type = 'C'
        elif ptype[0] == 'J':
            return self[1].mtype()
        else:
            raise RuntimeError('Edge is malformed, type cannot be determined: {}'.format(str(self)))

        return '{}{}'.format(outter_type, ptype[1:])
    
    def mtype(self):
        return self.type()[0]

    def argroles(self):
        """Returns the argument roles string of the edge, if it exists.
        Otherwise returns empty string.
        
        Argument roles can be return for the entire edge that they apply to,
        which can be a relation (R) or a concept (C). For example:

        ((not/M is/P.sc) bob/C sad/C) has argument roles "sc",
        (of/B.ma city/C berlin/C) has argument roles "ma".

        Argument roles can also be returned for the connectors that define 
        the outer edge, which can be of type predicate (P) or builder (B). For
        example:

        (not/M is/P.sc) has argument roles "sc",
        of/B.ma has argument roles "ma".
        """
        et = self.mtype()
        if et in {'R', 'C'} and self[0].mtype() in {'B', 'P'}:
            return self[0].argroles()
        if et not in {'B', 'P'}:
            return None
                
        return self[-1].argroles()
        
    def is_atom(self):
        return False
    
    def atoms(self):
        atom_set = set()
        for item in self:
            for atom in item.atoms():
                atom_set.add(atom)
        return atom_set    
    
    def subedges(self):
        edges = {self}
        for item in self:
            edges = edges.union(item.subedges())
        return edges

    def to_str(self):
        return "(" + " ".join(edge.to_str() for edge in self) + ")"

    def __str__(self):
        return self.to_str()

    def __repr__(self):
        return self.to_str()
    
    def roots(self):
        return Hyperedge(edge.roots() for edge in self)
    
    def simplify(self, with_subtypes=False, with_roles=False, with_morph=False, with_entity=False):
        return Hyperedge(edge.simplify(with_subtypes, with_roles, with_morph, with_entity) for edge in self)

    def reduce(self, with_srl=True, with_coref=True, with_ner=True):
        fn_reduce = lambda edge: Hyperedge.reduce(edge, with_srl=with_srl, with_coref=with_coref, with_ner=with_ner)

        if self.is_atom():
            if not with_ner and self.entity():
                return Atom(self.label(), self.type(), self.roles(), self.morph(), None)
            if not with_srl:
                roles = self.roles()
                if self.mtype() == "P" and roles:
                    roles = roles[0].replace("-", "")
                    return Atom(self.label(), self.type(), roles, self.morph(), self.entity())
            return self
        
        elif not with_coref and self[0].type() == "Jc":  # coreference
            return self[1]
        elif not with_srl and self[0].mtype() == "P" and "-" in self[0].argroles()[0]:  # srl with implicit argument
            return Hyperedge([fn_reduce(self[0])] + [fn_reduce(edge) for r, edge in zip(self[0].argroles()[0], self[1:]) if r != "-"])
        
        return Hyperedge(fn_reduce(edge) for edge in self)


def str2part(s):
    for k, v in atom_part_encoding.items():
        s = s.replace(k, v)
    return s

def part2str(part):
    for k, v in atom_part_encoding.items():
        part = part.replace(v, k)
    return part    


def build_atom_part(part):
    if part is None:
        return None

    if isinstance(part, str) and ":" not in part:
        return (str2part(part), )

    if isinstance(part, str) and ":" in part:
        part = part.split(":")

    if isinstance(part, (tuple, list)) and all(isinstance(p, str) for p in part):
        return tuple(str2part(p) for p in part)
    
    if isinstance(part, dict) and all(isinstance(k, str) and isinstance(v, str) for k, v in part.items()):
        return namedtuple("Part", list(part))(*(str2part(p) for p in part.values()))

    return str(part)


class Atom(Hyperedge):

    def __new__(cls, label, type=None, roles=None, morph=None, entity=None):
        return super(Hyperedge, cls).__new__(cls, (str2part(label), build_atom_part(type), build_atom_part(roles), build_atom_part(morph), build_atom_part(entity)))

    def label(self):
        return part2str(self[0])

    def type(self):
        return part2str(self[1][0])

    def mtype(self):
        return part2str(self[1][0][0])
    
    def is_atom(self):
        return True

    @staticmethod
    def _part_getter(part, i=None):
        if part is None:
            return part
        if i is None:
            if isinstance(part, str):
                return part2str(part)
            if isinstance(type, (tuple, list)):
                return tuple(part2str(p) for p in part)
            if isinstance(type, dict):
                return {k: part2str(v) for k, v in part.items()}
            return part
        if isinstance(i, str):
            return part2str(getattr(part, i))
        return part2str(part[i])

    def roles(self, i=None):
        return self._part_getter(self[2], i)

    def morph(self, i=None):
        return self._part_getter(self[3], i)

    def entity(self, i=None):
        return self._part_getter(self[4], i)
    
    def argroles(self):
        return self.roles()
    
    def roots(self):
        return self.__class__(self.label())
    
    def simplify(self, with_subtypes=False, with_roles=False, with_morph=False, with_entity=False):
        label = self.label()
        type = self.type() if with_subtypes else self.mtype()
        roles = self.roles() if with_roles else None
        morph = self.morph() if with_morph else None
        entity = self.entity() if with_entity else None
        return self.__class__(label, type, roles, morph, entity)
    
    def subedges(self):
        return {self}
    
    def atoms(self):
        return {self}

    def to_str(self):
        txt = part2str(self[0])

        rest = []
        for part in self[1:]:
            if part is None:
                rest.append("")
            elif isinstance(part, tuple):
                rest.append(":".join(part2str(p) for p in part))
            else:
                rest.append(part2str(part))
        
        while rest and rest[-1] == "":
            rest.pop()

        if not rest:
            return txt

        return txt + "/" + ".".join(rest)


class UniqueAtom(Atom):

    def __hash__(self):
        return id(self)

    def __eq__(self, other):
        return id(self) == id(other) and type(self) == type(other)