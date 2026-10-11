"""
Create maps automatically with QGIS and PyQgis!
Using APIs (OSM, Wikipedia, Wikidata) and geo-processing (intersection).

Checked with QGIS 3.14.16
Checked with QGIS 3.28.13
Checked with QGIS 3.34.11
Checked with QGIS 3.34.13

Example of map produced:
https://hg-map.fr/images/cours/python/Grand-Pic-de-la-Meije.png

Just change the path in "repLayers" and "repExport".
Download the data examples below this article, and unzip them:
https://hg-map.fr/tutos/73-qgis-et-python

Check/change the names and directories used by layers below "Path of layers".

Then just run this code!

Other PyQgis tips here:
https://hg-map.fr/astuces/84-pyqgis

Other standalone PyQgis tips here:
https://hg-map.fr/astuces/85-pyqgis
"""

from PyQt5 import *

# In some cases:
# from PyQt5.QtCore import *


import datetime
import xml.etree.ElementTree
import time
import shutil
import os
from pathlib import Path

import requests
import json

from qgis.PyQt.QtGui import QImage, QPainter, QColor

import wikipedia

# Main paths
repLayers = Path('C:/Users/georg/OneDrive/_saves/_generic data/France/Montagnes')
repExport = Path('C:/Users/georg/Downloads')
repIris = Path('C:/Users/georg/OneDrive/_saves/_generic data/France/France-Iris')

date = datetime.date.today()
aujourdhui_en = str(date)
aujourdhui_fr = date.strftime("%d/%m/%Y")

myBoldFont=QtGui.QFont('Verdana', 11)
myBoldFont.setBold(True)

myTitleBoldFont=QtGui.QFont('Verdana', 24)
myTitleBoldFont.setBold(True)

myMetaFont=QtGui.QFont('Verdana', 8)
myMetaFont.setItalic(True)


# Image 1
url = r'https://j4binv.master-geomatique.org/images/img_site/logos/logo2021-blanc.png'
response = requests.get(url)

image_originale1 = str(repLayers / 'logo_master.png')
path_nouvelle_image1 = str(repLayers / 'logo_master_fond_vert.png')

# Dowload image
if response.status_code == 200:
    with open(image_originale1, 'wb') as file:
        file.write(response.content)
else:
    raise Exception('Impossible de télécharger la photo !')

# Set a black background
my_image = QImage(image_originale1)
largeur = my_image.width() + 40
hauteur = my_image.height() + 40

nouvelle_image1 = QImage(largeur, hauteur, QImage.Format_ARGB32)
nouvelle_image1.fill(QColor(21, 187, 161))

painter = QPainter(nouvelle_image1)

x_offset = (largeur - my_image.width()) // 2
y_offset = (hauteur - my_image.height()) // 2

painter.drawImage(x_offset, y_offset, my_image) 
painter.end()

nouvelle_image1.save(path_nouvelle_image1)


# Image 2
url = r'https://j4binv.master-geomatique.org/images/2023/03/13/CY-Cergy-Paris-172Blanc.png'
response = requests.get(url)

image_originale2 = str(repLayers / 'logo_cyu.png')
path_nouvelle_image2 = str(repLayers / 'logo_cyu_fond_vert.png')

# Dowload image
if response.status_code == 200:
    with open(image_originale2, 'wb') as file:
        file.write(response.content)
else:
    raise Exception('Impossible de télécharger la photo !')

# Set a black background
my_image = QImage(image_originale2)
largeur = my_image.width()
hauteur = my_image.height()

nouvelle_image2 = QImage(largeur, hauteur, QImage.Format_ARGB32)
nouvelle_image2.fill(QColor(21, 187, 161))

painter = QPainter(nouvelle_image2)

x_offset = (largeur - my_image.width()) // 2
y_offset = (hauteur - my_image.height()) // 2

painter.drawImage(x_offset, y_offset, my_image) 
painter.end()

nouvelle_image2.save(path_nouvelle_image2)


# Prepare project and layout generation
project = QgsProject.instance()
iface.mapCanvas().refresh()
manager = project.layoutManager()

