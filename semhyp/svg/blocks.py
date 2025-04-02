from .elements import SVGElemArc, SVGElemText, SVGElemRectText, SVGElemLine, SVGElemCurvedLine
from ..text import ANNOS, TOK_ANNOS, SPAN_ANNOS
from ..hyper.hyperedge import Atom, UniqueAtom, Hyperedge 

class SVGBlockSent():

    def __init__(self, owner, sent):
        self.owner = owner
        self._content = []

        self.value = str(sent)
        self.width = len(self.value) * owner.font_width
        self.height = owner.font_height

        self._content.append(SVGElemText(x=0, y=owner.font_height, value=str(sent), style={"font-weight": "bold"}))

    def generate(self, dx=0, dy=0):
        content = ""
        for elem in self._content:
            content += elem.generate(dx, dy) + "\n"
        return content


class SVGBlockSentAnno():

    @staticmethod
    def _sent_to_table(sent, annos):
        NONE = " "
        OTHER = " "

        table = [[] for _ in sent]
        table_annos = []
        
        for anno in annos:
            values = [getattr(tok, anno) for tok in sent]

            if all(isinstance(val, str) and 
                   hasattr(val, "is_other") and 
                   val.is_other() 
                   for val in values):
                continue

            if all(isinstance(val, dict) for val in values):
                size = max(len(val) for val in values)
                table_annos += [anno] * size
            else:
                table_annos.append(anno)


            for column, val in zip(table, values):
                if isinstance(val, str):
                    if hasattr(val, "is_other"):
                        column.append(val if not val.is_other() else OTHER)
                    else:
                        column.append(val)
                elif val is None:
                    column.append(NONE)
                elif isinstance(val, dict):
                    if val:
                        for v in val.values():
                            if hasattr(v, "is_other"):
                                column.append(v if not v.is_other() else OTHER)
                    else:
                        column.append(OTHER)
        return table, table_annos
    
    @staticmethod
    def _sent_to_table_with_spans(sent, annos):
        span_annos = SPAN_ANNOS
        
        NONE = " "

        table = [[] for _ in sent]
        table_annos = []
        for anno in annos:
            if anno not in span_annos:
                for tok, column in zip(sent, table):
                    val = getattr(tok, anno)
                    if isinstance(val, str):
                        column.append(val)
                    elif val is None:
                        column.append(NONE)
                table_annos.append(anno)
            else:
                items = getattr(sent, anno)
                if not items:
                    continue
                
                    

                values = []
                if isinstance(items, list):
                    for cluster in items:
                        values.extend(cluster.spans)
                if isinstance(items, tuple):
                    values.append(items)
                elif isinstance(items, dict):
                    values.extend(items.values())
                
                for spans in values:
                    for column in table:
                        column.append(None)
                    for span in spans:
                        column = table[span[0].i_by_sent]
                        column[-1] = (span.label, span.end-span.start)
                    table_annos.append(anno)

        return table, table_annos

    def __init__(self, owner, sent, show_spans=True, annos=None, style=None):
        self.owner = owner
        self.style = style
        self._content = []

        if annos is None:
            annos = ANNOS
        
        table, table_annos = self._sent_to_table_with_spans(sent, annos) if show_spans else self._sent_to_table(sent, annos)
        
        # calc positions and sizes
        column_widths = [max(len(val) if isinstance(val, str) else len(val[0]) for val in column if val is not None) for column in table]
        column_x_centers = [(sum(column_widths[:i])) * owner.font_width + (column_widths[i] * owner.font_width) // 2 
                                  for i in range(len(column_widths))]
        column_x_lefts = [(sum(column_widths[:i])) * owner.font_width for i in range(len(column_widths))]
        column_w_lefts = [column_widths[i] * owner.font_width for i in range(len(column_widths))]

        self.width = sum(column_widths) * owner.font_width


        # draw dependency arcs
        self.dep_anno_border_height = 0
        for tok in sent:
            dest =  tok.i_by_sent
            src = tok.head.i_by_sent
            x1, x2 = column_x_centers[src], column_x_centers[dest]
            
            elem = SVGElemArc(x1, x2, 0, owner.offset, tok.dep)
            self._content.append(elem)
            self.dep_anno_border_height = max(elem.get_height(owner.font_height), self.dep_anno_border_height)

        self.height = self.dep_anno_border_height + max(len(column) for column in table) * owner.font_height

        for elem in self._content:
            elem.reset(y=self.dep_anno_border_height)

        # draw text blocks
        for i, column in enumerate(table):
            for j, value in enumerate(column):
                if isinstance(value, str):
                    self._content.append(SVGElemText(x=column_x_centers[i], 
                                                    y= self.dep_anno_border_height + (j + 1) * owner.font_height, 
                                                    value=value,
                                                    cls=f"center-text {table_annos[j]}"
                                                    ))
                elif isinstance(value, tuple):
                    value, size = value
                    w = sum(column_w_lefts[k] for k in range(i, i + size))
                    self._content.append(SVGElemRectText(x=column_x_lefts[i], 
                                                         y=self.dep_anno_border_height + (j + 1) * owner.font_height, 
                                                         w=w,
                                                         h=owner.font_height,
                                                         value=value,
                                                         text_cls=f"center-text {table_annos[j]}"))

    def generate(self, dx=0, dy=0):
        content = ""
        for elem in self._content:
            content += elem.generate(dx, dy) + "\n"
        return content


