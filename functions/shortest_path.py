from PyQt4.QtCore import *
from PyQt4.QtGui import *
from qgis.core import *
from qgis.gui import *
import psycopg2
from FunctionBase import FunctionBase

class Function(FunctionBase):
    
    @classmethod
    def getName(self):
        return 'shortest_path'
    
    @classmethod
    def getControlNames(self):
        return [
            'lineEditId', 'lineEditSource', 'lineEditTarget',
            'lineEditCost', 'lineEditReverseCost',
            'lineEditSourceId', 'buttonSelectSourceId',
            'lineEditTargetId', 'buttonSelectTargetId',
            'checkBoxDirected', 'checkBoxHasReverseCost',
            'buttonExport'
        ]
    
    @classmethod
    def isEdgeBase(self):
        return False
    
    @classmethod
    def prepare(self, con, args, geomType, canvasItemList):
        resultPathRubberBand = canvasItemList['path']
        resultPathRubberBand.reset(False)
    
    @classmethod
    def getQuery(self, args):
        return """
            SELECT * FROM shortest_path('
                SELECT %(id)s AS id,
                    %(source)s::int4 AS source,
                    %(target)s::int4 AS target,
                    %(cost)s::float8 AS cost%(reverse_cost)s
                    FROM %(edge_table)s',
                %(source_id)s, %(target_id)s, %(directed)s, %(has_reverse_cost)s)""" % args
    
    @classmethod
    def draw(self, rows, con, args, geomType, canvasItemList, mapCanvas):
        resultPathRubberBand = canvasItemList['path']
        for row in rows:
            cur2 = con.cursor()
            args['result_vertex_id'] = row[0]
            args['result_edge_id'] = row[1]
            args['result_cost'] = row[2]
            if args['result_edge_id'] != -1:
                query2 = """
                    SELECT ST_AsText(%(geometry)s) FROM %(edge_table)s
                        WHERE %(source)s = %(result_vertex_id)d AND %(id)s = %(result_edge_id)d
                    UNION
                    SELECT ST_AsText(ST_Reverse(%(geometry)s)) FROM %(edge_table)s
                        WHERE %(target)s = %(result_vertex_id)d AND %(id)s = %(result_edge_id)d;
                """ % args
                ##QMessageBox.information(self.ui, self.ui.windowTitle(), query2)
                cur2.execute(query2)
                row2 = cur2.fetchone()
                ##QMessageBox.information(self.ui, self.ui.windowTitle(), str(row2[0]))
                assert row2, "Invalid result geometry. (vertex_id:%(result_vertex_id)d, edge_id:%(result_edge_id)d)" % args
                
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
