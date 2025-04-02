import html

class SVGElemBase():

    def __init__(self, cls=None, style=None):
        self.cls = cls
        self.style = style

    def generate_class(self, cls=None):
        if not cls and not self.cls:
            return ""    
        cls = cls or self.cls
        return f' class="{cls}" '

    def generate_style(self):
        if not self.style:
            return ""
        svg = []
        for attr, val in self.style.items():
            svg.append(f"{attr}: {val}")
        return ' style="' + "; ".join(svg) + '" '

class SVGElemText(SVGElemBase):

    def __init__(self, x, y, value, cls=None, style=None):
        super().__init__(cls, style)
        self.x = x
        self.y = y
        self.value = value

    def get_width(self, font_width):
        return len(self.value) * font_width

    def get_height(self, font_height):
        return font_height

    def generate(self, dx=0, dy=0):
        x = self.x + dx
        y = self.y + dy
        value = html.escape(self.value)
        return f'<text x="{x}" y="{y}" {self.generate_class()} {self.generate_style()}>{value}</text>'

class SVGElemRectText(SVGElemBase):

    def __init__(self, x, y, w, h, value, text_cls=None, rect_cls=None, style=None):
        super().__init__(None, style)
        self.x = x
        self.y = y
        self.w = w
        self.h = h
        self.value = value
        self.text_cls=text_cls
        self.rect_cls=rect_cls

    def generate(self, dx=0, dy=0):
        x = self.x + dx
        y = self.y + dy
        w = self.w
        h = self.h
        value = html.escape(self.value)
        
        svg = f'<rect x="{x}" y="{y - h + 0.25 * h}" width="{w}" height="{h}" rx="{h * 0.2}" stroke="black" stroke-width="0.5" fill="white" {self.generate_class(self.rect_cls)} {self.generate_style()} />\n'
        #svg += f'<text="50%" y="50%" text-anchor="middle">{value}</text>'
        svg += f'<text x="{x + w / 2}" y="{y}" {self.generate_class(self.text_cls)} {self.generate_style()}>{value}</text>'
        #svg += f'<rect x="10" y="10" width="100" height="50" stroke="black" stroke-width="0.5" fill="none" />\n'
        return svg

class SVGElemLine(SVGElemBase):

    def __init__(self, x1, y1, x2, y2, font_height=None, start_value=None, end_value=None, cls=None, style=None):
        super().__init__(cls, style)
        self.x1 = x1
        self.y1 = y1
        self.x2 = x2
        self.y2 = y2
        self.font_height = font_height

        self.start_value = start_value or ""
        self.end_value = end_value or ""

    def generate(self, dx=0, dy=0):
        x1 = self.x1 + dx
        y1 = self.y1 + dy
        x2 = self.x2 + dx
        y2 = self.y2 + dy

        font_height = self.font_height
        if not font_height:
            dist_y = abs(y1 - y2)
            font_height = dist_y * 0.3

        start_value = html.escape(self.start_value)
        end_value = html.escape(self.end_value)

        svg = f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="black" stroke-width="0.5" fill="none" marker-end="url(#arrowhead)" />'
        if start_value:
            svg += f'<text x="{x1}" y="{y1 + font_height*0.25}" class="center-text" font-size="{font_height}">{end_value}</text>'

        if end_value:
            svg += f'<text x="{x2}" y="{y2 - font_height*0.25}" class="center-text" font-size="{font_height}">{end_value}</text>'

        return svg
    
