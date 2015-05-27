from fontTools.pens.basePen import BasePen
from robofab.pens.pointPen import AbstractPointPen


def calcArea(points):
    l = len(points)
    area = 0
    for i in xrange(l):
        x1, y1 = points[i]
        x2, y2 = points[(i+1)%l]
        area += (x1*y2)-(x2*y1)
    return area / 2


def overlap((x1, y1), (x2, y2), threshold=2):
    return -threshold < x2 - x1 < threshold and -threshold < y2 - y1 < threshold



class CleanPointPen(AbstractPointPen):
    """
    Draws a glyph and filters out points and/or contours
    that are matched by threshold values *areaThreshold* and *overlapThreshold*.

    *areaThreshold* defines the minimal area for a contour to be filtered out.
    *overlapThreshold* defines the distance between two points for them to be considered overlapping.
    """

    def __init__(self, otherPen, areaThreshold=1000, overlapThreshold=2, removeOverlappingPoints=False):
        self.otherPen = otherPen
        self.areaThreshold = areaThreshold
        self.overlapThreshold = overlapThreshold
        self.removeOverlappingPoints = removeOverlappingPoints
        self.contours = []
        self.components = []


    def beginPath(self):
        self.currentContour = []


    def addPoint(self, pt, segmentType=None, smooth=False, name=None, *args, **kwargs):
        previousPoint = self.currentContour[-1] if len(self.currentContour) else None
        point = {
            'pt': pt,
            'segmentType': segmentType,
            'smooth': smooth,
            'name': name
        }
        if (previousPoint is None) or \
           (previousPoint is not None and point['segmentType'] is None) or \
           (previousPoint is not None and self.removeOverlappingPoints == True and (point['segmentType'] is not None and previousPoint['segmentType'] is not None and not overlap(point['pt'], previousPoint['pt'], self.overlapThreshold))) or\
           self.removeOverlappingPoints == False:
            self.currentContour.append(point)


    def endPath(self):
        self._flushContour()


    def addComponent(self, baseGlyphName, transformation):
        self.otherPen.addComponent(baseGlyphName, transformation)


    def _flushContour(self):
        area = calcArea([point['pt'] for point in self.currentContour if point['segmentType'] is not None])
        if abs(area) >= self.areaThreshold:
            self.draw(self.currentContour)


    def draw(self, contour):
        pen = self.otherPen
        close = not contour[0]['segmentType'] == 'move'

        pen.moveTo(contour[0]['pt'])
        for i, point in enumerate(contour[1:]):
            i += 1

            if point['segmentType'] == 'line':
                pen.lineTo(point['pt'])

            elif point['segmentType'] == 'curve':
                c1, c2 = contour[i-2]['pt'], contour[i-1]['pt']
                pen.curveTo(c1, c2, point['pt'])

        if close == True:
            pen.closePath()
        elif close == False:
            pen.endPath()