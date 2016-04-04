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
        return 'bdAstar'
    
    @classmethod
    def getControlNames(self, version):
        return [
            'labelId', 'lineEditId',
            'labelSource', 'lineEditSource',
            'labelTarget', 'lineEditTarget',
            'labelCost', 'lineEditCost',
            'labelReverseCost', 'lineEditReverseCost',
            'labelX1', 'lineEditX1',
            'labelY1', 'lineEditY1',
            'labelX2', 'lineEditX2',
            'labelY2', 'lineEditY2',
            'labelSourceId', 'lineEditSourceId', 'buttonSelectSourceId',
            'labelTargetId', 'lineEditTargetId', 'buttonSelectTargetId',
            'checkBoxDirected', 'checkBoxHasReverseCost'
        ]
    
    @classmethod
    def isEdgeBase(self):
        return False
    
    @classmethod
    def canExport(self):
        return True
    
    def prepare(self, canvasItemList):
        resultPathRubberBand = canvasItemList['path']
        resultPathRubberBand.reset(Utils.getRubberBandType(False))
    
    def getQuery(self, args):
        return """
            SELECT seq, id1 AS _node, id2 AS _edge, cost AS _cost FROM pgr_bdAstar('
                SELECT %(id)s::int4 AS id,
                    %(source)s::int4 AS source,
                    %(target)s::int4 AS target,
                    %(cost)s::float8 AS cost%(reverse_cost)s,
                    %(x1)s::float8 AS x1,
                    %(y1)s::float8 AS y1,
                    %(x2)s::float8 AS x2,
                    %(y2)s::float8 AS y2
                    FROM %(edge_table)s',
                %(source_id)s, %(target_id)s, %(directed)s, %(has_reverse_cost)s)""" % args
    
    def getExportMergeQuery(self, args):
        args['result_query'] = self.getQuery(args)

        args['with_geom_query'] = """SELECT ST_UNION(%(edge_table)s.%(geometry)s) AS the_geom
            FROM %(edge_table)s JOIN result ON %(edge_table)s.%(id)s = result._edge
            """ % args

        args['aggregates_query'] = """SELECT
            SUM(_cost) AS agg_cost,
            array_agg(_node ORDER BY seq) AS _nodes,
            array_agg(_edge ORDER BY seq) AS _edges
            FROM result
            """

        query = """WITH
            result AS ( %(result_query)s ),
            with_geom AS ( %(with_geom_query)s ),
            aggregates AS ( %(aggregates_query)s )
            SELECT row_number() over() as seq,
            _nodes, _edges, agg_cost,
            ST_LineMerge(the_geom) AS path_geom FROM aggregates, with_geom 
            """ % args
        return query



    def draw(self, rows, con, args, geomType, canvasItemList, mapCanvas):
        resultPathRubberBand = canvasItemList['path']
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
                            resultPathRubberBand.addPoint(pt)
                elif geom.wkbType() == QGis.WKBLineString:
                    for pt in geom.asPolyline():
                        resultPathRubberBand.addPoint(pt)
    
    def __init__(self, ui):
        FunctionBase.__init__(self, ui)
