
class FunctionBase(object):

    @classmethod
    def getName(self):
        return ''
    
    @classmethod
    def getControlNames(self, version):
        return [ '' ]
    
    #The following contain the mayority of the functionality has:
    @classmethod
    def isEdgeBase(self):
        return False
    
    # the mayority of the functions can Export
    @classmethod
    def canExport(self):
        return True

    # the mayority of the functions can ExportMerged
    @classmethod
    def canExportMerged(self):
        return True

    @classmethod
    def isSupportedVersion(self, version):
        return version >= 2.0 and version < 3.0

    def prepare(self, canvasItemList):
        pass
    
    def getQuery(self, args):
        return ''
    
    def getExportQuery(self, args):
        return ''

    def getExportMergeQuery(self, args):
        return ''
    
    def draw(self, rows, con, args, geomType, canvasItemList, mapCanvas):
        pass
    
    def __init__(self, ui):
        self.ui = ui
        self.minVersion = 2.0
        self.maxVersion = 2.99
