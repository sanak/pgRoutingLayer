"""
/***************************************************************************
 pgRouting Tester
                                 a QGIS plugin
                                 
 based on "pgRoutingLayer" plugin Copyright 2011 Anita Graser 
                             -------------------
        begin                : 2012-08-15
        copyright            : (c) 2012 by sanak
        email                : geosanak@gmail.com
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
 This script initializes the plugin, making it known to QGIS.
"""

def name():
    return "pgRouting Tester"
def description():
    return "Dockable widget that test pgRouting functions"
def version():
    return "Version 0.1"
def icon():
    return "icons/icon.png"
def qgisMinimumVersion():
    return "1.7"
def classFactory(iface):
    from pgRoutingTester import PgRoutingTester
    return PgRoutingTester(iface)