# Remove existing layers
project.removeAllMapLayers()
project.clear()

time.sleep(1)
iface.mapCanvas().refresh()

crs = QgsCoordinateReferenceSystem.fromEpsgId(4326)
project.setCrs(crs)
project.setEllipsoid('EPSG:4326')

time.sleep(1)
iface.mapCanvas().refresh()

# Directory _cartes
_cartes = repExport / '_cartes'
if os.path.isdir(_cartes) == True:
    shutil.rmtree(_cartes)
if os.path.isdir(_cartes) == False:
    os.mkdir(_cartes)

# Directory peaks_iris
_peaks_iris = repLayers / '_peaks_iris'
if os.path.isdir(_peaks_iris) == True:
    shutil.rmtree(_peaks_iris)
if os.path.isdir(_peaks_iris) == False:
    os.mkdir(_peaks_iris)

time.sleep(1)

# For OSM
urlWithParams = "type=xyz&url=http://tile.openstreetmap.org/{z}/{x}/{y}.png"
osm = QgsRasterLayer(urlWithParams, "OpenStreetMap", "wms")

# Path of layers
peaks = QgsVectorLayer(str(repLayers / 'peaks/peaks.shp'), 'Peaks', 'ogr')
glaciers = QgsVectorLayer(str(repLayers / 'glaciers/glaciers.shp'), 'Glaciers', 'ogr')
eau = QgsVectorLayer(str(repLayers / 'TRONCON_HYDROGRAPHIQUE/TRONCON_HYDROGRAPHIQUE.shp'), 'Fleuves', 'ogr')
troncons_routes = QgsVectorLayer(str(repLayers / 'TRONCON_ROUTE/TRONCON_ROUTE.shp'), 'Grandes routes', 'ogr')
iris = QgsVectorLayer(str(repIris / 'iris/iris.shp'), 'IRIS', 'ogr')

# Open layers
project.addMapLayer(peaks)
project.addMapLayer(glaciers)
project.addMapLayer(eau)
project.addMapLayer(troncons_routes)
project.addMapLayer(iris)

project.addMapLayer(osm)
osm.setOpacity(0.75)

# Intersect peaks and IRIS
peaks_iris_path = str(_peaks_iris / 'peaks_iris.shp')

processing.run('qgis:intersection', { \
"INPUT": peaks, \
"OVERLAY": iris, \
"INPUT_FIELDS": ["OSM_ID", "NAME", "OTHER_TAGS"], \
"OVERLAY_FIELDS": ["CODE_IRIS", "NOM_COM"], \
"OVERLAY_FIELDS_PREFIX": "", \
"OUTPUT": peaks_iris_path})

# Remove layers
project.removeMapLayer(peaks)
project.removeMapLayer(iris)

# Open the new intersected layer
peaks_iris = QgsVectorLayer(peaks_iris_path, "Sommets", "ogr")
project.addMapLayer(peaks_iris)

# Register layer
mes_sommets = project.mapLayersByName("Sommets")[0]

# Copy peaks layer
sommet_unique = mes_sommets.clone()
sommet_unique.setName('Pour sélection')
project.addMapLayer(sommet_unique)

# Manage display order
root = project.layerTreeRoot()
root.setHasCustomLayerOrder (True)
order = root.customLayerOrder()
order.insert(0, order.pop(order.index(sommet_unique)))
order.insert(1, order.pop(order.index(peaks_iris)))
order.insert(2, order.pop(order.index(eau)))
order.insert(3, order.pop(order.index(troncons_routes)))
order.insert(4, order.pop(order.index(glaciers)))
order.insert(5, order.pop(order.index(osm)))
root.setCustomLayerOrder( order )

# Glaciers symbology
symbol_glaciers = QgsFillSymbol.createSimple({'line_style': 'solid', 'line_width': '0.4', 'color': '0,136,204,30'})
glaciers.renderer().setSymbol(symbol_glaciers)
glaciers.triggerRepaint()
iface.layerTreeView().refreshLayerSymbology(glaciers.id())
time.sleep(0.5)

