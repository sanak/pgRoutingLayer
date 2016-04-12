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
        return 'trsp(edge)'
    
    @classmethod
    def getControlNames(self, version):
        return [
            'labelId', 'lineEditId',
            'labelSource', 'lineEditSource',
            'labelTarget', 'lineEditTarget',
            'labelCost', 'lineEditCost',
            'labelReverseCost', 'lineEditReverseCost',
            'labelSourceId', 'lineEditSourceId', 'buttonSelectSourceId',
            'labelSourcePos', 'lineEditSourcePos',
            'labelTargetId', 'lineEditTargetId', 'buttonSelectTargetId',
            'labelTargetPos', 'lineEditTargetPos',
            'checkBoxDirected', 'checkBoxHasReverseCost',
            'labelTurnRestrictSql', 'plainTextEditTurnRestrictSql'
        ]
    
    @classmethod
    def isEdgeBase(self):
        return True
    
    @classmethod
    def canExport(self):
        return True
    
    def isSupportedVersion(self, version):
        return version >= 2.0 and version < 3.0

    def prepare(self, canvasItemList):
        resultPathRubberBand = canvasItemList['path']
        resultPathRubberBand.reset(Utils.getRubberBandType(False))
    
    def getQuery(self, args):
        return """
            SELECT seq, id1 AS _node, id2 AS _edge, cost AS _cost FROM pgr_trsp('
              SELECT %(id)s::int4 AS id,
                %(source)s::int4 AS source,
                %(target)s::int4 AS target,
                %(cost)s::float8 AS cost%(reverse_cost)s
              FROM %(edge_table)s
              WHERE %(edge_table)s.%(geometry)s && %(BBOX)s',
              %(source_id)s, %(source_pos)s, %(target_id)s, %(target_pos)s, %(directed)s, %(has_reverse_cost)s, %(turn_restrict_sql)s)""" % args
    
    def getExportQuery(self, args):
        args['result_query'] = self.getQuery(args)

        query = """
            WITH
            result AS ( %(result_query)s )
            SELECT 
              CASE
                WHEN result._node = %(edge_table)s.%(source)s
                  THEN %(edge_table)s.%(geometry)s
                ELSE ST_Reverse(%(edge_table)s.%(geometry)s)
              END AS path_geom,
              result.*, %(edge_table)s.*
            FROM %(edge_table)s JOIN result
              ON %(edge_table)s.%(id)s = result._edge ORDER BY result.seq
            """ % args
        return query

    def draw(self, rows, con, args, geomType, canvasItemList, mapCanvas):
        resultPathRubberBand = canvasItemList['path']
        i = 0
        count = len(rows)
        for row in rows:
            query2 = ""
            cur2 = con.cursor()
            args['result_node_id'] = row[1]
            args['result_edge_id'] = row[2]
            args['result_cost'] = row[3]
            
            if i == 0 and args['result_node_id'] == -1:
                args['result_next_node_id'] = rows[i + 1][1]
                query2 = """
                    SELECT ST_AsText(%(transform_s)sST_Line_Substring(%(geometry)s, %(source_pos)s, 1.0)%(transform_e)s) FROM %(edge_table)s
                        WHERE %(target)s = %(result_next_node_id)s AND %(id)s = %(result_edge_id)s
                    UNION
                    SELECT ST_AsText(%(transform_s)sST_Line_Substring(ST_Reverse(%(geometry)s), 1.0 - %(source_pos)s, 1.0)%(transform_e)s) FROM %(edge_table)s
                        WHERE %(source)s = %(result_next_node_id)s AND %(id)s = %(result_edge_id)s;
                """ % args
            elif i == (count - 1) and ((args['result_edge_id'] == -1) or (str(args['result_edge_id']) == args['target_id'])):
                if args['result_edge_id'] != -1:
                    query2 = """
                        SELECT ST_AsText(%(transform_s)sST_Line_Substring(%(geometry)s, 0.0, %(target_pos)s)%(transform_e)s) FROM %(edge_table)s
                            WHERE %(source)s = %(result_node_id)s AND %(id)s = %(result_edge_id)s
                        UNION
                        SELECT ST_AsText(%(transform_s)sST_Line_Substring(ST_Reverse(%(geometry)s), 0.0, 1.0 - %(target_pos)s)%(transform_e)s) FROM %(edge_table)s
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
                        resultPathRubberBand.addPoint(pt)
            elif geom.wkbType() == QGis.WKBLineString:
                for pt in geom.asPolyline():
                    resultPathRubberBand.addPoint(pt)
            
            i = i + 1
    
    def __init__(self, ui):
        FunctionBase.__init__(self, ui)
