import pandas as pd
from rapidfuzz import process
import unicodedata

fichier_reference = '/content/v_commune_2024.csv'
fichier_mal = '/content/communes_mal.csv'
fichier_sortie = '/content/communes_corrigees.csv'

communes_ref = pd.read_csv(fichier_reference, encoding='UTF-8', sep=',')
communes_ref['NCC'] = communes_ref['NCC'].apply(
    lambda x: unicodedata.normalize('NFC', x.strip()) if isinstance(x, str) else x
)

communes_mal = pd.read_csv(fichier_mal, encoding='utf-8', sep=";")
communes_mal = communes_mal.drop(columns=['Unnamed: 1', 'Unnamed: 2', 'Unnamed: 3', 'Unnamed: 4', 'Unnamed: 5', 'Unnamed: 6'], errors='ignore')

PARTICULES = {'la', 'le', 'les', 'de', 'du', 'des', 'd', 'l'}

PARTICULES_DEBUT = {
    'st': 'saint',
    'ste': 'sainte',
    'sts': 'saints',
    'stes': 'saintes'
}

def simplifier_nom(nom):
    if not isinstance(nom, str):
        return nom
    nom = unicodedata.normalize('NFD', nom)
    nom = ''.join(c for c in nom if unicodedata.category(c) != 'Mn')
    nom = nom.replace('-', '')
    mots = nom.lower().split()
    if mots and mots[0] in PARTICULES_DEBUT:
        mots[0] = PARTICULES_DEBUT[mots[0]]  
    mots = [mot for mot in mots if mot not in PARTICULES]
    return ''.join(mots)

communes_ref['NCC_SIMPLE'] = communes_ref['NCC'].apply(simplifier_nom)
liste_reference_simplifiee = communes_ref['NCC_SIMPLE'].tolist()
noms_originaux_par_simplifie = communes_ref.set_index('NCC_SIMPLE')['NCC'].to_dict()
libelle_par_ncc = communes_ref.set_index('NCC')['LIBELLE'].to_dict()

def corriger_nom_simplifie(nom, liste_simplifiee, correspondance_originaux):
    if not isinstance(nom, str):
        return nom
    nom_simplifie = simplifier_nom(nom)
    result = process.extractOne(nom_simplifie, liste_simplifiee, score_cutoff=85)
    if result:
        meilleure_correspondance, score, _ = result
        if abs(len(meilleure_correspondance) - len(nom_simplifie)) <= 3:
            return correspondance_originaux.get(meilleure_correspondance, nom)
    return nom 

communes_mal['COM_CORRIGEE'] = communes_mal['COM_NV'].apply(
    lambda x: corriger_nom_simplifie(x, liste_reference_simplifiee, noms_originaux_par_simplifie)
)

communes_mal['LIBELLE'] = communes_mal['COM_CORRIGEE'].map(libelle_par_ncc)

communes_mal['COM_CORRIGEE'] = communes_mal['COM_CORRIGEE'].apply(
    lambda x: unicodedata.normalize('NFC', x.strip()) if isinstance(x, str) else x
)

communes_mal.to_csv(fichier_sortie, index=False, encoding = 'UTF-8')

print(f"Les noms des communes corrigés, avec leur libellé, sont enregistrés dans '{fichier_sortie}'.")
