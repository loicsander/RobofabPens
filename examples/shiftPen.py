#coding=utf-8

from fontTools.pens.basePen import BasePen



class AbstractShiftPen(BasePen):
    """
    Move a glyph’s x and y coordinates by xShift and yShift respectively.
    In itself, the pen doesn’t ‘draw’ anything, it just collects coordinates,
    adds xShift and yShift, and prints the resulting coordinates for each contour.
    """
    def __init__(self, xShift=0, yShift=0):
        self.xShift = xShift
        self.yShift = yShift
        self.contourCounter = 0


    def _moveTo(self, pt):
        self.newCoordinates = []
        shiftedPoint, = self.shiftCoordinates(pt)
        self.newCoordinates.append((nx, ny))


    def _lineTo(self, pt):
        shiftedPoint, = self.shiftCoordinates(pt)
        self.newCoordinates.append((nx, ny))


    def _curveToOne(self, pt1, pt2, pt3):
        for pt in [pt1, pt2, pt3]:
            shiftedPoint, = self.shiftCoordinates(pt)
            self.newCoordinates.append((nx, ny))


    def endPath(self):
        """Print shifted coordinates for the currentContour as well as its index."""
        print self.contourCounter
        print '\n'.join([str(coordinates) for coordinates in self.newCoordinates])
        print '\n'
        self.contourCounter += 1

    # As there’s no drawing happening with this pen, self.closePath() can do the same as self.endPath().
    closePath = endPath


    def shiftCoordinates(self, *points):
        """For given (x, y) coordinates, return said coordinates shifted by (xShift, yShift)."""
        return [(x + self.xShift, y + self.yShift) for x, y in points]



class ShiftPen(AbstractShiftPen):
    """
    Implementation of an AbstractShiftPen that actually draws the resulting shifted glyph.
    Needs to be provided an external pen to do so.
    """
    def __init__(self, otherPen, xShift=0, yShift=0):
        super(ShiftPen, self).__init__(xShift, yShift)
        self.otherPen = otherPen


    def _moveTo(self, pt):
        shiftedPoint, = self.shiftCoordinates(pt)
        self.otherPen.moveTo(shiftedPoint)


    def _lineTo(self, pt):
        shiftedPoint, = self.shiftCoordinates(pt)
        self.otherPen.lineTo(shiftedPoint)


    def _curveToOne(self, pt1, pt2, pt3):
        self.otherPen.curveTo(*self.shiftCoordinates(pt1, pt2, pt3))


    def endPath(self):
        self.otherPen.endPath()


    def closePath(self):
        self.otherPen.closePath()


