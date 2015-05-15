Robofab Pens
================

A collection of [Robofab pens](http://robofab.org/objects/pen.html) doing various things with outlines.

**RobofabPens/Examples**

*Here are some simpler pens doing mostly basic things with and about outlines. I’m adding these hoping to help those who wish to better understand how robofab pen works. I’ll try adding a variety of examples.*

## ShiftPen

Two pens that affect an outline’s point coordinates. The first one ```AbstractShiftPen``` only collects the coordinates and returns the shifted value (as a printed output). The second one ```ShiftPen``` draws a shifted outline if provided with an external pen. Such a basic pen (a subclass of fontTools’ BasePen) has no drawing capabilities of its own; to draw something, it needs to wield another pen, the one that really draws and belongs to a glyph.

**Basic usage**
```python
from robofab.world import RGlyph

# create an empty glyph
glyph = RGlyph()
drawingPen = glyph.getPen()

# draw a square of 100x100 units with the drawing pen
drawingPen.moveTo((0, 0))
drawingPen.lineTo((0, 100))
drawingPen.lineTo((100, 100))
drawingPen.lineTo((100, 0))
drawingPen.closePath()

# the glyph now consists of a 100x100 units square

# create the shiftPen with shift values and give it the drawing pen
shiftPen = ShiftPen(drawingPen, xShift=50, yShift=50)

# draw the existing glyph with the shiftPen
glyph.draw(shiftPen)
```

the square in the glyph has now moved by 50 units, up and rightwards. In fact, there are now two squares in the glyph: the initial one, and the shifted one, since we drew the shifted square with the same pen as before without clearing the glyph’s contour.

If we wanted to simply move the square in the initial glyph, we need an additional step:

```python

# create an empty glyph
glyph = RGlyph()
drawingPen = glyph.getPen()

# draw a square of 100x100 units with the drawing pen
drawingPen.moveTo((0, 0))
drawingPen.lineTo((0, 100))
drawingPen.lineTo((100, 100))
drawingPen.lineTo((100, 0))
drawingPen.closePath()

# the glyph now consists of a 100x100 units square

# make a new glyph that will be the copy of the square we just drew
glyphCopy = RGlyph()
copyDrawingPen = glyphCopy.getPen()

# now we can draw the square from the initial glyph unto the copy
glyph.draw(copyDrawingPen)

# the square is copied, so we can now clear the initial glyph’s contour before drawing the new shifted square

glyph.clearContours()

# create the shiftPen with shift values and give it the drawing pen
shiftPen = ShiftPen(drawingPen, xShift=50, yShift=50)

# draw the existing glyph with the shiftPen
glyph.draw(shiftPen)
```

We now have effectively move the 100x100 units square inside the initial glyph.