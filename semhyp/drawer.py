"""
This module provides functionality for creating and manipulating SVG canvases.

Classes:
    SVGCanvas: A class for creating SVG canvas elements with various styles and markers.

Imports:
    from .svg.blocks import *: Imports all components from the svg.blocks module.
    from .text import Doc, Span: Imports the Doc and Span classes from the text module.
    from .hyper import edge2txt: Imports the edge2txt function from the hyper module.
"""

from .svg.blocks import SVGBlockSent, SVGBlockSentAnno, SVGBlockHyperedge
from .text import Doc, Span
from .hyper import edge2txt

class SVGCanvas():
    """
    A class for creating SVG canvas elements with various styles and markers.

    Attributes:
        template (str): The SVG template string with placeholders for width, height, font size, and colors.

    Methods:
        __init__(self, width, height, font_size): Initializes the SVGCanvas with specified width, height, and font size.
        add_block(self, block): Adds an SVG block to the canvas.
        render(self): Renders the SVG canvas as a string.
    """

    template="""
<svg width="{width}" height="{height}" xmlns="http://www.w3.org/2000/svg"
    font-family="courier new"
    font-size="{font_size}"
    style="background: white">
    <style>
        .center-text {{
            fill: black;
            text-anchor: middle;
        }}
        .left-text {{
            fill: black;
            text-anchor: left;
        }}

        .typeP {{fill: lightcoral;}}
        .typeC {{fill: lightblue;}}
        .typeT {{fill: lemonchiffon;}}
        .typeJ {{fill: moccasin;}}
        .typeM {{fill: honeydew;}}
        .typeB {{fill: lightgrey;}}
        
        {colors}

    </style>
    <!-- Define an arrow marker -->
    <defs>
        <marker id="arrowhead" 
                markerWidth="{arrow_width}" markerHeight="{arrow_height}" 
                refX="{arrow_width}" refY="{arrow_half_height}" 
                orient="auto" markerUnits="strokeWidth">
            <!-- Arrowhead path -->
            <polygon points="0 0, {arrow_width} {arrow_half_height}, 0 {arrow_height}" fill="grey" />
        </marker>
    </defs>          
    {content}
</svg>
"""

    def  __init__(self, font_height, font_width, offset, margin=0, colors=None):
        """
        Initializes the SVGCanvas with specified font height, font width, offset, margin, and colors.

        Args:
            font_height (int): The height of the font.
            font_width (int): The width of the font.
            offset (int): The offset for the canvas.
            margin (int, optional): The margin for the canvas. Defaults to 0.
            colors (dict, optional): A dictionary of colors for different elements. Defaults to None.
        """        
        self.font_height = font_height
        self.font_width = font_width
        self.offset = offset
        self.margin = margin
        self._blocks = []
        self.width = 0
        self.height = self.margin

        self.colors = colors
        if self.colors is None:
            self.colors = {"word": "black",
                           "lemma": "grey",
                           "ent": "blue",
                           "srl": "green",
                           "coref": "red"}
        


    def add(self, block):
        """
        Adds an SVG block to the canvas.

        Args:
            block (SVGBlock): The SVG block to add to the canvas.
        """
        self._blocks.append(block)
        self.width = max(block.width + 2 * self.margin, self.width)
        self.height += block.height + self.margin

    def generate(self):
        """
        Generates the SVG content for the canvas.

        Returns:
            str: The generated SVG content as a string.
        """        
        dy = self.margin
        dx = self.margin
        content = ""
        for block in self._blocks:
            content += block.generate(dx=dx, dy=dy)
            dy += block.height + self.margin

        arrow_width = self.font_height * 0.7
        arrow_height = arrow_width * 0.7
        arrow_half_height = arrow_height / 2

        colors = " ".join(f".{cls} {{fill: {color}}}" for cls, color in self.colors.items())
        svg = self.template.format(width=self.width, height=self.height, 
                                   font_size=self.font_height, 
                                   arrow_width=arrow_width, arrow_height=arrow_height, arrow_half_height=arrow_half_height,
                                   colors=colors, content=content)
        return svg
    

def draw_text(doc_or_sents, show_spans=True, annos=None, font_height=16, font_width=16*0.6, offset=5, margin=0):
    """
    Draws annotated sentences on an SVG canvas.

    Args:
        doc_or_sents (Doc or Span or list): The document, span, or list of sentences to draw.
        show_spans (bool, optional): Whether to show spans. Defaults to True.
        annos (str or list, optional): Annotations to include. Defaults to None.
        font_height (int, optional): The height of the font. Defaults to 16.
        font_width (float, optional): The width of the font. Defaults to 16*0.6.
        offset (int, optional): The offset for the canvas. Defaults to 5.
        margin (int, optional): The margin for the canvas. Defaults to 0.

    Returns:
        str: The generated SVG content as a string.
    """       
    canvas = SVGCanvas(font_height=font_height,
                       font_width=font_width,
                       offset=offset,
                       margin=margin)
        
    if isinstance(annos, str):
        annos = annos.replace(" ", "").split(",")

    if isinstance(doc_or_sents, Doc):
        sents = doc_or_sents.sents
    elif isinstance(doc_or_sents, Span):
        sents = [doc_or_sents]
    else:
        sents = doc_or_sents

    for sent in sents:
        block = SVGBlockSent(canvas, sent)
        canvas.add(block)
        block = SVGBlockSentAnno(canvas, sent, show_spans=show_spans, annos=annos)
        canvas.add(block)
    
    return canvas.generate()

def draw_hyper(edge_or_edges, font_height=15, font_width=16*0.6, offset=5, margin=0):
    """
    Draws hyperedges on an SVG canvas.

    Args:
        edge_or_edges (list or single edge): The hyperedge or list of hyperedges to draw.
        font_height (int, optional): The height of the font. Defaults to 15.
        font_width (float, optional): The width of the font. Defaults to 16*0.6.
        offset (int, optional): The offset for the canvas. Defaults to 5.
        margin (int, optional): The margin for the canvas. Defaults to 0.

    Returns:
        str: The generated SVG content as a string.
    """    
    canvas = SVGCanvas(font_height=font_height,
                       font_width=font_width,
                       offset=offset,
                       margin=margin)
    
    if not isinstance(edge_or_edges, list):
        edge_or_edges = [edge_or_edges]
    
    for edge in edge_or_edges:
        block = SVGBlockSent(canvas, edge2txt(edge))
        #canvas.add(block)
        block = SVGBlockHyperedge(canvas, edge)
        canvas.add(block)
    
    return canvas.generate()

def save(filename, content):
    """
    Saves the given SVG content to a file.

    Args:
        filename (str): The name of the file to save the content to.
        content (str): The content to save to the file.
    """
    with open(filename, "w") as fp:
        fp.write(content)

