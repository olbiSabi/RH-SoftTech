from django.db import models
from django.utils import timezone
from ..models import JRImputation, JRTicket, JRProject
from employee.models import ZY00


class ImputationService:
    """Service pour la gestion des imputations de temps"""

    @staticmethod
    def peut_valider_imputation(utilisateur, imputation):
        """Vérifie si un utilisateur peut valider une imputation"""
        # Récupérer l'employé correspondant à l'utilisateur
        try:
            employe = ZY00.objects.get(user=utilisateur)
        except ZY00.DoesNotExist:
            return False

        # Vérifier les droits administratifs
        if (employe.has_role('DRH') or
            employe.has_role('GESTION_APP') or
            employe.has_role('DIRECTEUR')):
            return True

        # L'utilisateur doit être chef de projet du projet du ticket
        projet = imputation.ticket.projet
        return projet.chef_projet == employe
    
    @staticmethod
    def valider_imputation(imputation, valide_par, commentaire=""):
        """Valide une imputation et met à jour les statistiques"""
        imputation.statut_validation = 'VALIDE'
        imputation.valide_par = valide_par
        imputation.date_validation = timezone.now()
        imputation.commentaire_validation = commentaire
        imputation.save()
        
        # Mettre à jour le temps passé sur le ticket
        ImputationService.mettre_a_jour_temps_ticket(imputation.ticket)
        
        return imputation
    
    @staticmethod
    def rejeter_imputation(imputation, valide_par, commentaire):
        """Rejette une imputation"""
        imputation.statut_validation = 'REJETE'
        imputation.valide_par = valide_par
        imputation.date_validation = timezone.now()
        imputation.commentaire_validation = commentaire
        imputation.save()
        
        return imputation
    
    @staticmethod
    def mettre_a_jour_temps_ticket(ticket):
        """Met à jour le temps total passé sur un ticket"""
        total_temps = JRImputation.objects.filter(
            ticket=ticket,
            statut_validation='VALIDE'
        ).aggregate(
            total=models.Sum(models.F('heures') + models.F('minutes') / 60.0)
        )['total'] or 0
        
        ticket.temps_passe = total_temps
        ticket.save()
    
    @staticmethod
    def get_imputations_en_attente(projet=None):
        """Retourne les imputations en attente de validation"""
        queryset = JRImputation.objects.filter(statut_validation='EN_ATTENTE')
        
        if projet:
            queryset = queryset.filter(ticket__projet=projet)
        
        return queryset.select_related('employe', 'ticket', 'ticket__projet')
    
    @staticmethod
    def get_temps_par_employe(employe, date_debut=None, date_fin=None):
        """Retourne le temps imputé par un employé sur une période"""
        queryset = JRImputation.objects.filter(
            employe=employe,
            statut_validation='VALIDE'
        )
        
        if date_debut:
            queryset = queryset.filter(date_imputation__gte=date_debut)
        
        if date_fin:
            queryset = queryset.filter(date_imputation__lte=date_fin)
        
        return queryset.aggregate(
            total_heures=models.Sum(models.F('heures') + models.F('minutes') / 60.0),
            total_imputations=models.Count('id')
        )
    
    @staticmethod
    def get_temps_par_projet(projet, date_debut=None, date_fin=None):
        """Retourne le temps imputé sur un projet sur une période"""
        queryset = JRImputation.objects.filter(
            ticket__projet=projet,
            statut_validation='VALIDE'
        )
        
        if date_debut:
            queryset = queryset.filter(date_imputation__gte=date_debut)
        
        if date_fin:
            queryset = queryset.filter(date_imputation__lte=date_fin)
        
        return queryset.aggregate(
            total_heures=models.Sum(models.F('heures') + models.F('minutes') / 60.0),
            total_imputations=models.Count('id')
        )
    
    @staticmethod
    def get_rapport_hebdomadaire(employe, semaine=None):
        """Génère un rapport hebdomadaire des imputations d'un employé"""
        if semaine is None:
            semaine = timezone.now().date().isocalendar()[1]
        
        # Calculer les dates de la semaine
        annee = timezone.now().date().year
        date_debut = timezone.datetime.strptime(f'{annee}-{semeine}-1', "%Y-%W-%w").date()
        date_fin = date_debut + timezone.timedelta(days=6)
        
        imputations = JRImputation.objects.filter(
            employe=employe,
            date_imputation__range=[date_debut, date_fin],
            statut_validation='VALIDE'
        ).select_related('ticket', 'ticket__projet')
        
        # Regrouper par projet
        temps_par_projet = {}
        total_heures = 0
        
        for imp in imputations:
            projet = imp.ticket.projet
            if projet.code not in temps_par_projet:
                temps_par_projet[projet.code] = {
                    'nom': projet.nom,
                    'heures': 0,
                    'tickets': set()
                }
            
            temps_par_projet[projet.code]['heures'] += imp.total_heures
            temps_par_projet[projet.code]['tickets'].add(imp.ticket.code)
            total_heures += imp.total_heures
        
        # Convertir les sets en listes
        for projet_code in temps_par_projet:
            temps_par_projet[projet_code]['tickets'] = list(
                temps_par_projet[projet_code]['tickets']
            )
        
        return {
            'employe': f"{employe.nom} {employe.prenom}",
            'semaine': semaine,
            'annee': annee,
            'date_debut': date_debut,
            'date_fin': date_fin,
            'total_heures': total_heures,
            'total_imputations': imputations.count(),
            'temps_par_projet': temps_par_projet,
            'imputations_detail': imputations.order_by('date_imputation')
        }
    
    @staticmethod
    def get_rapport_mensuel(projet, mois=None, annee=None):
        """Génère un rapport mensuel des imputations d'un projet"""
        if mois is None:
            mois = timezone.now().month
        if annee is None:
            annee = timezone.now().year
        
        imputations = JRImputation.objects.filter(
            ticket__projet=projet,
            date_imputation__year=annee,
            date_imputation__month=mois,
            statut_validation='VALIDE'
        ).select_related('employe', 'ticket')
        
        # Regrouper par employé
        temps_par_employe = {}
        total_heures = 0
        
        for imp in imputations:
            employe_key = f"{imp.employe.nom} {imp.employe.prenom}"
            if employe_key not in temps_par_employe:
                temps_par_employe[employe_key] = {
                    'employe': imp.employe,
                    'heures': 0,
                    'tickets': set(),
                    'par_type_activite': {}
                }
            
            temps_par_employe[employe_key]['heures'] += imp.total_heures
            temps_par_employe[employe_key]['tickets'].add(imp.ticket.code)
            
            # Par type d'activité
            type_activite = imp.get_type_activite_display()
            if type_activite not in temps_par_employe[employe_key]['par_type_activite']:
                temps_par_employe[employe_key]['par_type_activite'][type_activite] = 0
            temps_par_employe[employe_key]['par_type_activite'][type_activite] += imp.total_heures
            
            total_heures += imp.total_heures
        
        # Convertir les sets en listes
        for employe_key in temps_par_employe:
            temps_par_employe[employe_key]['tickets'] = list(
                temps_par_employe[employe_key]['tickets']
            )
        
        return {
            'projet': projet,
            'mois': mois,
            'annee': annee,
            'total_heures': total_heures,
            'total_imputations': imputations.count(),
            'temps_par_employe': temps_par_employe,
            'par_type_activite': ImputationService.get_temps_par_type_activite(
                imputations
            )
        }
    
    @staticmethod
    def get_temps_par_type_activite(imputations):
        """Calcule le temps par type d'activité"""
        temps_par_type = {}
        
        for imp in imputations:
            type_activite = imp.get_type_activite_display()
            if type_activite not in temps_par_type:
                temps_par_type[type_activite] = 0
            temps_par_type[type_activite] += imp.total_heures
        
        return temps_par_type
    
    @staticmethod
    def detecter_anomalies(employe=None, projet=None):
        """Détecte des anomalies dans les imputations"""
        anomalies = []
        
        queryset = JRImputation.objects.filter(statut_validation='VALIDE')
        
        if employe:
            queryset = queryset.filter(employe=employe)
        
        if projet:
            queryset = queryset.filter(ticket__projet=projet)
        
        # Anomalie 1: Plus de 24h imputées en une journée
        heures_par_jour = queryset.values('employe', 'date_imputation').annotate(
            total_heures=models.Sum(models.F('heures') + models.F('minutes') / 60.0)
        ).filter(total_heures__gt=24)
        
        for item in heures_par_jour:
            anomalies.append({
                'type': 'depassement_journalier',
                'description': f"{item['total_heures']}h imputées le {item['date_imputation']}",
                'gravite': 'haute'
            })
        
        # Anomalie 2: Imputations le week-end
        imputations_weekend = queryset.filter(
            date_imputation__week_day__in=[6, 7]  # Samedi=6, Dimanche=7
        ).count()
        
        if imputations_weekend > 0:
            anomalies.append({
                'type': 'travail_weekend',
                'description': f"{imputations_weekend} imputation(s) le week-end",
                'gravite': 'moyenne'
            })
        
        # Anomalie 3: Jours sans imputation pour les employés actifs
        if employe is None:
            from employee.models import ZY00
            employes_actifs = ZY00.objects.filter(statut='ACTIF')
            
            for emp in employes_actifs:
                dernieres_imputations = queryset.filter(
                    employe=emp
                ).order_by('-date_imputation')[:5]
                
                if dernieres_imputations.count() > 0:
                    derniere_date = dernieres_imputations[0].date_imputation
                    jours_sans_imputation = (timezone.now().date() - derniere_date).days
                    
                    if jours_sans_imputation > 7:
                        anomalies.append({
                            'type': 'inactivite',
                            'description': f"{emp} n'a pas d'imputation depuis {jours_sans_imputation} jours",
                            'gravite': 'moyenne'
                        })
        
        return anomalies
    
    @staticmethod
    def exporter_donnees(format='excel', filtres=None):
        """Exporte les données d'imputations"""
        queryset = JRImputation.objects.filter(statut_validation='VALIDE')
        
        if filtres:
            if filtres.get('date_debut'):
                queryset = queryset.filter(date_imputation__gte=filtres['date_debut'])
            if filtres.get('date_fin'):
                queryset = queryset.filter(date_imputation__lte=filtres['date_fin'])
            if filtres.get('employe'):
                queryset = queryset.filter(employe=filtres['employe'])
            if filtres.get('projet'):
                queryset = queryset.filter(ticket__projet=filtres['projet'])
        
        queryset = queryset.select_related('employe', 'ticket', 'ticket__projet')
        
        if format == 'excel':
            return ImputationService._exporter_excel(queryset)
        elif format == 'csv':
            return ImputationService._exporter_csv(queryset)
        else:
            raise ValueError(f"Format non supporté: {format}")
    
    @staticmethod
    def _exporter_excel(queryset):
        """Exporte les données en format Excel"""
        import pandas as pd
        from io import BytesIO
        
        data = []
        for imp in queryset:
            data.append({
                'Date': imp.date_imputation,
                'Employé': f"{imp.employe.nom} {imp.employe.prenom}",
                'Projet': imp.ticket.projet.code,
                'Ticket': imp.ticket.code,
                'Type activité': imp.get_type_activite_display(),
                'Heures': imp.total_heures,
                'Description': imp.description,
                'Validé par': f"{imp.valide_par.nom} {imp.valide_par.prenom}" if imp.valide_par else '',
                'Date validation': imp.date_validation,
            })
        
        df = pd.DataFrame(data)
        
        output = BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df.to_excel(writer, sheet_name='Imputations', index=False)
            
            # Ajuster la largeur des colonnes
            worksheet = writer.sheets['Imputations']
            for idx, col in enumerate(df.columns):
                max_len = max(
                    df[col].astype(str).map(len).max(),
                    len(str(col))
                )
                worksheet.set_column(idx, idx, max_len + 2)
        
        output.seek(0)
        return output
    
    @staticmethod
    def _exporter_csv(queryset):
        """Exporte les données en format CSV"""
        import csv
        from io import StringIO
        
        output = StringIO()
        writer = csv.writer(output)
        
        # En-têtes
        writer.writerow([
            'Date', 'Employé', 'Projet', 'Ticket', 'Type activité',
            'Heures', 'Description', 'Validé par', 'Date validation'
        ])
        
        # Données
        for imp in queryset:
            writer.writerow([
                imp.date_imputation,
                f"{imp.employe.nom} {imp.employe.prenom}",
                imp.ticket.projet.code,
                imp.ticket.code,
                imp.get_type_activite_display(),
                imp.total_heures,
                imp.description,
                f"{imp.valide_par.nom} {imp.valide_par.prenom}" if imp.valide_par else '',
                imp.date_validation,
            ])
        
        output.seek(0)
        return output
