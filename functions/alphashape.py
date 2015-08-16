from PyQt4.QtCore import *
from PyQt4.QtGui import *
from qgis.core import *
from qgis.gui import *
import psycopg2
from .. import pgRoutingLayer_utils as Utils
from FunctionBase import FunctionBase

class Function(FunctionBase):
    
    @classmethod
    def getName(self):
        return 'alphashape'
    
    @classmethod
    def getControlNames(self):
        return [
            'labelId', 'lineEditId',
            'labelSource', 'lineEditSource',
            'labelTarget', 'lineEditTarget',
            'labelCost', 'lineEditCost',
            'labelReverseCost', 'lineEditReverseCost',
            'labelSourceId', 'lineEditSourceId', 'buttonSelectSourceId',
            'labelDistance', 'lineEditDistance',
            'checkBoxDirected', 'checkBoxHasReverseCost'
        ]
    
    @classmethod
    def isEdgeBase(self):
        return False
    
    @classmethod
    def canExport(self):
        return True
    
    def prepare(self, canvasItemList):
        resultAreaRubberBand = canvasItemList['area']
        resultAreaRubberBand.reset(Utils.getRubberBandType(True))

    def getQuery(self, args):
        return """
            SELECT x, y FROM pgr_alphashape('
                %(node_query)s
                SELECT *
                    FROM node
                    JOIN
                    (SELECT * FROM pgr_drivingDistance(''
                        SELECT %(id)s AS id,
                            %(source)s::int4 AS source,
                            %(target)s::int4 AS target,
                            %(cost)s::float8 AS cost%(reverse_cost)s
                            FROM %(edge_table)s'',
                        %(source_id)s, %(distance)s, %(directed)s, %(has_reverse_cost)s))
                    AS dd ON node.id = dd.id1'::text)""" % args
    
    def draw(self, rows, con, args, geomType, canvasItemList, mapCanvas):
        resultAreaRubberBand = canvasItemList['area']
        trans = None
        if mapCanvas.hasCrsTransformEnabled():
            canvasCrs = Utils.getDestinationCrs(mapCanvas)
            layerCrs = QgsCoordinateReferenceSystem()
            Utils.createFromSrid(layerCrs, args['srid'])
            trans = QgsCoordinateTransform(layerCrs, canvasCrs)
        
        # return columns are 'x', 'y'
        for row in rows:
            x = row[0]
            y = row[1]
            pt = QgsPoint(x, y)
            if trans:
                pt = trans.transform(pt)
            
            resultAreaRubberBand.addPoint(pt)
    
    def __init__(self, ui):
        FunctionBase.__init__(self, ui)
