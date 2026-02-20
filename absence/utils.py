# absence/utils.py


def calculer_jours_acquis_au(employe, annee_reference, date_reference):
    """
    Calcule les jours acquis jusqu'à une date donnée.
    Délègue au service AcquisitionService (source unique de vérité).
    """
    from absence.services.acquisition_service import AcquisitionService
    return AcquisitionService.calculer_jours_acquis_au(employe, annee_reference, date_reference)


def calculer_mois_travailles_jusquau(employe, annee_reference, date_limite):
    """
    Calcule le nombre de mois travaillés jusqu'à une date donnée.
    Délègue au service AcquisitionService (source unique de vérité).
    """
    from absence.services.acquisition_service import AcquisitionService
    return AcquisitionService.calculer_mois_travailles_jusquau(employe, annee_reference, date_limite)


def calculer_jours_anciennete(employe, parametres):
    """
    Calcule les jours supplémentaires selon l'ancienneté.
    Délègue au service AcquisitionService (source unique de vérité).
    """
    from absence.services.acquisition_service import AcquisitionService
    return AcquisitionService.calculer_jours_anciennete(employe, parametres)