class SVGBlockHyperedge():

    @staticmethod    
    def _hypergraph_to_graph(edge):

        def is_atom(item):
            if isinstance(item, (Atom, UniqueAtom)):
                return True
            elif isinstance(item, Hyperedge):
                return False
            else:
                raise Exception(f"{item} should be atom or hyperedge")

        def store2dict(nodes, item):
            if isinstance(item, Atom):
                item = Atom(*item)
            if item in nodes:
                return nodes[item]
            nodes[item] = len(nodes)
            return nodes[item]

        def edge_role(edge):
            if is_atom(edge):
                roles = edge.roles()
                if roles:
                    return ".".join(roles)
                return ""

            et = edge.type()
            if et[0] == "P":
                return edge_role(edge[-1])

            er = edge.argroles()
            if et and er:
                return et + "." + er
            if et:
                return et
            if er:
                return "." + er
            return ""

        data = {"nodes": {},
                "links": [],
                "crosslinks": []}
        
        nodes = {}
        stack = [edge]
        visited = set()
        while stack:
            parent = stack.pop(0)  # BFS - use deque
            if parent.is_atom():
                parent_i = store2dict(nodes, parent)
                continue
            
            parent_i = store2dict(nodes, parent[0])
            for child in parent[1:]:
                if not is_atom(child) and child[0].type()[0] in ("J", "B"):
                    child_i = store2dict(nodes, child[0])
                    rel = edge_role(child[0])
                    stack += [child]
                elif child.type()[0] in ("C", "P", "M") or is_atom(child):
                    child_i = store2dict(nodes, child)
                    rel = edge_role(child)
                else:
                    child_i = store2dict(nodes, child[0])
                    rel = edge_role(child[0])
                    stack += [child]

                # triples from graph with repeated child store in extra links
                if child_i not in visited:
                    data["links"].append((parent_i, child_i, rel))
                    visited.add(child_i)
                else:
                    data["crosslinks"].append((parent_i, child_i, rel))

        # remove extra links which are in links
        if data["crosslinks"]:
            links_pairs = {(parent_i, child_i) 
                           for parent_i, child_i, _ in 
                           data["links"]}
            data["crosslinks"] = {(parent_i, child_i, rel)
                                  for (parent_i, child_i, rel) in data["crosslinks"]
                                  if (parent_i, child_i) not in links_pairs}    

        for node, i in nodes.items():
            data["nodes"][i] = {"text": str(node.simplify()),
                                "type": node.type()[0]}

        root_role = edge_role(edge if is_atom(edge) else edge[0])
        data["links"].append((0, 0, root_role))

        return data

    @staticmethod
    def _put_sizes_in_graph(graph, sizes):
        children = {}
        parents = {}

        root_links = []
        for parent_i, child_i, rel in graph["links"]:
            if parent_i == child_i:
                root_links.append((rel, parent_i))
            else:
                children[parent_i] = children.get(parent_i, []) + [(rel, child_i)]
                parents[child_i] = (rel, parent_i)
        root_is = set(graph["nodes"]) - set(parents)


        def _traverse(parent_i, offx=0, depth=0):
            parent = graph["nodes"][parent_i]

            parent_rel, _ = parents.get(parent_i, ("", parent_i))

            text_w = len(parent["text"]) * sizes["node_font_width"]
            rel_w = len(parent_rel) * sizes["link_font_width"]
            parent_w = max(text_w, rel_w)

            children_occ = 0
            children_xy = []
            children_rels = []
            for child_rel, child_i in children.get(parent_i, []):
                child = _traverse(child_i, children_occ + offx, depth + 1)
                children_occ += child["occupy"] + sizes["node_font_width"]
                children_xy.append((child["x"] + child["w"] // 2, child["y"]))
                children_rels.append(child_rel)

            parent_occ = max(children_occ, parent_w)
            
            parent.update({"occupy": parent_occ,
                           "x": offx + (parent_occ - text_w) // 2,
                           "y": 2 * sizes["link_font_height"] + (sizes["node_font_height"] + sizes["node_span"]) * depth,
                           "w": text_w,
                           "h": sizes["node_font_height"],})
            
            #graph["nodes"][parent_i].update()

            # primary links
            x1, y1 = (parent["x"], parent["y"])
            parent_w_part = parent["w"] // (len(children_xy) + 1)
            for (x2, y2), rel in zip(children_xy, children_rels):
                x1 += parent_w_part
                graph["links"].append({"x1": x1, 
                                       "y1": y1, 
                                       "x2": x2, 
                                       "y2": y2 - parent["h"] * 0.75, 
                                       "end_text": rel})

            return parent

        graph["links"].clear()
        for root_i in root_is:
            _traverse(root_i, offx=10)

        # root arc
        for r, i in root_links:
            root = graph["nodes"][i]

            x = root["x"] + root["w"] // 2
            y = root["y"]
            graph["links"].append({"x1": x, "y1": y - sizes["node_font_height"] * 0.75,
                                   "x2": x, "y2": y - sizes["node_font_height"] * 0.75,
                                   "end_text": r})

        # secondary links
        crosslinks = []
        for p, c, r in graph["crosslinks"]:
            parent = graph["nodes"][p]
            child = graph["nodes"][c]

            x1 = parent["x"] + parent["w"] // 2
            y1 = parent["y"]
            x2 = child["x"] + child["w"] // 2
            y2 = child["y"] + child["h"] * 0.25
            crosslinks.append({"x1": x1, "y1": y1, 
                               "x2": x2, "y2": y2, 
                               "end_text": r})
        graph["crosslinks"] = crosslinks
        graph["nodes"] = list(graph["nodes"].values())

        # tilt everything

        tilt_x = min(node["x"] for node in graph["nodes"])
        for node in graph["nodes"]:
            node["x"] -= tilt_x
        for link in graph["links"]:
            link["x1"] -= tilt_x
            link["x2"] -= tilt_x
        for link in graph["crosslinks"]:
            link["x1"] -= tilt_x
            link["x2"] -= tilt_x
        return graph

    def __init__(self, owner, edge, style=None):
        self.owner = owner
        self.style = style
        self.hyperedge = edge

        graph = self._hypergraph_to_graph(edge)

        sizes = {"node_font_width": self.owner.font_width,
                 "node_font_height": self.owner.font_height,
                 "link_font_width": self.owner.font_width * 0.75,
                 "link_font_height": self.owner.font_height * 0.75,
                 "node_span": self.owner.font_height * 2}
        
        graph = self._put_sizes_in_graph(graph, sizes)

        self._content = []
        self.width = 0
        self.height = 0
        for link in graph["links"]:
            self._content.append(SVGElemLine(x1=link["x1"], y1=link["y1"], 
                                             x2=link["x2"], y2=link["y2"],
                                             font_height=sizes["link_font_height"],                                             
                                             end_value=link["end_text"]))

        for link in graph["crosslinks"]:
            self._content.append(SVGElemCurvedLine(x1=link["x1"], y1=link["y1"], 
                                                   x2=link["x2"], y2=link["y2"],
                                                   font_height=sizes["link_font_height"],
                                                   end_value=link["end_text"]))
            x, y, w, h = self._content[-1].get_boundary_box()
            self.height = max(self.height, y + h)

        for node in graph["nodes"]:
            self._content.append(SVGElemRectText(x=node["x"], 
                                                 y=node["y"], 
                                                 w=node["w"], 
                                                 h=node["h"], 
                                                 value=node["text"], 
                                                 text_cls="center-text", 
                                                 rect_cls="type" + node["type"]))
            
            self.width = max(self.width, node["x"] + node["w"])
            self.height = max(self.height, node["y"] + node["h"])


    def generate(self, dx=0, dy=0):
        content = ""
        for elem in self._content:
            content += elem.generate(dx, dy) + "\n"
        return content

