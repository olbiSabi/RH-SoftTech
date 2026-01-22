# employee/views_api/api/__init__.py
"""
Package des vues API modales pour l'application employee.
Expose les fonctions de vue générées par GenericModalCRUDView.
"""

# Classe de base
from .base import GenericModalCRUDView, make_modal_view_functions

# Vues Téléphone
from .telephone_api import (
    api_telephone_detail,
    api_telephone_create_modal,
    api_telephone_update_modal,
    api_telephone_delete_modal,
    TelephoneModalView,
)

# Vues Email
from .email_api import (
    api_email_detail,
    api_email_create_modal,
    api_email_update_modal,
    api_email_delete_modal,
    EmailModalView,
)

# Vues Adresse
from .adresse_api import (
    api_adresse_detail,
    api_adresse_create_modal,
    api_adresse_update_modal,
    api_adresse_delete_modal,
    AdresseModalView,
)

# Vues Contrat
from .contrat_api import (
    api_contrat_detail,
    api_contrat_create_modal,
    api_contrat_update_modal,
    api_contrat_delete_modal,
    ContratModalView,
)

# Vues Affectation
from .affectation_api import (
    api_affectation_detail,
    api_affectation_create_modal,
    api_affectation_update_modal,
    api_affectation_delete_modal,
    AffectationModalView,
)

# Vues Document (sans GenericModalCRUDView car upload fichier)
from .document_api import (
    api_document_create_modal,
    api_document_delete_modal,
)

# Vues Famille (ZYFA)
from .famille_api import (
    api_famille_detail,
    api_famille_create_modal,
    api_famille_update_modal,
    api_famille_delete_modal,
)

# Vues Historique Noms/Prénoms (ZYNP)
from .znp_api import (
    api_znp_detail,
    api_znp_create_modal,
    api_znp_update_modal,
    api_znp_delete_modal,
)

# Vues Personnes à prévenir (ZYPP)
from .personne_prevenir_api import (
    api_personne_prevenir_detail,
    api_personne_prevenir_create_modal,
    api_personne_prevenir_update_modal,
    api_personne_prevenir_delete_modal,
)

# Vues Identité Bancaire (ZYIB)
from .identite_bancaire_api import (
    api_identite_bancaire_detail,
    api_identite_bancaire_create_or_update,
    api_identite_bancaire_delete,
)

# Vues Photo
from .photo_api import (
    modifier_photo_ajax,
    supprimer_photo_ajax,
)

# Helpers
from .helper_api import (
    api_postes_by_departement,
)


__all__ = [
    # Base
    'GenericModalCRUDView',
    'make_modal_view_functions',

    # Téléphone
    'api_telephone_detail',
    'api_telephone_create_modal',
    'api_telephone_update_modal',
    'api_telephone_delete_modal',
    'TelephoneModalView',

    # Email
    'api_email_detail',
    'api_email_create_modal',
    'api_email_update_modal',
    'api_email_delete_modal',
    'EmailModalView',

    # Adresse
    'api_adresse_detail',
    'api_adresse_create_modal',
    'api_adresse_update_modal',
    'api_adresse_delete_modal',
    'AdresseModalView',

    # Contrat
    'api_contrat_detail',
    'api_contrat_create_modal',
    'api_contrat_update_modal',
    'api_contrat_delete_modal',
    'ContratModalView',

    # Affectation
    'api_affectation_detail',
    'api_affectation_create_modal',
    'api_affectation_update_modal',
    'api_affectation_delete_modal',
    'AffectationModalView',

    # Document
    'api_document_create_modal',
    'api_document_delete_modal',

    # Famille
    'api_famille_detail',
    'api_famille_create_modal',
    'api_famille_update_modal',
    'api_famille_delete_modal',

    # Historique Noms/Prénoms
    'api_znp_detail',
    'api_znp_create_modal',
    'api_znp_update_modal',
    'api_znp_delete_modal',

    # Personnes à prévenir
    'api_personne_prevenir_detail',
    'api_personne_prevenir_create_modal',
    'api_personne_prevenir_update_modal',
    'api_personne_prevenir_delete_modal',

    # Identité Bancaire
    'api_identite_bancaire_detail',
    'api_identite_bancaire_create_or_update',
    'api_identite_bancaire_delete',

    # Photo
    'modifier_photo_ajax',
    'supprimer_photo_ajax',

    # Helpers
    'api_postes_by_departement',
]