# Eau symbology
symbol_eau = QgsLineSymbol.createSimple({'line_style': 'solid', 'line_width': '2', 'color': '#0088CC'})
eau.renderer().setSymbol(symbol_eau)
eau.triggerRepaint()
iface.layerTreeView().refreshLayerSymbology(eau.id())
time.sleep(0.5)

# Routes symbology
symbol_troncons_routes = QgsLineSymbol.createSimple({'line_style': 'dash', 'line_width': '1', 'color': 'black'})
troncons_routes.renderer().setSymbol(symbol_troncons_routes)
troncons_routes.triggerRepaint()
iface.layerTreeView().refreshLayerSymbology(troncons_routes.id())
time.sleep(0.5)



# Glaciers labels
glacierLabelSettings = QgsPalLayerSettings()
glacierLabelSettings.fieldName = 'name'
glacierLabelSettings.enabled = True

glacierText = QgsTextFormat()
glacierText.setFont(QFont('Verdana', 8))
glacierText.setSize(8)

glacierLabelSettings.setFormat(glacierText)

glacierSettings = QgsVectorLayerSimpleLabeling(glacierLabelSettings)
glaciers.setLabeling(glacierSettings)
glaciers.setLabelsEnabled(True)

glaciers.triggerRepaint()
iface.mapCanvas().refresh()
time.sleep(0.5)


# Zoom on peaks
extent_mes_sommets = mes_sommets.extent()
iface.mapCanvas().setExtent(extent_mes_sommets)
iface.mapCanvas().refresh()
time.sleep(0.5)

