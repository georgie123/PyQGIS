# -*- coding: utf-8 -*-
"""Crée un projet autonome QGIS 3.28 du cadastre de Cergy (95127).

Exécution PowerShell (installation QGIS présente sur ce poste) :
    & 'C:\Program Files\QGIS 3.28.13\apps\Python39\python.exe' .\_CreateMaps_Examples\CreateCadastre-Cergy.py

Ou depuis le shell OSGeo4W : python-qgis-ltr.bat CreateCadastre-Cergy.py
Aucun paquet Python supplémentaire à installer. Internet est nécessaire.
Le résultat est placé dans Downloads/Cadastre_Cergy_<date et heure>/.
Déplacer le dossier entier conserve les liens entre projet et données.

Source : https://cadastre.data.gouv.fr/datasets/cadastre-etalab
"""

import argparse
import gzip
import json
import os
from pathlib import Path
import sys
from datetime import datetime


CODE_INSEE = "95127"
SOURCE = "https://cadastre.data.gouv.fr/datasets/cadastre-etalab"
BASE_URL = (
    "https://cadastre.data.gouv.fr/data/etalab-cadastre/"
    "latest/geojson/communes/95/95127"
)
DLL_HANDLES = []


def dossier_downloads():
    """Respecte aussi un dossier Téléchargements Windows déplacé par l'utilisateur."""
    if os.name == "nt":
        import winreg

        cle = r"Software\Microsoft\Windows\CurrentVersion\Explorer\User Shell Folders"
        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, cle) as registre:
                chemin, _ = winreg.QueryValueEx(
                    registre, "{374DE290-123F-4565-9164-39C4925E467B}"
                )
            return Path(os.path.expandvars(chemin))
        except OSError:
            pass
    return Path.home() / "Downloads"


def preparer_qgis():
    """Permet aussi de lancer directement le python.exe livré avec QGIS."""
    if os.name == "nt":
        for racine in Path(sys.executable).resolve().parents:
            candidats = [racine / "apps" / "qgis-ltr", racine / "apps" / "qgis"]
            prefixe = next((p for p in candidats if (p / "python" / "qgis").is_dir()), None)
            if prefixe is None:
                continue
            repertoires = [racine / "bin", prefixe / "bin", racine / "apps/Qt5/bin"]
            os.environ["PATH"] = os.pathsep.join(map(str, repertoires)) + os.pathsep + os.environ.get("PATH", "")
            for repertoire in repertoires:
                if repertoire.is_dir() and hasattr(os, "add_dll_directory"):
                    DLL_HANDLES.append(os.add_dll_directory(str(repertoire)))
            sys.path.insert(0, str(prefixe / "python"))
            os.environ["QGIS_PREFIX_PATH"] = str(prefixe)
            os.environ["QT_PLUGIN_PATH"] = os.pathsep.join([
                str(prefixe / "qtplugins"), str(racine / "apps/Qt5/plugins")
            ])
            os.environ["GDAL_DATA"] = str(racine / "share/gdal")
            os.environ["PROJ_LIB"] = str(racine / "share/proj")
            break
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")


def telecharger(nom, dossier):
    # Import après la configuration des DLL QGIS (OpenSSL est livré avec QGIS).
    from urllib.request import Request, urlopen

    url = "{}/cadastre-{}-{}.json.gz".format(BASE_URL, CODE_INSEE, nom)
    print("Téléchargement : {}".format(nom), flush=True)
    requete = Request(url, headers={"User-Agent": "CreateCadastre-Cergy/1.0"})
    with urlopen(requete, timeout=120) as reponse:
        contenu = gzip.decompress(reponse.read())
        url_effective = reponse.geturl()
    donnees = json.loads(contenu)
    if donnees.get("type") != "FeatureCollection" or not isinstance(donnees.get("features"), list):
        raise RuntimeError("Réponse GeoJSON incorrecte pour {}".format(nom))
    if nom in ("communes", "parcelles", "batiments", "sections") and not donnees["features"]:
        raise RuntimeError("La couche {} est vide.".format(nom))
    fichier = dossier / (nom + ".geojson")
    fichier.write_bytes(contenu)
    return fichier, {"couche": nom, "url": url, "url_effective": url_effective,
                     "entites": len(donnees["features"])}


