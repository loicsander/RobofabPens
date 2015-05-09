#coding=utf-8
from __future__ import division
from math import pi, radians, cos, sin, atan2, atan, hypot
import random

from robofab.pens.adapterPens import PointToSegmentPen, SegmentToPointPen
from robofab.pens.reverseContourPointPen import ReverseContourPointPen
from fontTools.pens.basePen import BasePen


def circle(pen, (cx, cy), radius, roundness=0.55):
    r = radius
    pen.moveTo((cx+r, cy))
    pen.curveTo((cx+r, cy+(r*roundness)), (cx+(r*roundness), cy+r), (cx, cy+r))
    pen.curveTo((cx-(r*roundness), cy+r), (cx-r, cy+(r*roundness)), (cx-r, cy))
    pen.curveTo((cx-r, cy-(r*roundness)), (cx-(r*roundness), cy-r), (cx, cy-r))
    pen.curveTo((cx+(r*roundness), cy-r), (cx+r, cy-(r*roundness)), (cx+r, cy))
    pen.closePath()


def calcVector(point1, point2):
    x1, y1 = point1
    x2, y2 = point2
    dx = x2 - x1
    dy = y2 - y1
    return dx, dy


def calcDistance(point1, point2):
    dx, dy = calcVector(point1, point2)
    return hypot(dx, dy)


def calcAngle(point1, point2):
    dx, dy = calcVector(point1, point2)
    return atan2(dy, dx)


def satellize((x, y), angle, width, shift=0.5):
    x1, y1 = polarCoord((x, y), angle, width*shift)
    x2, y2 = polarCoord((x, y), angle, -(width*(1-shift)))
    return (x1, y1), (x2, y2)


def polarCoord((x, y), angle, distance):
    nx = x + (distance * cos(angle))
    ny = y + (distance * sin(angle))
    return nx, ny


def pointOnACurve((x1, y1), (cx1, cy1), (cx2, cy2), (x2, y2), value):
    # From Frederik Berlaen’s Outliner
    dx = x1
    cx = (cx1 - dx) * 3.0
    bx = (cx2 - cx1) * 3.0 - cx
    ax = x2 - dx - cx - bx
    dy = y1
    cy = (cy1 - dy) * 3.0
    by = (cy2 - cy1) * 3.0 - cy
    ay = y2 - dy - cy - by
    mx = ax*(value)**3 + bx*(value)**2 + cx*(value) + dx
    my = ay*(value)**3 + by*(value)**2 + cy*(value) + dy
    return mx, my


def remap(values, newMin=0, newMax=1):
    initDelta = values[-1] - values[0]
    if initDelta == 0:
        return values
    newDelta = newMax - newMin
    for i, v in enumerate(values):
        ratio = v / initDelta
        new = newMin + (newDelta * ratio)
        values[i] =  new
    return values


def curveIntervals((a1, h1, h2, a2), pace=10):
    l = 0
    c = 1
    intervals = [0]
    ax, ay = a1
    bx, by = h1
    cx, cy = h2
    dx, dy = a2
    # define an arbitrary number of steps that’s likely to be inferior to the size of a pixel/grid unit
    delta = int(hypot(dx-ax, dy-ay) * 1.5)
    for i in range(delta+1):
        t = i/delta
        x, y = pointOnACurve((ax, ay), (bx, by), (cx, cy), (dx, dy), t)
        if i > 0:
            l += hypot(x-px, y-py)
            if l >= c * pace:
                intervals.append(t)
                c += 1
        px, py = x, y
    intervals = remap(intervals)
    return intervals, l


def bezierTangent(a, b, c, d, t):
    # Implementation of http://stackoverflow.com/questions/4089443/find-the-tangent-of-a-point-on-a-cubic-bezier-curve-on-an-iphone
    return (-3*(1-t)**2 * a) + (3*(1-t)**2 * b) - (6*t*(1-t) * b) - (3*t**2 * c) + (6*t*(1-t) * c) + (3*t**2 * d)


def firstDerivative((x1, y1), (cx1, cy1), (cx2, cy2), (x2, y2), value):
    mx = bezierTangent(x1, cx1, cx2, x2, value)
    my = bezierTangent(y1, cy1, cy2, y2, value)
    return mx, my



