#############################################################################
##############################  DEPARTEMENT  ################################
#############################################################################
# Depuis la racine de votre projet Django (où se trouve manage.py)

# Importation simple (cherche automatiquement File/Departement.xlsx)
python manage.py import_departements

# Spécifier un autre fichier dans File/
python manage.py import_departements --fichier "Departements_2024.xlsx"

# Spécifier la feuille
python manage.py import_departements --fichier "Departement.xlsx" --feuille "Feuil1"

# Mode simulation (dry-run)
python manage.py import_departements --dry-run

# Mettre à jour uniquement les existants
python manage.py import_departements --update

# Avec verbosité détaillée
python manage.py import_departements --verbosity 2

# Chemin personnalisé (si votre fichier n'est pas dans File/)
python manage.py import_departements --chemin "/chemin/complet/vers/Departement.xlsx"

# Avec affichage des différences
python manage.py import_departements --show-diff

# Mode détaillé (verbosité 2)
python manage.py import_departements --verbosity 2

# Simulation avec analyse complète
python manage.py import_departements --dry-run --show-diff --verbosity 2




#############################################################################
#################################  POSTE   ##################################
#############################################################################

# Importation normale
python manage.py import_postes

# Avec affichage des différences
python manage.py import_postes --show-diff

# Mode simulation
python manage.py import_postes --dry-run --show-diff --verbosity 2

# Ignorer les départements manquants
python manage.py import_postes --ignore-missing-dept

# Mettre à jour uniquement les existants
python manage.py import_postes --update


# 1. Vérifier les départements référencés
python manage.py verifier_postes

# 2. Importer les postes (mode simulation d'abord)
python manage.py import_postes --dry-run --show-diff --verbosity 1

# 3. Importer pour de vrai
python manage.py import_postes --show-diff --verbosity 1

# 4. Options avancées
python manage.py import_postes --update  # Mettre à jour seulement les existants
python manage.py import_postes --ignore-missing-dept  # Ignorer les dépts manquants