# Make layouts and maps
jeuDeTest = list(mes_sommets.getFeatures())
for feat in jeuDeTest[:3]:
# for feat in mes_sommets.getFeatures():
    id_peak = feat['OSM_ID']
    peak_name = feat['NAME']
    commune = feat['NOM_COM']
    
    layoutName = str(peak_name)

    print('\n' + layoutName.replace("'", '') + ' : OK !')

    # Sort the single peak layer
    expr_filtre = u"OSM_ID = '{}'".format(id_peak)
    sommet_unique.setSubsetString(expr_filtre)
    
    # Rename the single peak layer
    sommet_unique.setName(layoutName)
    
    # Single peak Symbology
    symbol_sommet_unique = QgsMarkerSymbol.createSimple({'name': 'Triangle', 'color': 'blue', 'outline_color': 'black', 'size': '8'})
    sommet_unique.renderer().setSymbol(symbol_sommet_unique)
    sommet_unique.triggerRepaint()

    iface.layerTreeView().refreshLayerSymbology(sommet_unique.id())
    iface.mapCanvas().refresh()

    # Filter the peaks layer
    expr_exclusion = u"OSM_ID <> '{}'".format(id_peak)
    mes_sommets.setSubsetString(expr_exclusion)
    
    # Rename the peaks layer
    mes_sommets.setName('Autres sommets')
    
    # Peaks Symbology
    symbol_mes_sommets = QgsMarkerSymbol.createSimple({'name': 'Triangle', 'color': '#0088CC', 'outline_color': 'black', 'size': '5'})
    mes_sommets.renderer().setSymbol(symbol_mes_sommets)
    mes_sommets.triggerRepaint()

    iface.layerTreeView().refreshLayerSymbology(mes_sommets.id())
    iface.mapCanvas().refresh()

    # Checking for non-existence of a layout with the same name
    layouts_list = manager.printLayouts()
    for l in layouts_list:
        if l.name() == layoutName:
            manager.removeLayout(l)

    # Generating an empty layout
    layout = QgsPrintLayout(project)
    layout.initializeDefaults()
    layout.setName(layoutName)
    manager.addLayout(layout)

    # Load an empty map
    map = QgsLayoutItemMap(layout)
    map.setRect(20, 20, 20, 20)

    # Zoom on single peak in canvas
    extent = sommet_unique.extent()
    iface.mapCanvas().setExtent(extent)
    iface.mapCanvas().zoomScale(20000)
    iface.mapCanvas().refresh()

    # Zoom on single peak in the map (to force zoom on the 1st map)
    map.setExtent(iface.mapCanvas().extent())
    map.setScale(100000)

    # Layout
    layout.addLayoutItem(map)

    # Resize the map
    map.attemptMove(QgsLayoutPoint(5, 27, QgsUnitTypes.LayoutMillimeters))
    map.attemptResize(QgsLayoutSize(220, 178, QgsUnitTypes.LayoutMillimeters))
    map.setFrameEnabled(True)

    # Custom Legend
    tree_layers = project.layerTreeRoot().children()
    checked_layers = [layer.name() for layer in tree_layers if layer.isVisible()]
    layers_to_remove = [layer for layer in project.mapLayers().values() if layer.name() not in checked_layers]
    legend = QgsLayoutItemLegend(layout)
    legend.setTitle('Légende')
    layout.addLayoutItem(legend)
    legend.attemptMove(QgsLayoutPoint(230, 30, QgsUnitTypes.LayoutMillimeters))

    # This line will prevent unused layers from being removed from your QGIS layers panel
    legend.setAutoUpdateModel(False) 
    m = legend.model()
    g = m.rootGroup()
    for l in layers_to_remove:
        g.removeLayer(l)

    g.removeLayer(osm)
    legend.adjustBoxSize()


    # OSM XML
    monUrl = requests.get("https://www.openstreetmap.org/api/0.6/node/" + id_peak)
    lectureXml = xml.etree.ElementTree.fromstring(monUrl.content)

    # Altitude
    monAltitude = ''
    for balise in lectureXml.iter('tag'):
        if balise.attrib['k'] == 'ele':
            monAltitude = ' (' + str(balise.attrib['v']) + ' mètres)'
            print(monAltitude.replace(' (', '').replace(')', ''))

    # Copyright
    mesCopyright = ''
    for balise in lectureXml.iter('osm'):
        if balise.attrib['copyright']:
            mesCopyright = str(balise.attrib['copyright'])
            print(mesCopyright)

    # OSM user
    monUser = ''
    for balise in lectureXml.iter('node'):
        if balise.attrib['user']:
            monUser = str(balise.attrib['user'])
            print(monUser)


    # Wikidata ID on OSM XML then Wikidata image
    WikidataID = 'xxx'
    WikidataImage = 'xxx'
    try:
        for balise in lectureXml.iter('tag'):
            if balise.attrib['k'] == 'wikidata':
                
                WikidataID = str(balise.attrib['v'])

                url = 'https://www.wikidata.org/wiki/Special:EntityData/' + WikidataID + '.json'

                headers = {'User-Agent': 'georges.hinot@hg-map.fr'}

                response = requests.get(url, headers=headers)
                my_data = json.loads(response.text)

                entity = my_data['entities'][WikidataID]

                image_name = entity["claims"].get("P18", [{}])[0].get("mainsnak", {}).get("datavalue", {}).get("value", None)

                print('Photo:', image_name)

                if image_name:
                    WikidataImage = 'https://commons.wikimedia.org/wiki/Special:FilePath/' + str(image_name).replace(' ', '_')
                else:
                    WikidataImage = 'xxx'

                print('URL de la photo:', WikidataImage)

    except Exception as ex:
        print('EXCEPT:')
        print(ex)
        WikidataImage = 'xxx'
    
    if WikidataImage != 'xxx':
            print('Image :' + WikidataImage)


    # Title
    title = QgsLayoutItemLabel(layout)
    title.setText(layoutName + monAltitude)
    title.setFont(myTitleBoldFont)
    title.adjustSizeToText()
    layout.addLayoutItem(title)
    title.attemptMove(QgsLayoutPoint(5, 4, QgsUnitTypes.LayoutMillimeters))
    title.attemptResize(QgsLayoutSize(220, 20, QgsUnitTypes.LayoutMillimeters))
     
    # Subtitle
    subtitle = QgsLayoutItemLabel(layout)
    subtitle.setText('Commune de ' + commune)
    subtitle.setFont(QFont('Verdana', 17))
    subtitle.setFontColor(QColor(6, 77, 114))
    subtitle.adjustSizeToText()
    layout.addLayoutItem(subtitle)
    subtitle.attemptMove(QgsLayoutPoint(5, 17, QgsUnitTypes.LayoutMillimeters))
    subtitle.attemptResize(QgsLayoutSize(220, 20, QgsUnitTypes.LayoutMillimeters))

    # Meta 1
    meta1 = QgsLayoutItemLabel(layout)
    meta1.setText(mesCopyright + ' (' + monUser + ')')
    meta1.setFont(myMetaFont)
    meta1.adjustSizeToText()
    layout.addLayoutItem(meta1)
    meta1.attemptMove(QgsLayoutPoint(20, 196, QgsUnitTypes.LayoutMillimeters))
    meta1.attemptResize(QgsLayoutSize(204, 8, QgsUnitTypes.LayoutMillimeters))
    meta1.setHAlign(Qt.AlignRight)
    
    # 

    # Meta 2
    meta2 = QgsLayoutItemLabel(layout)
    meta2.setText('Python c\'est la vie le boss ! Carte générée le ' + aujourdhui_fr + ' avec QGIS ' + Qgis.QGIS_VERSION)
    meta2.setFont(myMetaFont)
    meta2.adjustSizeToText()
    layout.addLayoutItem(meta2)
    meta2.attemptMove(QgsLayoutPoint(20, 200, QgsUnitTypes.LayoutMillimeters))
    meta2.attemptResize(QgsLayoutSize(204, 8, QgsUnitTypes.LayoutMillimeters))
    meta2.setHAlign(Qt.AlignRight)

    # Scale bar
    scalebar = QgsLayoutItemScaleBar(layout)
    scalebar.setStyle('Single Box')
    scalebar.setUnits(QgsUnitTypes.DistanceMeters)
    scalebar.setNumberOfSegments(2)
    scalebar.setNumberOfSegmentsLeft(0)
    scalebar.setUnitsPerSegment(250)
    scalebar.setLinkedMap(map)
    scalebar.setUnitLabel('mètres')
    scalebar.setFont(QFont('Verdana', 12))
    scalebar.update()
    layout.addLayoutItem(scalebar)
    scalebar.attemptMove(QgsLayoutPoint(10, 188, QgsUnitTypes.LayoutMillimeters))

    # Logo 1
    my_logo1 = QgsLayoutItemPicture(layout)
    my_logo1.setPicturePath(path_nouvelle_image1)
    layout.addLayoutItem(my_logo1)
    my_logo1.attemptResize(QgsLayoutSize(17, 18, QgsUnitTypes.LayoutMillimeters))
    my_logo1.attemptMove(QgsLayoutPoint(277,3, QgsUnitTypes.LayoutMillimeters))

    # Logo 2
    my_logo2 = QgsLayoutItemPicture(layout)
    my_logo2.setPicturePath(path_nouvelle_image2)
    layout.addLayoutItem(my_logo2)
    my_logo2.attemptResize(QgsLayoutSize(54, 18, QgsUnitTypes.LayoutMillimeters))
    my_logo2.attemptMove(QgsLayoutPoint(220,3, QgsUnitTypes.LayoutMillimeters))

    # Image Wikidata
    if WikidataImage == 'xxx':
        pass
    else:
        jolieImage = QgsLayoutItemPicture(layout)
        jolieImage.setPicturePath(WikidataImage)
        layout.addLayoutItem(jolieImage)
        jolieImage.attemptResize(QgsLayoutSize(75, 75, QgsUnitTypes.LayoutMillimeters))
        jolieImage.attemptMove(QgsLayoutPoint(9, 31, QgsUnitTypes.LayoutMillimeters))

    # Wikipedia summary
    myWikiContent = ''
    try:
        wikipedia.set_lang("fr")
        myWikiContent = wikipedia.summary(layoutName, sentences=3)

        myWikiContent = myWikiContent.replace('== Géographie ==', '').replace('\n\n', '\n')
        myWikiContent = myWikiContent.replace('== Description ==', '').replace('\n\n', '\n')
        myWikiContent = myWikiContent.replace('== Toponymie ==', '').replace('\n\n', '\n')
        myWikiContent = myWikiContent.replace('== Notes et références ==', '').replace('\n\n', '\n')
        myWikiContent = myWikiContent.replace('== Annexes ==', '').replace('\n\n', '\n')
        
        myWikiContent = myWikiContent.replace('=== Situation ===', '').replace('\n\n', '\n')
        myWikiContent = myWikiContent.replace('=== Bibliographie ===', '').replace('\n\n', '\n')
        
        myWikiContent = myWikiContent.replace('\n\n', '\n')

        print(str(myWikiContent).replace("'", ''))

        # Check the relevance of the result
        if layoutName.lower() in str(myWikiContent).lower() or 'écrins' in str(myWikiContent).lower():
            None
        else:
            myWikiContent = ''

    except Exception:
        print('Problème Wikipédia !')
        pass

    # Text
    if myWikiContent != '':
        TextCustom = QgsLayoutItemLabel(layout)
        TextCustom.setText("Wikipédia :")
        TextCustom.setFont(myBoldFont)
        layout.addLayoutItem(TextCustom)
        TextCustom.attemptMove(QgsLayoutPoint(230, 90, QgsUnitTypes.LayoutMillimeters))
        TextCustom.attemptResize(QgsLayoutSize(60, 100, QgsUnitTypes.LayoutMillimeters))

        TextCustom = QgsLayoutItemLabel(layout)
        TextCustom.setText(myWikiContent)
        TextCustom.setFont(QFont('Verdana', 11))
        layout.addLayoutItem(TextCustom)
        TextCustom.attemptMove(QgsLayoutPoint(230, 95, QgsUnitTypes.LayoutMillimeters))
        TextCustom.attemptResize(QgsLayoutSize(60, 100, QgsUnitTypes.LayoutMillimeters))

    if myWikiContent == '':
        TextCustom = QgsLayoutItemLabel(layout)
        TextCustom.setText('Euuuuh...')
        TextCustom.setFont(QFont('Verdana', 11))
        layout.addLayoutItem(TextCustom)
        TextCustom.attemptMove(QgsLayoutPoint(230, 90, QgsUnitTypes.LayoutMillimeters))
        TextCustom.attemptResize(QgsLayoutSize(60, 100, QgsUnitTypes.LayoutMillimeters))


    # PDF Export
    manager = project.layoutManager()
    layoutManager = manager.layoutByName(layoutName)
    exporter = QgsLayoutExporter(layoutManager)
    exporter.exportToPdf(str(_cartes / (aujourdhui_en + '-' + layoutName + '.pdf')),QgsLayoutExporter.PdfExportSettings())