class StepPen(BasePen):
    """
    Pen moving along an outline with a given number of steps.
    Can be subclassed to do systematic drawing, a dotted line for instance.

    In the base implementation, the steps a converted to t values on a segment, thus they will not necessarily be evenly spaced in curve segments.
    If you want evenly spaced steps, you should set the *isPaced* variable to True.
    If *isPaced* is set to True, the pace value is used as a distance, otherwise, it will correspond to a number of steps.

    Subclassing the pen, one does only need to implement the drawStep() method
    to define what will be drawn at each step along the line.

    self.drawStep() receives 3 arguments, a point’s coordinates, the tangent angle at that point,
    and the progression along the currently drawn segment.

    This pen doesn’t draw components.
    """

    def __init__(self, pace=20):
        self.isPaced = True
        self.otherPen = None
        self.pace = pace if pace > 0 else 1
        self.points = []
        self.pacedPoints = []
        self._currentContour = []

    def _moveTo(self, pt):
        self.move_ = True
        self._currentContour.append(pt)
        self.points.append(pt)

    def _lineTo(self, pt1):
        pt0 = self.points[-1]
        d = calcDistance(pt0, pt1)
        tanAngle = calcAngle(pt0, pt1)

        if self.move_ == True:
            self.drawStep(pt0, tanAngle, 0)
            self.pacedPoints.append(pt0)
            self.move_ = False

        if self.isPaced == True:
            steps = int(d / self.pace)
        elif self.isPaced == False:
            steps = self.pace

        if steps <= 0: steps = 1

        x0, y0 = pt0
        x1, y1 = pt1
        for i in range(1, steps+1):
            x = x0 + ((x1 - x0) * (i / steps))
            y = y0 + ((y1 - y0) * (i / steps))
            if (x, y) not in self.points:
                self.drawStep((x, y), tanAngle, i/steps)
                self.pacedPoints.append((x, y))
        self.points.append(pt1)
        self._currentContour.append(pt1)

    def _curveToOne(self, pt1, pt2, pt3):
        pt0 = self.points[-1]
        nx, ny = firstDerivative(pt0, pt1, pt2, pt3, 0)
        tanAngle = atan2(ny, nx)

        if self.move_ == True:
            self.drawStep(pt0, tanAngle, 0)
            self.pacedPoints.append(pt0)
            self.move_ = False

        if self.isPaced == True:
            intervals, d = curveIntervals((pt0, pt1, pt2, pt3), self.pace)
        elif self.isPaced == False:
            intervals = [s/self.pace for s in range(self.pace+1)]

        steps = len(intervals)

        for i, t in enumerate(intervals[1:]):
            x, y = pointOnACurve(pt0, pt1, pt2, pt3, t)
            nx, ny = firstDerivative(pt0, pt1, pt2, pt3, t)
            tanAngle = atan2(ny, nx)
            if (x, y) not in self.points:
                self.drawStep((x, y), tanAngle, i/steps)
                self.pacedPoints.append((x, y))
        self.points.append(pt3)
        self._currentContour.append(pt3)

    def endPath(self):
        if self.otherPen is not None and self.otherPen.contour is not None:
            self.otherPen.endPath()
        self.previousPoint = None
        self._currentContour = []

    def closePath(self):
        if len(self._currentContour):
            self._lineTo(self._currentContour[0])
        if self.otherPen is not None and self.otherPen.contour is not None:
            self.otherPen.closePath()
        self.previousPoint = None
        self._currentContour = []

    def addComponent(self, glyphName, transformation):
        self.otherPen.addComponent(glyphName, transformation)

    def drawStep(self, (x, y), tanAngle, progress):
        pass

    def setIsPaced(self, b=True):
        self.isPaced = b