def creer_projet(dossier):
    from qgis.core import (
        Qgis, QgsCoordinateReferenceSystem, QgsCoordinateTransform,
        QgsFillSymbol, QgsPalLayerSettings, QgsProject, QgsReferencedRectangle,
        QgsTextBufferSettings, QgsTextFormat, QgsVectorFileWriter, QgsVectorLayer,
        QgsVectorLayerSimpleLabeling,
    )
    from qgis.PyQt.QtGui import QColor, QFont

    print("QGIS {}".format(Qgis.QGIS_VERSION), flush=True)
    projet = QgsProject.instance()
    projet.setTitle("Cadastre de Cergy — 95127")
    projet.setCrs(QgsCoordinateReferenceSystem("EPSG:2154"))
    projet.setFilePathStorage(Qgis.FilePathType.Relative)
    projet.setBackgroundColor(QColor("#ffffff"))
    sources = dossier / "sources"
    sources.mkdir()
    gpkg = dossier / "Cadastre_Cergy.gpkg"
    couches = {}
    provenance = []
    # Ordre de dessin : les premières couches ajoutées restent en dessous.
    definitions = [
        ("lieux_dits", "Lieux-dits", "no", "#999999", "0.15"),
        ("parcelles", "Parcelles", "solid", "#777777", "0.15"),
        ("batiments", "Bâtiments", "solid", "#80573d", "0.18"),
        ("sections", "Sections cadastrales", "no", "#c26b29", "0.45"),
        ("communes", "Limite de Cergy", "no", "#b02d40", "0.8"),
    ]
    for nom, titre, remplissage, contour, largeur in definitions:
        fichier, info = telecharger(nom, sources)
        provenance.append(info)
        if not info["entites"]:
            print("Couche vide ignorée : {}".format(nom), flush=True)
            continue
        originale = QgsVectorLayer(str(fichier), titre, "ogr")
        if not originale.isValid() or not originale.crs().isValid():
            raise RuntimeError("Couche source invalide : {}".format(fichier))
        options = QgsVectorFileWriter.SaveVectorOptions()
        options.driverName = "GPKG"
        options.layerName = nom
        options.fileEncoding = "UTF-8"
        options.actionOnExistingFile = (
            QgsVectorFileWriter.CreateOrOverwriteLayer if gpkg.exists()
            else QgsVectorFileWriter.CreateOrOverwriteFile
        )
        options.ct = QgsCoordinateTransform(originale.crs(), projet.crs(), projet)
        resultat = QgsVectorFileWriter.writeAsVectorFormatV3(
            originale, str(gpkg), projet.transformContext(), options
        )
        if resultat[0] != QgsVectorFileWriter.NoError:
            raise RuntimeError("Export {} : {}".format(nom, resultat[1]))
        couche = QgsVectorLayer(str(gpkg) + "|layername=" + nom, titre, "ogr")
        if not couche.isValid() or couche.featureCount() != info["entites"]:
            raise RuntimeError("Couche exportée incorrecte : {}".format(nom))
        couleur = "#fff9ed" if nom == "parcelles" else "#d8ad89"
        couche.renderer().setSymbol(QgsFillSymbol.createSimple({
            "style": remplissage, "color": couleur, "outline_color": contour,
            "outline_width": largeur, "outline_width_unit": "MM",
        }))
        champ = {"parcelles": "numero", "sections": "code", "lieux_dits": "nom"}.get(nom)
        if champ and couche.fields().indexFromName(champ) >= 0:
            etiquettes = QgsPalLayerSettings()
            etiquettes.fieldName = champ
            etiquettes.scaleVisibility = True
            etiquettes.minimumScale = 5000 if nom == "parcelles" else 30000
            etiquettes.maximumScale = 1
            texte = QgsTextFormat()
            texte.setFont(QFont("Arial", 8))
            texte.setSize(8)
            texte.setColor(QColor(contour))
            tampon = QgsTextBufferSettings()
            tampon.setEnabled(True)
            tampon.setSize(0.6)
            tampon.setColor(QColor("white"))
            texte.setBuffer(tampon)
            etiquettes.setFormat(texte)
            couche.setLabeling(QgsVectorLayerSimpleLabeling(etiquettes))
            couche.setLabelsEnabled(True)
        metadonnees = couche.metadata()
        metadonnees.setTitle(titre + " — Cergy")
        metadonnees.setAbstract("Cadastre ouvert DGFiP / Etalab. Source : " + info["url"])
        couche.setMetadata(metadonnees)
        projet.addMapLayer(couche)
        couches[nom] = couche
        print("  {} : {} entités".format(titre, couche.featureCount()), flush=True)

    emprise = couches["communes"].extent()
    emprise.scale(1.08)
    projet.viewSettings().setDefaultViewExtent(QgsReferencedRectangle(emprise, projet.crs()))
    chemin_projet = dossier / "Cadastre_Cergy.qgz"
    if not projet.write(str(chemin_projet)):
        raise RuntimeError("Impossible d'enregistrer le projet : " + str(chemin_projet))
    (dossier / "sources.json").write_text(json.dumps({
        "commune": "Cergy", "code_insee": CODE_INSEE,
        "telecharge_le": datetime.now().astimezone().isoformat(),
        "source": SOURCE, "qgis": Qgis.QGIS_VERSION, "couches": provenance,
    }, ensure_ascii=False, indent=2), encoding="utf-8")
    projet.clear()
    print("\nProjet créé : {}".format(chemin_projet), flush=True)
    print("Ouvrir ce fichier .qgz dans QGIS. Conserver le .gpkg à ses côtés.")


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--sortie", type=Path, default=None,
                        help="Dossier parent du résultat (par défaut : Downloads).")
    args = parser.parse_args()
    preparer_qgis()
    try:
        from qgis.core import QgsApplication
    except ImportError as erreur:
        raise RuntimeError("Exécuter ce script avec le Python livré avec QGIS 3.28.") from erreur
    application = QgsApplication([], False)
    application.initQgis()
    try:
        parent = args.sortie if args.sortie is not None else dossier_downloads()
        dossier = parent.expanduser().resolve() / datetime.now().strftime("Cadastre_Cergy_%Y%m%d_%H%M%S_%f")
        dossier.mkdir(parents=True, exist_ok=False)
        print("Dossier de sortie : {}".format(dossier), flush=True)
        creer_projet(dossier)
    finally:
        application.exitQgis()


if __name__ == "__main__":
    main()
