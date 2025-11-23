import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HR_ONIAN.settings')
django.setup()

from django.conf import settings

print("=" * 80)
print("VÉRIFICATION DE LA CONFIGURATION EMAIL")
print("=" * 80)

print(f"\nEMAIL_BACKEND: {settings.EMAIL_BACKEND}")
print(f"DEFAULT_FROM_EMAIL: {settings.DEFAULT_FROM_EMAIL}")

if hasattr(settings, 'EMAIL_HOST'):
    print(f"EMAIL_HOST: {settings.EMAIL_HOST}")
if hasattr(settings, 'EMAIL_PORT'):
    print(f"EMAIL_PORT: {settings.EMAIL_PORT}")

print("\n" + "=" * 80)
print("LOCALISATION DU FICHIER SETTINGS.PY")
print("=" * 80)

import HR_ONIAN.settings as settings_module
print(f"\nFichier settings utilisé: {settings_module.__file__}")

# Lire directement le fichier pour voir ce qui est dedans
print("\n" + "=" * 80)
print("LIGNES CONTENANT 'EMAIL' DANS SETTINGS.PY")
print("=" * 80)

with open(settings_module.__file__, 'r') as f:
    lines = f.readlines()
    for i, line in enumerate(lines, 1):
        if 'EMAIL' in line and not line.strip().startswith('#'):
            print(f"Ligne {i}: {line.rstrip()}")