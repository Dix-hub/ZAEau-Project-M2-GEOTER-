from qgis.core import *
from qgis.processing import alg
from PyQt5.QtCore import QVariant
import re

@alg(name="exploser_hstore", label="Exploser un champ Hstore", group="Scripts personnalisés", group_label="Mes Scripts")
@alg.input(type=alg.VECTOR_LAYER, name="INPUT", label="Couche d'entrée")
@alg.input(type=alg.STRING, name="HSTORE_FIELD", label="Champ Hstore", default="other_tags")
@alg.output(type=alg.VECTOR_LAYER, name="OUTPUT", label="Couche de sortie")

def processAlgorithm(self, parameters, context, feedback, values=None):
    """
    Cet algorithme extrait les clés d'un champ Hstore et les convertit en champs séparés.
    Ensuite, il supprime le champ Hstore d'origine.

    INPUT: Couche vectorielle avec un champ Hstore
    HSTORE_FIELD: Nom du champ contenant les données Hstore
    OUTPUT: Nouvelle couche avec un champ par clé Hstore
    """
    layer = self.parameterAsVectorLayer(parameters, 'INPUT', context)
    hstore_field = parameters['HSTORE_FIELD']

    if not layer:
        feedback.reportError("La couche est invalide.", fatalError=True)
        return {}

    # Fonction pour convertir une chaîne Hstore OSM en dictionnaire
    def parse_hstore(hstore_str):
        hstore_dict = {}
        matches = re.findall(r'"([^"]+)"=>"([^"]+)"', hstore_str)  # Extrait les paires clé-valeur
        for key, value in matches:
            hstore_dict[key] = value
        return hstore_dict

    # Extraire toutes les clés uniques du champ Hstore
    keys = set()
    for feature in layer.getFeatures():
        hstore_value = feature[hstore_field]
        if hstore_value:
            try:
                hstore_dict = parse_hstore(hstore_value)  # Utiliser le parseur
                keys.update(hstore_dict.keys())
            except Exception as e:
                feedback.reportError(f"Erreur de parsing : {e}")

    # Ajouter de nouveaux champs
    layer_provider = layer.dataProvider()
    new_fields = [QgsField(key, QVariant.String) for key in keys]
    layer_provider.addAttributes(new_fields)
    layer.updateFields()

    # Remplir les champs avec leurs valeurs
    for feature in layer.getFeatures():
        attrs = {}
        hstore_value = feature[hstore_field]
        if hstore_value:
            try:
                hstore_dict = parse_hstore(hstore_value)
                for key in keys:
                    attrs[layer.fields().indexFromName(key)] = hstore_dict.get(key, None)
            except Exception as e:
                feedback.reportError(f"Erreur de remplissage : {e}")
        layer_provider.changeAttributeValues({feature.id(): attrs})

    # Supprimer le champ Hstore d'origine
    layer_provider.deleteAttributes([layer.fields().indexFromName(hstore_field)])
    layer.updateFields()

    return {"OUTPUT": layer}