class SVGElemCurvedLine(SVGElemLine):


    def _calculate(self, dx=0, dy=0):        
        x1 = self.x1 + dx
        y1 = self.y1 + dy
        x2 = self.x2 + dx
        y2 = self.y2 + dy

        dist = ((x1 - x2) ** 2 + (y1 - y2) ** 2) ** 0.5
        d = dist * 0.15

        cx = (x1 + x2) / 2
        cy = (y1 + y2) / 2 + d

        font_height = self.font_height
        if not font_height:
            dist_y = abs(y1 - y2)
            font_height = dist_y * 0.3

        return (x1, y1), (cx, cy), (x2, y2), font_height


    def get_boundary_box(self, dx=0, dy=0):
        (x1, y1), (cx, cy), (x2, y2), font_height = self._calculate(dx, dy)

        def parametric_curve_point(t):
            xt = (1 - t) ** 2 * x1 + 2 * (1 - t) * t * cx + t ** 2 * x2
            yt = (1 - t) ** 2 * y1 + 2 * (1 - t) * t * cy + t ** 2 * y2
            return xt, yt

        max_t = (y1 - cy) / (y1 - 2 * cy + y2)
        _, max_yt = parametric_curve_point(max_t)

        min_x, max_x = min(x1, x2), max(x1, x2)
        min_y, max_y = min(y1, y2, max_yt), max(y1, y2, max_yt)

        return min_x, min_y, max_x - min_x, max_y - min_y

    def generate(self, dx=0, dy=0):
        (x1, y1), (cx, cy), (x2, y2), font_height = self._calculate(dx, dy)

        start_value = html.escape(self.start_value)
        end_value = html.escape(self.end_value)
        svg = f'<path d="M {x1},{y1} Q {cx},{cy} {x2},{y2}" stroke="black" stroke-width="0.5" stroke-dasharray="5, 5" fill="none" marker-end="url(#arrowhead)" />'

        if start_value:
            svg += f'<text x="{x1}" y="{y1 + font_height*0.75}" class="center-text" font-size="75%">{start_value}</text>'

        if end_value:
            svg += f'<text x="{x2}" y="{y2 + font_height*0.75}" class="center-text" font-size="75%">{end_value}</text>'
        #svg = f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="black" stroke-width="0.5" fill="none" marker-end="url(#arrowhead)" />'
        return svg

class SVGElemArc(SVGElemBase):

    def __init__(self, x1, x2, y, offset, value, cls=None, style=None):
        super().__init__(None, style)
        self.root_arc_height = 50
        self.x1 = x1
        self.x2 = x2
        self.y = y
        self.offset = offset
        self.value = value

    def reset(self, y=None):
        if y is not None:
            self.y = y

    def get_width(self, font_width):
        x1 = self.x1
        x2 = self.x2
        w_text = self.value * font_width
        if x1 == x2:
            return w_text
        else:
            w_arc = abs(x1 - x2) - self.offset 
            return max(w_arc, w_text)

    def get_height(self, font_height):
        if self.x1 == self.x2:
            return self.root_arc_height + self.offset + font_height
        
        rx = (abs(self.x1 - self.x2) - self.offset) / 2
        ry = (rx - self.offset) * 0.6
        return ry + self.offset + font_height

    def generate(self, dx, dy):
        x1 = self.x1 + dx
        x2 = self.x2 + dx
        y = self.y + dy

        offset = self.offset
        value = html.escape(self.value)

        rx = (abs(x1 - x2) - offset) / 2
        ry = (rx - offset) * 0.6
        
        svg = ""
        if x1 == x2:
            svg += f'<path d="M {x1} {y - self.root_arc_height} L {x1} {y}" stroke="black" stroke-width="0.5" fill="none" marker-end="url(#arrowhead)" />\n'
            ry  = self.root_arc_height
        elif x1 > x2:
            x1 -= offset
            svg += f'<path d="M {x1} {y} A {rx} {ry} 0 0 0 {x2} {y}" stroke="black" stroke-width="0.5" fill="none" marker-end="url(#arrowhead)" />\n'
        else:
            x1 += offset
            svg += f'<path d="M {x1} {y} A {rx} {ry} 0 0 1 {x2} {y}" stroke="black" stroke-width="0.5" fill="none" marker-end="url(#arrowhead)" />\n'
        
        # draw dep
        xt = min(x1, x2) + (abs(x1 - x2)) / 2
        yt = y - ry - offset

        svg += f'<text x="{xt}" y="{yt}" class="center-text">{value}</text>'

        return svg        
