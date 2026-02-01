from django.db import models
from django.utils import timezone
from django.shortcuts import get_object_or_404
from ..models import JRClient, JRProject, JRTicket


class ClientService:
    """Service pour la gestion des clients"""
    
    @staticmethod
    def get_clients_actifs():
        """Retourne les clients actifs avec leurs statistiques"""
        clients = JRClient.objects.filter(statut='ACTIF').annotate(
            nombre_projets=models.Count('projets'),
            ca_total=models.Sum('projets__montant_total')
        ).order_by('raison_sociale')
        
        return clients
    
    @staticmethod
    def get_client_avec_stats(client_id):
        """Retourne un client avec ses statistiques détaillées"""
        client = get_object_or_404(JRClient, pk=client_id)
        
        # Statistiques des projets
        projets = JRProject.objects.filter(client=client)
        stats_projets = {
            'total': projets.count(),
            'actifs': projets.filter(statut='ACTIF').count(),
            'termines': projets.filter(statut='TERMINE').count(),
            'en_retard': projets.filter(
                statut__in=['PLANIFIE', 'ACTIF'],
                date_fin_prevue__lt=timezone.now().date()
            ).count(),
        }
        
        # Chiffre d'affaires
        ca_total = projets.aggregate(
            total=models.Sum('montant_total')
        )['total'] or 0
        
        # Tickets du client
        tickets = JRTicket.objects.filter(projet__client=client)
        stats_tickets = {
            'total': tickets.count(),
            'ouverts': tickets.filter(statut='OUVERT').count(),
            'en_cours': tickets.filter(statut='EN_COURS').count(),
            'termines': tickets.filter(statut='TERMINE').count(),
            'en_retard': tickets.filter(
                date_echeance__lt=timezone.now().date(),
                statut__in=['OUVERT', 'EN_COURS', 'EN_REVUE']
            ).count(),
        }
        
        return {
            'client': client,
            'stats_projets': stats_projets,
            'ca_total': ca_total,
            'stats_tickets': stats_tickets,
            'projets_recents': projets.order_by('-created_at')[:5],
            'tickets_recents': tickets.order_by('-created_at')[:10],
        }
    
    @staticmethod
    def rechercher_clients(requete):
        """Recherche avancée de clients"""
        queryset = JRClient.objects.all()
        
        if requete:
            queryset = queryset.filter(
                models.Q(raison_sociale__icontains=requete) |
                models.Q(code_client__icontains=requete) |
                models.Q(contact_principal__icontains=requete) |
                models.Q(email_contact__icontains=requete) |
                models.Q(ville__icontains=requete) |
                models.Q(pays__icontains=requete)
            )
        
        return queryset.order_by('raison_sociale')
    
    @staticmethod
    def get_clients_par_pays():
        """Retourne les statistiques des clients par pays"""
        return JRClient.objects.values('pays').annotate(
            count=models.Count('id'),
            ca_total=models.Sum('projets__montant_total')
        ).order_by('-count')
    
    @staticmethod
    def get_top_clients_par_ca(limit=10):
        """Retourne les top clients par chiffre d'affaires"""
        return JRClient.objects.annotate(
            ca_total=models.Sum('projets__montant_total')
        ).filter(ca_total__isnull=False).order_by('-ca_total')[:limit]
    
    @staticmethod
    def get_clients_sans_projet():
        """Retourne les clients sans projet"""
        return JRClient.objects.filter(
            models.Q(projets__isnull=True) | models.Q(projets__count=0)
        )
    
    @staticmethod
    def dupliquer_client(client_id, nouvelle_raison_sociale):
        """Duplique un client avec une nouvelle raison sociale"""
        client_original = get_object_or_404(JRClient, pk=client_id)
        
        # Créer le nouveau client
        nouveau_client = JRClient.objects.create(
            raison_sociale=nouvelle_raison_sociale,
            contact_principal=client_original.contact_principal,
            email_contact=client_original.email_contact,
            telephone_contact=client_original.telephone_contact,
            adresse=client_original.adresse,
            code_postal=client_original.code_postal,
            ville=client_original.ville,
            pays=client_original.pays,
            numero_tva=client_original.numero_tva,
            conditions_paiement=client_original.conditions_paiement,
            statut='ACTIF'
        )
        
        return nouveau_client
    
    @staticmethod
    def archiver_client(client_id):
        """Archive un client (change le statut en INACTIF)"""
        client = get_object_or_404(JRClient, pk=client_id)
        
        # Vérifier qu'il n'y a pas de projets actifs
        projets_actifs = JRProject.objects.filter(
            client=client,
            statut__in=['PLANIFIE', 'ACTIF']
        )
        
        if projets_actifs.exists():
            raise ValueError(
                "Impossible d'archiver ce client car il a des projets actifs."
            )
        
        client.statut = 'INACTIF'
        client.save()
        
        return client
    
    @staticmethod
    def get_rapport_client(client_id, date_debut=None, date_fin=None):
        """Génère un rapport détaillé pour un client"""
        client = get_object_or_404(JRClient, pk=client_id)
        
        # Projets dans la période
        projets = JRProject.objects.filter(client=client)
        
        if date_debut:
            projets = projets.filter(date_debut__gte=date_debut)
        if date_fin:
            projets = projets.filter(date_debut__lte=date_fin)
        
        # Tickets des projets
        tickets = JRTicket.objects.filter(projet__in=projets)
        
        # Statistiques
        rapport = {
            'client': client,
            'periode': {
                'debut': date_debut,
                'fin': date_fin,
            },
            'projets': {
                'total': projets.count(),
                'actifs': projets.filter(statut='ACTIF').count(),
                'termines': projets.filter(statut='TERMINE').count(),
                'montant_total': projets.aggregate(
                    total=models.Sum('montant_total')
                )['total'] or 0,
                'liste': projets.order_by('-created_at'),
            },
            'tickets': {
                'total': tickets.count(),
                'ouverts': tickets.filter(statut='OUVERT').count(),
                'en_cours': tickets.filter(statut='EN_COURS').count(),
                'termines': tickets.filter(statut='TERMINE').count(),
                'par_priorite': list(
                    tickets.values('priorite')
                    .annotate(count=models.Count('id'))
                    .order_by('-count')
                ),
                'par_type': list(
                    tickets.values('type_ticket')
                    .annotate(count=models.Count('id'))
                    .order_by('-count')
                ),
            },
        }
        
        return rapport
    
    @staticmethod
    def exporter_clients(format='excel', filtres=None):
        """Exporte la liste des clients"""
        queryset = JRClient.objects.all()
        
        if filtres:
            if filtres.get('statut'):
                queryset = queryset.filter(statut=filtres['statut'])
            if filtres.get('pays'):
                queryset = queryset.filter(pays__icontains=filtres['pays'])
        
        if format == 'excel':
            return ClientService._exporter_clients_excel(queryset)
        elif format == 'csv':
            return ClientService._exporter_clients_csv(queryset)
        else:
            raise ValueError(f"Format non supporté: {format}")
    
    @staticmethod
    def _exporter_clients_excel(queryset):
        """Exporte les clients en format Excel"""
        import pandas as pd
        from io import BytesIO
        
        data = []
        for client in queryset:
            projets_count = JRProject.objects.filter(client=client).count()
            ca_total = JRProject.objects.filter(client=client).aggregate(
                total=models.Sum('montant_total')
            )['total'] or 0
            
            data.append({
                'Code Client': client.code_client,
                'Raison Sociale': client.raison_sociale,
                'Contact Principal': client.contact_principal,
                'Email': client.email_contact,
                'Téléphone': client.telephone_contact or '',
                'Ville': client.ville or '',
                'Pays': client.pays,
                'Statut': client.get_statut_display(),
                'Nombre de Projets': projets_count,
                'CA Total': ca_total,
                'Date Création': client.created_at,
            })
        
        df = pd.DataFrame(data)
        
        output = BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df.to_excel(writer, sheet_name='Clients', index=False)
            
            # Ajuster la largeur des colonnes
            worksheet = writer.sheets['Clients']
            for idx, col in enumerate(df.columns):
                max_len = max(
                    df[col].astype(str).map(len).max(),
                    len(str(col))
                )
                worksheet.set_column(idx, idx, max_len + 2)
        
        output.seek(0)
        return output
    
    @staticmethod
    def _exporter_clients_csv(queryset):
        """Exporte les clients en format CSV"""
        import csv
        from io import StringIO
        
        output = StringIO()
        writer = csv.writer(output)
        
        # En-têtes
        writer.writerow([
            'Code Client', 'Raison Sociale', 'Contact Principal', 'Email',
            'Téléphone', 'Ville', 'Pays', 'Statut', 'Nombre de Projets',
            'CA Total', 'Date Création'
        ])
        
        # Données
        for client in queryset:
            projets_count = JRProject.objects.filter(client=client).count()
            ca_total = JRProject.objects.filter(client=client).aggregate(
                total=models.Sum('montant_total')
            )['total'] or 0
            
            writer.writerow([
                client.code_client,
                client.raison_sociale,
                client.contact_principal,
                client.email_contact,
                client.telephone_contact or '',
                client.ville or '',
                client.pays,
                client.get_statut_display(),
                projets_count,
                ca_total,
                client.created_at,
            ])
        
        output.seek(0)
        return output