# Finish with a beautiful canvas in QGIS, lol
# We delete here processed layers, because not easy to "really" delete them (with the shape) before the loop, dunno why lol
project.removeMapLayer(sommet_unique)
project.removeMapLayer(mes_sommets)

peaks = QgsVectorLayer(str(repLayers / 'peaks/peaks.shp'), 'Sommets', 'ogr')
project.addMapLayer(peaks)
my_peaks = project.mapLayersByName('Sommets')[0]

symbol_peaks = QgsMarkerSymbol.createSimple({'name': 'Triangle', 'color': 'green', 'outline_color': 'black', 'size': '8'})
my_peaks.renderer().setSymbol(symbol_peaks)

# my_peaks.setSubsetString('')
my_peaks.triggerRepaint()
iface.layerTreeView().refreshLayerSymbology(my_peaks.id())
iface.mapCanvas().refresh()

# Manage display order
root = project.layerTreeRoot()
root.setHasCustomLayerOrder (True)
order = root.customLayerOrder()
order.insert(0, order.pop(order.index(my_peaks)))
root.setCustomLayerOrder(order)

extent_my_peaks = my_peaks.extent()
iface.mapCanvas().setExtent(extent_my_peaks)
iface.mapCanvas().refresh()

glaciers.setLabelsEnabled(False)
glaciers.triggerRepaint()
iface.mapCanvas().refresh()

# Remove images
os.remove(image_originale1)
os.remove(path_nouvelle_image1)
os.remove(image_originale2)
os.remove(path_nouvelle_image2)