class FlattenPen(StepPen):
    """Flattens curves into segments of given length (pace value)."""

    def __init__(self, pen, pace=10):
        super(FlattenPen, self).__init__(pace)
        self.otherPen = pen

    def _lineTo(self, pt1):
        pt0 = self.points[-1]
        d = calcDistance(pt0, pt1)

        if self.move_ == True:
            self.otherPen.moveTo(pt0)
            self.pacedPoints.append(pt0)
            self.move_ = False

        self.otherPen.lineTo(pt1)
        self.pacedPoints.append(pt1)
        self.points.append(pt1)
        self._currentContour.append(pt1)

    def drawStep(self, (x, y), tanAngle, progress):
        if self.move_ == True:
           drawFunc = self.otherPen.moveTo
        elif self.move_ == False:
            drawFunc = self.otherPen.lineTo
        drawFunc((x, y))


class JitterPen(StepPen):
    """Draws an outline by adding jitter, some sort of gaussian noise."""

    def __init__(self, pen, pace=10, xAmplitude=10, yAmplitude=None):
        super(JitterPen, self).__init__(pace)
        self.otherPen = pen
        self.xAmplitude = xAmplitude
        self.yAmplitude = yAmplitude if yAmplitude is not None else xAmplitude

    def drawStep(self, (x, y), tanAngle, progress):

        if self.move_ == True:
           drawFunc = self.otherPen.moveTo
        elif self.move_ == False:
            drawFunc = self.otherPen.lineTo

        jx = self.deviate(x, self.xAmplitude)
        jy = self.deviate(y, self.yAmplitude)
        drawFunc((jx, jy))

    def deviate(self, value, amplitude):
        return random.gauss(value, amplitude)

class DashPen(StepPen):
    """Draws lines at each step. If *normal* is set to False, the lines are perpendicular to the outline direction, else, tangent."""

    def __init__(self, pen, pace=20, length=10, angle=None, normal=False, embroidered=False):
        super(DashPen, self).__init__(pace)
        self.otherPen = pen
        self.length = length
        self.normal = normal
        self.embroidered = embroidered
        self.angle = radians(angle) if angle is not None else None

    def drawStep(self, (x, y), tanAngle, progress):
        if self.normal == True and self.angle is None:
            angle = tanAngle + (pi/2)
        elif self.normal == False and self.angle is None:
            angle = tanAngle
        elif self.angle is not None:
            angle = self.angle
        pt1, pt2 = satellize((x, y), angle, self.length)
        if self.embroidered == False or (self.embroidered == True and self.otherPen.contour is None):
            self.otherPen.moveTo(pt1)
        else:
            self.otherPen.lineTo(pt1)
        self.otherPen.lineTo(pt2)
        if self.embroidered == False:
            self.otherPen.endPath()


class DotPen(StepPen):
    """Draws a circle at each step with given radius."""

    isPaced = True

    def __init__(self, pen, pace=20, radius=10):
        super(DotPen, self).__init__(pace)
        self.otherPen = pen
        self.radius = radius

    def drawStep(self, (x, y), tanAngle, progress):
        r = self.radius
        circle(self.otherPen, (x, y), r)

    def deviate(self, value, amplitude):
        return random.gauss(value, amplitude)

class SpikePen(StepPen):
    """Adds spikes to an outline (what do you mean, useless?)."""

    isPaced = True

    def __init__(self, pen, pace=20, spikeLength=25):
        super(SpikePen, self).__init__(pace)
        self.otherPen = pen
        self.spikeLength = spikeLength

    def closePath(self):
        if len(self._currentContour):
            self._lineTo(self._currentContour[0])
#            self.drawStep(self._currentContour[0], 0, 0)
        if self.otherPen is not None and self.otherPen.contour is not None:
            self.otherPen.closePath()
        self.previousPoint = None
        self._currentContour = []

    def drawStep(self, (x1, y1), tanAngle, progress):

        if self.move_ == True:
           self.otherPen.moveTo((x1, y1))

        elif self.move_ == False:

            x0, y0 = self.pacedPoints[-1]
            l = self.spikeLength
            d = calcDistance((x0, y0), (x1, y1))
            a = calcAngle((x0, y0), (x1, y1))
            sa = atan(l / (d/2))
            sl = hypot(d/2, l)
            sx = x0 + (sl * cos(sa+a))
            sy = y0 + (sl * sin(sa+a))
            self.otherPen.lineTo((sx, sy))
            self.otherPen.lineTo((x1, y1))