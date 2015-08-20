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
        return 'trsp(via edges)'
    
    @classmethod
    def getControlNames(self):
        return [
            'labelId', 'lineEditId',
            'labelSource', 'lineEditSource',
            'labelTarget', 'lineEditTarget',
            'labelCost', 'lineEditCost',
            'labelReverseCost', 'lineEditReverseCost',
            'labelIds', 'lineEditIds', 'buttonSelectIds',
            'labelPcts', 'lineEditPcts',
            'checkBoxDirected', 'checkBoxHasReverseCost',
            'labelTurnRestrictSql', 'plainTextEditTurnRestrictSql'
        ]
    
    @classmethod
    def isEdgeBase(self):
        return True
    
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
                ARRAY[%(ids)s]::integer[], ARRAY[%(pcts)s]::float8[], %(directed)s, %(has_reverse_cost)s, %(turn_restrict_sql)s)""" % args
    
    def draw(self, rows, con, args, geomType, canvasItemList, mapCanvas):
        resultPathsRubberBands = canvasItemList['paths']
        # TODO: detect each paths
        rubberBand = QgsRubberBand(mapCanvas, Utils.getRubberBandType(False))
        rubberBand.setColor(QColor(255, 0, 0, 128))
        rubberBand.setWidth(4)
        i = 0
        count = len(rows)
        ids = args['ids'].split(',')
        args['last_id'] = ids[len(ids) - 1]
        pcts = args['pcts'].split(',')
        args['first_pct'] = pcts[0]
        args['last_pct'] = pcts[len(pcts) - 1]
        for row in rows:
            query2 = ""
            cur2 = con.cursor()
            args['result_node_id'] = row[1]
            args['result_edge_id'] = row[2]
            args['result_cost'] = row[3]

            if i == 0 and args['result_node_id'] == -1:
                args['result_next_node_id'] = rows[i + 1][1]
                query2 = """
                    SELECT ST_AsText(%(transform_s)sST_Line_Substring(%(geometry)s, %(first_pct)s, 1.0)%(transform_e)s) FROM %(edge_table)s
                        WHERE %(target)s = %(result_next_node_id)s AND %(id)s = %(result_edge_id)s
                    UNION
                    SELECT ST_AsText(%(transform_s)sST_Line_Substring(ST_Reverse(%(geometry)s), 1.0 - %(first_pct)s, 1.0)%(transform_e)s) FROM %(edge_table)s
                        WHERE %(source)s = %(result_next_node_id)s AND %(id)s = %(result_edge_id)s;
                """ % args
            elif i == (count - 1) and ((args['result_edge_id'] == -1) or (str(args['result_edge_id']) == args['last_id'])):
                if args['result_edge_id'] != -1:
                    query2 = """
                        SELECT ST_AsText(%(transform_s)sST_Line_Substring(%(geometry)s, 0.0, %(last_pct)s)%(transform_e)s) FROM %(edge_table)s
                            WHERE %(source)s = %(result_node_id)s AND %(id)s = %(result_edge_id)s
                        UNION
                        SELECT ST_AsText(%(transform_s)sST_Line_Substring(ST_Reverse(%(geometry)s), 0.0, 1.0 - %(last_pct)s)%(transform_e)s) FROM %(edge_table)s
                            WHERE %(target)s = %(result_node_id)s AND %(id)s = %(result_edge_id)s;
                    """ % args
                else:
                    break
            else:
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
            
            i = i + 1

        if rubberBand:
            resultPathsRubberBands.append(rubberBand)

    def __init__(self, ui):
        FunctionBase.__init__(self, ui)
