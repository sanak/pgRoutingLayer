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
        return 'trsp(via vertices)'
    
    @classmethod
    def getControlNames(self):
        return [
            'labelId', 'lineEditId',
            'labelSource', 'lineEditSource',
            'labelTarget', 'lineEditTarget',
            'labelCost', 'lineEditCost',
            'labelReverseCost', 'lineEditReverseCost',
            'labelIds', 'lineEditIds', 'buttonSelectIds',
            'checkBoxDirected', 'checkBoxHasReverseCost',
            'labelTurnRestrictSql', 'plainTextEditTurnRestrictSql'
        ]
    
    @classmethod
    def isEdgeBase(self):
        return False
    
    @classmethod
    def canExport(self):
        return True
    
    def prepare(self, canvasItemList):
        resultPathsRubberBands = canvasItemList['paths']
        for path in resultPathsRubberBands:
            path.reset(Utils.getRubberBandType(False))
        canvasItemList['paths'] = []
    
    def getQuery(self, args):
        return """
            SELECT seq, id1 AS node, id2 AS edge, cost FROM pgr_trsp('
                SELECT %(id)s AS id,
                    %(source)s::int4 AS source,
                    %(target)s::int4 AS target,
                    %(cost)s::float8 AS cost%(reverse_cost)s
                    FROM %(edge_table)s',
                ARRAY[%(ids)s]::integer[], %(directed)s, %(has_reverse_cost)s, %(turn_restrict_sql)s)""" % args
    
    def draw(self, rows, con, args, geomType, canvasItemList, mapCanvas):
        resultPathsRubberBands = canvasItemList['paths']
        # TODO: detect each paths
        rubberBand = QgsRubberBand(mapCanvas, Utils.getRubberBandType(False))
        rubberBand.setColor(QColor(255, 0, 0, 128))
        rubberBand.setWidth(4)
        for row in rows:
            cur2 = con.cursor()
            args['result_node_id'] = row[1]
            args['result_edge_id'] = row[2]
            args['result_cost'] = row[3]
            if args['result_edge_id'] != -1:
                query2 = """
                    SELECT ST_AsText(%(transform_s)s%(geometry)s%(transform_e)s) FROM %(edge_table)s
                        WHERE %(source)s = %(result_node_id)d AND %(id)s = %(result_edge_id)d
                    UNION
                    SELECT ST_AsText(%(transform_s)sST_Reverse(%(geometry)s)%(transform_e)s) FROM %(edge_table)s
                        WHERE %(target)s = %(result_node_id)d AND %(id)s = %(result_edge_id)d;
                """ % args
                ##Utils.logMessage(query2)
                cur2.execute(query2)
                row2 = cur2.fetchone()
                ##Utils.logMessage(str(row2[0]))
                assert row2, "Invalid result geometry. (node_id:%(result_node_id)d, edge_id:%(result_edge_id)d)" % args
                
                geom = QgsGeometry().fromWkt(str(row2[0]))
                if geom.wkbType() == QGis.WKBMultiLineString:
                    for line in geom.asMultiPolyline():
                        for pt in line:
                            rubberBand.addPoint(pt)
                elif geom.wkbType() == QGis.WKBLineString:
                    for pt in geom.asPolyline():
                        rubberBand.addPoint(pt)

        if rubberBand:
            resultPathsRubberBands.append(rubberBand)

    def __init__(self, ui):
        FunctionBase.__init__(self, ui)
