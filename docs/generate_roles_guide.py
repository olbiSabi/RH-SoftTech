# docs/generate_roles_guide.py

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib.colors import HexColor, white, black
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, Image, KeepTogether
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
from datetime import datetime
import os


def create_roles_guide():
    """
    Génère le guide PDF de paramétrage des rôles
    """

    # Créer le dossier docs s'il n'existe pas
    os.makedirs('docs', exist_ok=True)

    # Nom du fichier PDF
    filename = f'docs/Guide_Parametrage_Roles_{datetime.now().strftime("%Y%m%d")}.pdf'

    # Créer le document
    doc = SimpleDocTemplate(
        filename,
        pagesize=A4,
        rightMargin=2 * cm,
        leftMargin=2 * cm,
        topMargin=2 * cm,
        bottomMargin=2 * cm,
        title="Guide de Paramétrage des Rôles - ONIAN EasyM",
        author="ONIAN EasyM"
    )

    # Styles
    styles = getSampleStyleSheet()

    # Style personnalisé pour le titre principal
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=HexColor('#1c5d5f'),
        spaceAfter=30,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    )

    # Style pour les titres de section
    heading1_style = ParagraphStyle(
        'CustomHeading1',
        parent=styles['Heading1'],
        fontSize=18,
        textColor=HexColor('#1c5d5f'),
        spaceAfter=12,
        spaceBefore=20,
        fontName='Helvetica-Bold'
    )

    # Style pour les sous-titres
    heading2_style = ParagraphStyle(
        'CustomHeading2',
        parent=styles['Heading2'],
        fontSize=14,
        textColor=HexColor('#193f41'),
        spaceAfter=10,
        spaceBefore=15,
        fontName='Helvetica-Bold'
    )

    # Style pour le texte normal
    normal_style = ParagraphStyle(
        'CustomNormal',
        parent=styles['Normal'],
        fontSize=10,
        alignment=TA_JUSTIFY,
        spaceAfter=10
    )

    # Style pour les notes importantes
    note_style = ParagraphStyle(
        'Note',
        parent=styles['Normal'],
        fontSize=9,
        textColor=HexColor('#f57c00'),
        leftIndent=20,
        rightIndent=20,
        spaceAfter=10,
        spaceBefore=10,
        borderColor=HexColor('#f57c00'),
        borderWidth=1,
        borderPadding=10,
        backColor=HexColor('#fff3e0')
    )

    # Contenu du document
    story = []

    # ========================================
    # PAGE DE GARDE
    # ========================================

    story.append(Spacer(1, 3 * cm))

    # Titre principal
    story.append(Paragraph(
        "GUIDE DE PARAMÉTRAGE<br/>DES RÔLES",
        title_style
    ))

    story.append(Spacer(1, 1 * cm))

    # Sous-titre
    story.append(Paragraph(
        "Système de Gestion des Absences",
        ParagraphStyle(
            'Subtitle',
            parent=styles['Normal'],
            fontSize=14,
            textColor=HexColor('#666666'),
            alignment=TA_CENTER
        )
    ))

    story.append(Spacer(1, 2 * cm))

    # Informations du document
    info_data = [
        ['Application:', 'ONIAN EasyM'],
        ['Module:', 'Gestion des Absences'],
        ['Version:', '1.2'],
        ['Date:', datetime.now().strftime('%d/%m/%Y')],
    ]

    info_table = Table(info_data, colWidths=[4 * cm, 8 * cm])
    info_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
    ]))

    story.append(info_table)

    story.append(PageBreak())

    # ========================================
    # TABLE DES MATIÈRES
    # ========================================

    story.append(Paragraph("TABLE DES MATIÈRES", heading1_style))
    story.append(Spacer(1, 0.5 * cm))

    toc_data = [
        ['1.', 'Introduction', '3'],
        ['2.', 'Architecture des Rôles', '4'],
        ['3.', 'Description des Rôles', '5'],
        ['   3.1', 'Rôle GESTION_APP', '5'],
        ['   3.2', 'Rôle RH_VALIDATION_ABS', '6'],
        ['   3.3', 'Rôle MANAGER_ABS', '7'],
        ['   3.4', 'Rôle EMPLOYE_STD', '8'],
        ['   3.5', 'Rôle ASSISTANT_RH', '9'],
        ['4.', 'Installation des Rôles', '10'],
        ['5.', 'Attribution des Rôles', '11'],
        ['6.', 'Gestion des Permissions', '12'],
        ['7.', 'Décorateurs et Mixins', '13'],
        ['8.', 'Exemples d\'Utilisation', '15'],
        ['9.', 'Dépannage', '16'],
    ]

    toc_table = Table(toc_data, colWidths=[1 * cm, 12 * cm, 2 * cm])
    toc_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
        ('ALIGN', (2, 0), (2, -1), 'RIGHT'),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('LINEBELOW', (0, -1), (-1, -1), 0.5, HexColor('#cccccc')),
    ]))

    story.append(toc_table)
    story.append(PageBreak())

    # ========================================
    # 1. INTRODUCTION
    # ========================================

    story.append(Paragraph("1. INTRODUCTION", heading1_style))

    story.append(Paragraph(
        "Le système de gestion des absences d'ONIAN EasyM repose sur un système de rôles "
        "permettant de contrôler finement les accès et les permissions de chaque utilisateur. "
        "Ce guide vous explique comment configurer et gérer ces rôles.",
        normal_style
    ))

    story.append(Paragraph(
        "<b>Objectifs de ce guide :</b>",
        normal_style
    ))

    objectives = [
        "Comprendre l'architecture des rôles",
        "Installer et configurer les rôles",
        "Attribuer les rôles aux employés",
        "Gérer les permissions associées",
        "Résoudre les problèmes courants"
    ]

    for obj in objectives:
        story.append(Paragraph(f"• {obj}", normal_style))

    story.append(Spacer(1, 0.5 * cm))

    story.append(Paragraph(
        "⚠️ <b>Note importante :</b> La gestion des rôles nécessite des droits administrateur. "
        "Assurez-vous d'avoir les permissions nécessaires avant de procéder aux modifications.",
        note_style
    ))

    story.append(PageBreak())

    # ========================================
    # 2. ARCHITECTURE DES RÔLES
    # ========================================

    story.append(Paragraph("2. ARCHITECTURE DES RÔLES", heading1_style))

    story.append(Paragraph(
        "Le système utilise 5 rôles principaux, chacun correspondant à un niveau de responsabilité "
        "différent dans le processus de gestion des absences :",
        normal_style
    ))

    # Tableau des rôles
    roles_data = [
        ['Rôle', 'Code', 'Niveau', 'Description'],
        ['Gestionnaire Application', 'GESTION_APP', 'Admin', 'Paramétrage complet'],
        ['RH Validation', 'RH_VALIDATION_ABS', 'RH', 'Validation finale des absences'],
        ['Manager', 'MANAGER_ABS', 'Manager', 'Validation niveau 1'],
        ['Assistant RH', 'ASSISTANT_RH', 'RH', 'Consultation uniquement'],
        ['Employé Standard', 'EMPLOYE_STD', 'Employé', 'Déclaration d\'absences'],
    ]

    roles_table = Table(roles_data, colWidths=[4.5 * cm, 4 * cm, 2.5 * cm, 5 * cm])
    roles_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), HexColor('#1c5d5f')),
        ('TEXTCOLOR', (0, 0), (-1, 0), white),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 9),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), HexColor('#f5f5f5')),
        ('GRID', (0, 0), (-1, -1), 0.5, HexColor('#cccccc')),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [white, HexColor('#f9f9f9')]),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
    ]))

    story.append(roles_table)
    story.append(Spacer(1, 0.5 * cm))

    # Hiérarchie
    story.append(Paragraph("2.1 Hiérarchie des Permissions", heading2_style))

    story.append(Paragraph(
        "Les rôles suivent une hiérarchie stricte :",
        normal_style
    ))

    hierarchy_data = [
        ['Niveau 5', 'GESTION_APP', 'Toutes les permissions'],
        ['Niveau 4', 'RH_VALIDATION_ABS', 'Validation RH + consultation'],
        ['Niveau 3', 'ASSISTANT_RH', 'Consultation uniquement (lecture seule)'],
        ['Niveau 2', 'MANAGER_ABS', 'Validation manager + ses équipes'],
        ['Niveau 1', 'EMPLOYE_STD', 'Ses propres absences uniquement'],
    ]

    hierarchy_table = Table(hierarchy_data, colWidths=[2.5 * cm, 5 * cm, 8.5 * cm])
    hierarchy_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), HexColor('#e8f5e9')),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('GRID', (0, 0), (-1, -1), 0.5, HexColor('#cccccc')),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (-1, -1), 10),
        ('RIGHTPADDING', (0, 0), (-1, -1), 10),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
    ]))

    story.append(hierarchy_table)

    story.append(PageBreak())

    # ========================================
    # 3. DESCRIPTION DES RÔLES
    # ========================================

    story.append(Paragraph("3. DESCRIPTION DÉTAILLÉE DES RÔLES", heading1_style))

    # 3.1 GESTION_APP
    story.append(Paragraph("3.1 Rôle GESTION_APP (Gestionnaire Application)", heading2_style))

    story.append(Paragraph(
        "<b>Code :</b> GESTION_APP<br/>"
        "<b>Groupe Django :</b> GESTION_APP<br/>"
        "<b>Niveau :</b> Administrateur",
        normal_style
    ))

    story.append(Paragraph("<b>Description :</b>", normal_style))
    story.append(Paragraph(
        "Ce rôle offre un accès complet à tous les paramétrages de l'application. "
        "Il est destiné aux administrateurs système et aux responsables de la configuration "
        "de l'application.",
        normal_style
    ))

    story.append(Paragraph("<b>Permissions :</b>", normal_style))

    gestion_app_perms = [
        "Gestion complète des types d'absence",
        "Configuration des jours fériés",
        "Paramétrage des conventions de congés",
        "Configuration des paramètres de calcul",
        "Gestion des acquisitions de congés",
        "Paramétrage de l'entreprise",
        "Validation des absences (tous niveaux)",
        "Export et rapports complets",
    ]

    for perm in gestion_app_perms:
        story.append(Paragraph(f"✓ {perm}", normal_style))

    story.append(Paragraph(
        "⚠️ <b>Attention :</b> Ce rôle donne un accès total au paramétrage. "
        "Ne l'attribuez qu'aux personnes de confiance ayant les compétences techniques nécessaires.",
        note_style
    ))

    story.append(Spacer(1, 0.5 * cm))

    # 3.2 RH_VALIDATION_ABS
    story.append(Paragraph("3.2 Rôle RH_VALIDATION_ABS (RH Validation)", heading2_style))

    story.append(Paragraph(
        "<b>Code :</b> RH_VALIDATION_ABS<br/>"
        "<b>Groupe Django :</b> RH_VALIDATION_ABS<br/>"
        "<b>Niveau :</b> Ressources Humaines",
        normal_style
    ))

    story.append(Paragraph("<b>Description :</b>", normal_style))
    story.append(Paragraph(
        "Ce rôle permet de valider les absences après approbation du manager. "
        "Il représente la validation finale dans le workflow des absences.",
        normal_style
    ))

    story.append(Paragraph("<b>Permissions :</b>", normal_style))

    rh_perms = [
        "Validation finale des absences (niveau RH)",
        "Consultation de toutes les absences de l'entreprise",
        "Export des données d'absence",
        "Consultation des acquisitions de congés",
        "Accès aux rapports RH",
    ]

    for perm in rh_perms:
        story.append(Paragraph(f"✓ {perm}", normal_style))

    story.append(Paragraph("<b>Workflow :</b>", normal_style))
    story.append(Paragraph(
        "1. L'employé soumet une demande<br/>"
        "2. Le manager valide (niveau 1)<br/>"
        "3. <b>Le RH valide (niveau 2) ← CE RÔLE</b><br/>"
        "4. L'absence est confirmée",
        normal_style
    ))

    story.append(PageBreak())

    # 3.3 MANAGER_ABS
    story.append(Paragraph("3.3 Rôle MANAGER_ABS (Manager)", heading2_style))

    story.append(Paragraph(
        "<b>Code :</b> MANAGER_ABS<br/>"
        "<b>Groupe Django :</b> MANAGER_ABS<br/>"
        "<b>Niveau :</b> Manager",
        normal_style
    ))

    story.append(Paragraph("<b>Description :</b>", normal_style))
    story.append(Paragraph(
        "Ce rôle permet aux managers de valider les demandes d'absence de leurs équipes. "
        "Il représente la première étape du processus de validation.",
        normal_style
    ))

    story.append(Paragraph("<b>Permissions :</b>", normal_style))

    manager_perms = [
        "Validation des absences de son équipe (niveau 1)",
        "Consultation des absences de son département",
        "Consultation de ses propres absences",
        "Création d'absences pour lui-même",
    ]

    for perm in manager_perms:
        story.append(Paragraph(f"✓ {perm}", normal_style))

    story.append(Paragraph(
        "ℹ️ <b>Note :</b> Un manager ne peut valider que les absences des employés "
        "de son département. Cette restriction est gérée automatiquement par le système.",
        note_style
    ))

    story.append(Spacer(1, 0.5 * cm))

    # 3.4 EMPLOYE_STD
    story.append(Paragraph("3.4 Rôle EMPLOYE_STD (Employé Standard)", heading2_style))

    story.append(Paragraph(
        "<b>Code :</b> EMPLOYE_STD<br/>"
        "<b>Groupe Django :</b> EMPLOYE_STD<br/>"
        "<b>Niveau :</b> Employé",
        normal_style
    ))

    story.append(Paragraph("<b>Description :</b>", normal_style))
    story.append(Paragraph(
        "Ce rôle est attribué à tous les employés standards. Il permet de gérer "
        "ses propres absences uniquement.",
        normal_style
    ))

    story.append(Paragraph("<b>Permissions :</b>", normal_style))

    employe_perms = [
        "Création de demandes d'absence",
        "Consultation de ses propres absences",
        "Modification de ses absences (statut brouillon)",
        "Annulation de ses absences",
        "Consultation de son solde de congés",
    ]

    for perm in employe_perms:
        story.append(Paragraph(f"✓ {perm}", normal_style))

    story.append(PageBreak())

    # 3.5 ASSISTANT_RH - NOUVEAU
    story.append(Paragraph("3.5 Rôle ASSISTANT_RH (Assistant RH)", heading2_style))

    story.append(Paragraph(
        "<b>Code :</b> ASSISTANT_RH<br/>"
        "<b>Groupe Django :</b> ASSISTANT_RH<br/>"
        "<b>Niveau :</b> Ressources Humaines (Consultation)",
        normal_style
    ))

    story.append(Paragraph("<b>Description :</b>", normal_style))
    story.append(Paragraph(
        "Ce rôle permet de consulter toutes les absences de l'entreprise en mode lecture seule, "
        "sans pouvoir les valider ou les modifier. Il est destiné aux assistants RH qui ont besoin "
        "de visibilité sur les absences pour des tâches administratives.",
        normal_style
    ))

    story.append(Paragraph("<b>Permissions :</b>", normal_style))

    assistant_rh_perms = [
        "Consultation de toutes les absences (lecture seule)",
        "Consultation des types d'absence",
        "Consultation des acquisitions de congés",
        "Consultation des jours fériés",
        "Consultation des conventions de congés",
        "Accès aux rapports et statistiques",
    ]

    for perm in assistant_rh_perms:
        story.append(Paragraph(f"✓ {perm}", normal_style))

    story.append(Paragraph("<b>Restrictions :</b>", normal_style))

    assistant_rh_restrictions = [
        "Ne peut PAS valider les absences",
        "Ne peut PAS modifier les absences",
        "Ne peut PAS créer d'absences pour d'autres employés",
        "Ne peut PAS gérer les paramètres de l'application",
    ]

    for restriction in assistant_rh_restrictions:
        story.append(Paragraph(f"✗ {restriction}", normal_style))

    story.append(Paragraph(
        "ℹ️ <b>Note :</b> Ce rôle est idéal pour les assistants RH qui ont besoin de consulter "
        "les absences pour établir des rapports, suivre les plannings ou répondre aux questions "
        "des employés, sans avoir le pouvoir de validation.",
        note_style
    ))

    story.append(PageBreak())

    # ========================================
    # 4. INSTALLATION DES RÔLES
    # ========================================

    story.append(Paragraph("4. INSTALLATION DES RÔLES", heading1_style))

    story.append(Paragraph(
        "L'installation des rôles se fait via une commande Django personnalisée. "
        "Cette commande crée automatiquement tous les rôles et leurs permissions associées.",
        normal_style
    ))

    story.append(Paragraph("4.1 Prérequis", heading2_style))

    prereq = [
        "Accès au serveur (SSH ou console locale)",
        "Droits administrateur sur la base de données",
        "Django installé et configuré",
        "Application 'employee' et 'absence' migrées",
    ]

    for item in prereq:
        story.append(Paragraph(f"• {item}", normal_style))

    story.append(Paragraph("4.2 Procédure d'Installation", heading2_style))

    story.append(Paragraph("<b>Étape 1 : Accéder au serveur</b>", normal_style))
    story.append(Paragraph(
        "Connectez-vous au serveur via SSH ou ouvrez un terminal sur le serveur local :",
        normal_style
    ))

    story.append(Paragraph(
        "<font name='Courier' color='#333333'>$ ssh utilisateur@serveur</font>",
        ParagraphStyle('Code', parent=normal_style, fontName='Courier', backColor=HexColor('#f5f5f5'))
    ))

    story.append(Paragraph("<b>Étape 2 : Naviguer vers le projet</b>", normal_style))
    story.append(Paragraph(
        "<font name='Courier' color='#333333'>$ cd /chemin/vers/votre/projet</font>",
        ParagraphStyle('Code', parent=normal_style, fontName='Courier', backColor=HexColor('#f5f5f5'))
    ))

    story.append(Paragraph("<b>Étape 3 : Activer l'environnement virtuel</b>", normal_style))
    story.append(Paragraph(
        "<font name='Courier' color='#333333'>$ source venv/bin/activate</font>",
        ParagraphStyle('Code', parent=normal_style, fontName='Courier', backColor=HexColor('#f5f5f5'))
    ))

    story.append(Paragraph("<b>Étape 4 : Exécuter la commande</b>", normal_style))
    story.append(Paragraph(
        "<font name='Courier' color='#333333'>$ python manage.py create_absence_roles</font>",
        ParagraphStyle('Code', parent=normal_style, fontName='Courier', backColor=HexColor('#f5f5f5'))
    ))

    story.append(Paragraph("<b>Étape 5 : Vérifier le résultat</b>", normal_style))
    story.append(Paragraph(
        "Vous devriez voir un message de confirmation similaire à :",
        normal_style
    ))

    story.append(Paragraph(
        "<font name='Courier' color='#28a745'>✅ Rôle GESTION_APP créé<br/>"
        "✅ Rôle RH_VALIDATION_ABS créé<br/>"
        "✅ Rôle MANAGER_ABS créé<br/>"
        "✅ Rôle EMPLOYE_STD créé<br/>"
        "✅ Rôle ASSISTANT_RH créé<br/><br/>"
        "🎉 Configuration des rôles terminée !</font>",
        ParagraphStyle('Success', parent=normal_style, fontName='Courier',
                       textColor=HexColor('#28a745'), backColor=HexColor('#d4edda'), fontSize=8)
    ))

    story.append(PageBreak())

    # ========================================
    # 5. ATTRIBUTION DES RÔLES
    # ========================================

    story.append(Paragraph("5. ATTRIBUTION DES RÔLES AUX EMPLOYÉS", heading1_style))

    story.append(Paragraph(
        "Une fois les rôles créés, vous devez les attribuer aux employés. "
        "Plusieurs méthodes sont disponibles :",
        normal_style
    ))

    story.append(Paragraph("5.1 Via l'Interface d'Administration Django", heading2_style))

    admin_steps = [
        "Connectez-vous à l'admin Django : http://votresite.com/admin/",
        "Naviguez vers <b>Employee → Attribution de rôle (ZYRE)</b>",
        "Cliquez sur <b>Ajouter attribution de rôle</b>",
        "Sélectionnez l'<b>employé</b>",
        "Sélectionnez le <b>rôle</b> à attribuer",
        "Définissez la <b>date de début</b>",
        "Cochez <b>Actif</b>",
        "Cliquez sur <b>Enregistrer</b>",
    ]

    for i, step in enumerate(admin_steps, 1):
        story.append(Paragraph(f"{i}. {step}", normal_style))

    story.append(Spacer(1, 0.5 * cm))

    story.append(Paragraph("5.2 Via le Shell Django (Méthode Avancée)", heading2_style))

    story.append(Paragraph(
        "Pour les administrateurs avancés, vous pouvez utiliser le shell Django :",
        normal_style
    ))

    story.append(Paragraph(
        "<font name='Courier' color='#333333'>"
        "$ python manage.py shell<br/><br/>"
        "from employee.models import ZYRO, ZYRE, ZY00<br/>"
        "from django.utils import timezone<br/><br/>"
        "# Récupérer le rôle<br/>"
        "role = ZYRO.objects.get(CODE='ASSISTANT_RH')<br/><br/>"
        "# Récupérer l'employé<br/>"
        "employe = ZY00.objects.get(matricule='MT000001')<br/><br/>"
        "# Créer l'attribution<br/>"
        "ZYRE.objects.create(<br/>"
        "&nbsp;&nbsp;&nbsp;&nbsp;employe=employe,<br/>"
        "&nbsp;&nbsp;&nbsp;&nbsp;role=role,<br/>"
        "&nbsp;&nbsp;&nbsp;&nbsp;date_debut=timezone.now().date(),<br/>"
        "&nbsp;&nbsp;&nbsp;&nbsp;actif=True<br/>"
        ")<br/><br/>"
        "print('✅ Rôle attribué avec succès')"
        "</font>",
        ParagraphStyle('Code', parent=normal_style, fontName='Courier',
                       fontSize=7, backColor=HexColor('#f5f5f5'))
    ))

    story.append(PageBreak())

    # ========================================
    # 6. GESTION DES PERMISSIONS
    # ========================================

    story.append(Paragraph("6. GESTION DES PERMISSIONS", heading1_style))

    story.append(Paragraph("6.1 Tableau Récapitulatif des Permissions", heading2_style))

    perms_data = [
        ['Action', 'GESTION_APP', 'RH', 'MANAGER', 'ASSISTANT_RH', 'EMPLOYÉ'],
        ['Créer absence (soi)', '✓', '✓', '✓', '✓', '✓'],
        ['Voir ses absences', '✓', '✓', '✓', '✓', '✓'],
        ['Voir toutes absences', '✓', '✓', 'Équipe', '✓', 'Soi'],
        ['Valider (Manager)', '✓', '✗', '✓', '✗', '✗'],
        ['Valider (RH)', '✓', '✓', '✗', '✗', '✗'],
        ['Gérer types absence', '✓', '✗', '✗', '✗', '✗'],
        ['Gérer jours fériés', '✓', '✗', '✗', '✗', '✗'],
        ['Gérer conventions', '✓', '✗', '✗', '✗', '✗'],
        ['Paramètres entreprise', '✓', '✗', '✗', '✗', '✗'],
        ['Export données', '✓', '✓', '✗', '✓', '✗'],
    ]

    perms_table = Table(perms_data, colWidths=[4 * cm, 2.2 * cm, 2.2 * cm, 2.2 * cm, 2.2 * cm, 2.2 * cm])
    perms_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), HexColor('#1c5d5f')),
        ('TEXTCOLOR', (0, 0), (-1, 0), white),
        ('ALIGN', (0, 0), (0, -1), 'LEFT'),
        ('ALIGN', (1, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 0.5, HexColor('#cccccc')),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [white, HexColor('#f9f9f9')]),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))

    story.append(perms_table)

    story.append(Spacer(1, 0.5 * cm))

    story.append(Paragraph("6.2 Cumul de Rôles", heading2_style))

    story.append(Paragraph(
        "Un employé peut avoir plusieurs rôles simultanément. Dans ce cas, "
        "le système applique le principe du <b>cumul des permissions</b> :",
        normal_style
    ))

    cumul_example = [
        "<b>Exemple 1 :</b> Marie est EMPLOYÉ + ASSISTANT_RH",
        "→ Elle peut créer ses absences ET consulter toutes les absences de l'entreprise",
        "",
        "<b>Exemple 2 :</b> Jean est EMPLOYÉ + MANAGER + RH",
        "→ Il peut créer ses absences, valider en tant que manager ET en tant que RH",
        "",
        "<b>Exemple 3 :</b> Sophie est EMPLOYÉ + ASSISTANT_RH",
        "→ Elle voit toutes les absences mais ne peut rien valider",
    ]

    for item in cumul_example:
        story.append(Paragraph(item, normal_style))

    story.append(Paragraph(
        "ℹ️ <b>Note :</b> Le système gère automatiquement les notifications pour éviter "
        "les doublons. Un employé avec plusieurs rôles recevra une notification pour chaque contexte.",
        note_style
    ))

    story.append(PageBreak())

    # ========================================
    # 7. DÉCORATEURS ET MIXINS (NOUVEAU)
    # ========================================

    story.append(Paragraph("7. DÉCORATEURS ET MIXINS", heading1_style))

    story.append(Paragraph(
        "Pour protéger vos vues et contrôler l'accès selon les rôles, ONIAN EasyM fournit "
        "des décorateurs (pour les vues fonctions) et des mixins (pour les vues classes).",
        normal_style
    ))

    story.append(Spacer(1, 0.3 * cm))

    # ========================================
    # 7.1 Décorateurs pour Vues Fonctions
    # ========================================

    story.append(Paragraph("7.1 Décorateurs pour Vues Fonctions", heading2_style))

    story.append(Paragraph(
        "Les décorateurs s'appliquent sur les vues définies avec <font name='Courier'>def</font>. "
        "Ils permettent de restreindre l'accès à certaines vues en fonction des rôles.",
        normal_style
    ))

    decorators_data = [
        ['Décorateur', 'Rôles Autorisés', 'Usage Typique'],
        ['@drh_or_admin_required', 'DRH, PDG, Admin', 'Fonctions DRH'],
        ['@gestion_app_required', 'GESTION_APP, Admin', 'Paramétrage, Gestion rôles'],
        ['@assistant_rh_required', 'ASSISTANT_RH, RH_VALIDATION_ABS, DRH, GESTION_APP, Admin', 'Consultation RH'],
        ['@rh_required', 'RH_VALIDATION_ABS, DRH, GESTION_APP, Admin', 'Validation RH'],
        ['@manager_required', 'MANAGER_ABS, Managers, DRH, GESTION_APP, Admin', 'Validation équipe'],
        ['@manager_or_rh_required', 'Managers OU RH, Admin', 'Validation mixte'],
        ['@role_required(...)', 'Personnalisable', 'Rôles multiples custom'],
    ]

    decorators_table = Table(decorators_data, colWidths=[5.5 * cm, 5.5 * cm, 5 * cm])
    decorators_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), HexColor('#1c5d5f')),
        ('TEXTCOLOR', (0, 0), (-1, 0), white),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 7),
        ('FONTNAME', (0, 1), (0, -1), 'Courier'),
        ('FONTSIZE', (0, 1), (0, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), HexColor('#f5f5f5')),
        ('GRID', (0, 0), (-1, -1), 0.5, HexColor('#cccccc')),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [white, HexColor('#f9f9f9')]),
        ('FONTSIZE', (1, 1), (-1, -1), 7),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
    ]))

    story.append(decorators_table)

    story.append(Spacer(1, 0.5 * cm))

    # Exemple d'utilisation
    story.append(Paragraph("<b>Exemple d'utilisation :</b>", normal_style))

    story.append(Paragraph(
        "<font name='Courier' size='8'>"
        "@login_required<br/>"
        "@drh_or_admin_required<br/>"
        "def embauche_agent(request):<br/>"
        "&nbsp;&nbsp;&nbsp;&nbsp;# Code de la vue...<br/>"
        "&nbsp;&nbsp;&nbsp;&nbsp;pass"
        "</font>",
        ParagraphStyle('Code', parent=normal_style, fontName='Courier',
                       fontSize=8, backColor=HexColor('#f5f5f5'), leftIndent=20)
    ))

    story.append(Spacer(1, 0.5 * cm))

    # ========================================
    # 7.2 Mixins pour Vues Classes
    # ========================================

    story.append(Paragraph("7.2 Mixins pour Vues Classes (CBV)", heading2_style))

    story.append(Paragraph(
        "Les mixins s'appliquent sur les vues classes (héritant de ListView, UpdateView, etc.). "
        "Ils offrent une approche orientée objet pour la gestion des permissions.",
        normal_style
    ))

    mixins_data = [
        ['Mixin', 'Rôles Autorisés', 'Usage Typique'],
        ['DRHOrAdminRequiredMixin', 'DRH, GESTION_APP, Admin', 'CRUD employés'],
        ['GestionAppRequiredMixin', 'GESTION_APP, Admin', 'Paramétrage application'],
        ['AssistantRHRequiredMixin', 'ASSISTANT_RH, RH_VALIDATION_ABS, DRH, GESTION_APP, Admin', 'Consultation RH'],
        ['DRHOrAssistantRHRequiredMixin', 'Tous rôles RH, Admin', 'Accès RH général'],
        ['ManagerRequiredMixin', 'MANAGER_ABS, Managers, DRH, GESTION_APP, Admin', 'Gestion équipe'],
    ]

    mixins_table = Table(mixins_data, colWidths=[5.5 * cm, 5.5 * cm, 5 * cm])
    mixins_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), HexColor('#1c5d5f')),
        ('TEXTCOLOR', (0, 0), (-1, 0), white),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 8),
        ('FONTNAME', (0, 1), (0, -1), 'Courier'),
        ('FONTSIZE', (0, 1), (0, -1), 7),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), HexColor('#f5f5f5')),
        ('GRID', (0, 0), (-1, -1), 0.5, HexColor('#cccccc')),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [white, HexColor('#f9f9f9')]),
        ('FONTSIZE', (1, 1), (-1, -1), 8),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
    ]))

    story.append(mixins_table)

    story.append(Spacer(1, 0.5 * cm))

    # Exemple d'utilisation
    story.append(Paragraph("<b>Exemple d'utilisation :</b>", normal_style))

    story.append(Paragraph(
        "<font name='Courier' size='8'>"
        "class EmployeListView(LoginRequiredMixin,<br/>"
        "&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;DRHOrAdminRequiredMixin,<br/>"
        "&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;ListView):<br/>"
        "&nbsp;&nbsp;&nbsp;&nbsp;model = ZY00<br/>"
        "&nbsp;&nbsp;&nbsp;&nbsp;template_name = 'employee/list.html'"
        "</font>",
        ParagraphStyle('Code', parent=normal_style, fontName='Courier',
                       fontSize=8, backColor=HexColor('#f5f5f5'), leftIndent=20)
    ))

    story.append(Spacer(1, 0.5 * cm))

    # ========================================
    # 7.3 Ordre des Mixins (Important)
    # ========================================

    story.append(Paragraph("7.3 Ordre des Mixins (Critique)", heading2_style))

    story.append(Paragraph(
        "⚠️ <b>L'ordre des mixins est crucial pour le bon fonctionnement !</b> "
        "Respectez toujours cette hiérarchie :",
        note_style
    ))

    story.append(Paragraph(
        "<font name='Courier' size='8'>"
        "class MaVue(LoginRequiredMixin,&nbsp;&nbsp;&nbsp;&nbsp;# 1. Vérification connexion<br/>"
        "&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;DRHOrAdminRequiredMixin,&nbsp;&nbsp;# 2. Vérification permission<br/>"
        "&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;ListView):&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;# 3. Type de vue Django<br/>"
        "&nbsp;&nbsp;&nbsp;&nbsp;pass"
        "</font>",
        ParagraphStyle('Code', parent=normal_style, fontName='Courier',
                       fontSize=8, backColor=HexColor('#f5f5f5'), leftIndent=20)
    ))

    story.append(Paragraph(
        "<b>Règle d'or :</b> Les mixins de permission viennent toujours APRÈS LoginRequiredMixin "
        "mais AVANT la vue de base (ListView, CreateView, UpdateView, etc.)",
        normal_style
    ))

    story.append(PageBreak())

    # ========================================
    # 7.4 Tableau Comparatif
    # ========================================

    story.append(Paragraph("7.4 Décorateurs vs Mixins : Quand Utiliser Quoi ?", heading2_style))

    comparison_data = [
        ['Critère', 'Décorateurs (@)', 'Mixins (Classe)'],
        ['Type de vue', 'Vues fonctions (def)', 'Vues classes (CBV)'],
        ['Syntaxe', '@decorateur\ndef ma_vue(request):', 'class MaVue(Mixin, View):'],
        ['Complexité', 'Simple et direct', 'Plus structuré, POO'],
        ['Réutilisabilité', 'Moyenne', 'Élevée (héritage)'],
        ['Performance', 'Légèrement plus rapide', 'Optimisé pour CBV'],
        ['Exemple', '@drh_or_admin_required', 'DRHOrAdminRequiredMixin'],
    ]

    comparison_table = Table(comparison_data, colWidths=[4 * cm, 6 * cm, 6 * cm])
    comparison_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), HexColor('#e8f5e9')),
        ('TEXTCOLOR', (0, 0), (-1, 0), HexColor('#1c5d5f')),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 0.5, HexColor('#cccccc')),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [white, HexColor('#f9f9f9')]),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))

    story.append(comparison_table)

    story.append(Spacer(1, 0.5 * cm))

    story.append(Paragraph(
        "💡 <b>Recommandation :</b> Utilisez les mixins pour les vues classes (CBV) car ils offrent "
        "une meilleure intégration avec Django et facilitent la maintenance du code.",
        note_style
    ))

    story.append(PageBreak())

    # ========================================
    # 8. EXEMPLES D'UTILISATION (ancienne section 7)
    # ========================================

    story.append(Paragraph("8. EXEMPLES D'UTILISATION", heading1_style))

    story.append(Paragraph("8.1 Cas d'Usage Typiques", heading2_style))

    # Cas 1
    story.append(Paragraph("<b>Cas 1 : Employé Standard</b>", normal_style))
    story.append(Paragraph(
        "<b>Profil :</b> Sophie, assistante administrative<br/>"
        "<b>Rôle attribué :</b> EMPLOYE_STD<br/>"
        "<b>Permissions :</b> Créer et consulter ses absences uniquement",
        normal_style
    ))

    story.append(Spacer(1, 0.3 * cm))

    # Cas 2
    story.append(Paragraph("<b>Cas 2 : Manager de Département</b>", normal_style))
    story.append(Paragraph(
        "<b>Profil :</b> Nicolas, chef du département IT<br/>"
        "<b>Rôles attribués :</b> EMPLOYE_STD + MANAGER_ABS<br/>"
        "<b>Permissions :</b> Créer ses absences + Valider les absences de son équipe IT",
        normal_style
    ))

    story.append(Spacer(1, 0.3 * cm))

    # Cas 3
    story.append(Paragraph("<b>Cas 3 : Responsable RH</b>", normal_style))
    story.append(Paragraph(
        "<b>Profil :</b> Nathalie, DRH<br/>"
        "<b>Rôles attribués :</b> EMPLOYE_STD + RH_VALIDATION_ABS<br/>"
        "<b>Permissions :</b> Créer ses absences + Valider toutes les absences (niveau RH)",
        normal_style
    ))

    story.append(Spacer(1, 0.3 * cm))

    # Cas 4
    story.append(Paragraph("<b>Cas 4 : Assistant RH</b>", normal_style))
    story.append(Paragraph(
        "<b>Profil :</b> Marie, assistante RH<br/>"
        "<b>Rôles attribués :</b> EMPLOYE_STD + ASSISTANT_RH<br/>"
        "<b>Permissions :</b> Créer ses absences + Consulter toutes les absences (lecture seule)",
        normal_style
    ))

    story.append(Spacer(1, 0.3 * cm))

    # Cas 5
    story.append(Paragraph("<b>Cas 5 : Administrateur Système</b>", normal_style))
    story.append(Paragraph(
        "<b>Profil :</b> Marc, responsable IT<br/>"
        "<b>Rôle attribué :</b> GESTION_APP<br/>"
        "<b>Permissions :</b> Accès complet au paramétrage de l'application",
        normal_style
    ))

    story.append(Spacer(1, 0.5 * cm))

    story.append(Paragraph("8.2 Workflow Complet", heading2_style))

    workflow_data = [
        ['Étape', 'Acteur', 'Rôle Requis', 'Action'],
        ['1', 'Sophie', 'EMPLOYE_STD', 'Crée une demande d\'absence'],
        ['2', 'Nicolas', 'MANAGER_ABS', 'Valide la demande (niveau 1)'],
        ['3', 'Nathalie', 'RH_VALIDATION_ABS', 'Valide la demande (niveau 2)'],
        ['4', 'Sophie', 'EMPLOYE_STD', 'Reçoit la confirmation'],
        ['5', 'Marie', 'ASSISTANT_RH', 'Consulte pour établir un rapport'],
    ]

    workflow_table = Table(workflow_data, colWidths=[1.5 * cm, 3 * cm, 4 * cm, 7.5 * cm])
    workflow_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), HexColor('#e8f5e9')),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('GRID', (0, 0), (-1, -1), 0.5, HexColor('#cccccc')),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [white, HexColor('#f9f9f9')]),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
    ]))

    story.append(workflow_table)

    story.append(PageBreak())

    # ========================================
    # 9. DÉPANNAGE
    # ========================================

    story.append(Paragraph("9. DÉPANNAGE", heading1_style))

    story.append(Paragraph("9.1 Problèmes Courants", heading2_style))

    # Problème 1
    story.append(Paragraph(
        "<b>Problème :</b> L'employé ne peut pas valider les absences en tant que manager",
        normal_style
    ))
    story.append(Paragraph(
        "<b>Solutions :</b>",
        normal_style
    ))
    solutions_1 = [
        "Vérifier que le rôle MANAGER_ABS est bien attribué",
        "Vérifier que l'attribution est active (date_fin = NULL)",
        "Vérifier que l'employé est bien défini comme manager du département dans ZYMA",
        "Vérifier que l'employé de la demande est bien dans le département du manager",
    ]
    for sol in solutions_1:
        story.append(Paragraph(f"• {sol}", normal_style))

    story.append(Spacer(1, 0.3 * cm))

    # Problème 2
    story.append(Paragraph(
        "<b>Problème :</b> L'employé ne voit pas les menus de paramétrage",
        normal_style
    ))
    story.append(Paragraph(
        "<b>Solutions :</b>",
        normal_style
    ))
    solutions_2 = [
        "Vérifier que le rôle GESTION_APP est attribué",
        "Vider le cache du navigateur",
        "Vérifier les templates (condition `{% if user.employe.peut_gerer_parametrage_app %}`)",
        "Se déconnecter et se reconnecter",
    ]
    for sol in solutions_2:
        story.append(Paragraph(f"• {sol}", normal_style))

    story.append(Spacer(1, 0.3 * cm))

    # Problème 3
    story.append(Paragraph(
        "<b>Problème :</b> L'assistant RH peut valider des absences",
        normal_style
    ))
    story.append(Paragraph(
        "<b>Solutions :</b>",
        normal_style
    ))
    solutions_3 = [
        "Vérifier que SEUL le rôle ASSISTANT_RH est attribué (pas RH_VALIDATION_ABS)",
        "Vérifier que les boutons de validation sont masqués dans le template",
        "Vérifier que les vues de validation utilisent bien les décorateurs @rh_required",
        "Re-exécuter la commande create_absence_roles pour corriger les permissions",
    ]
    for sol in solutions_3:
        story.append(Paragraph(f"• {sol}", normal_style))

    story.append(Spacer(1, 0.5 * cm))

    story.append(Paragraph("9.2 Commandes de Diagnostic", heading2_style))

    story.append(Paragraph(
        "Utilisez ces commandes pour diagnostiquer les problèmes :",
        normal_style
    ))

    story.append(Paragraph(
        "<font name='Courier' color='#333333'>"
        "# Vérifier les rôles existants<br/>"
        "python manage.py shell<br/>"
        ">>> from employee.models import ZYRO<br/>"
        ">>> ZYRO.objects.all()<br/><br/>"
        "# Vérifier les attributions d'un employé<br/>"
        ">>> from employee.models import ZY00<br/>"
        ">>> emp = ZY00.objects.get(matricule='MT000001')<br/>"
        ">>> emp.get_roles()<br/><br/>"
        "# Vérifier si un employé est assistant RH<br/>"
        ">>> emp.est_assistant_rh()<br/><br/>"
        "# Vérifier les permissions d'un rôle<br/>"
        ">>> role = ZYRO.objects.get(CODE='ASSISTANT_RH')<br/>"
        ">>> role.django_group.permissions.all()"
        "</font>",
        ParagraphStyle('Code', parent=normal_style, fontName='Courier',
                       fontSize=7, backColor=HexColor('#f5f5f5'))
    ))

    story.append(Spacer(1, 0.5 * cm))

    story.append(Paragraph("9.3 Contact Support", heading2_style))

    story.append(Paragraph(
        "Si le problème persiste après avoir essayé ces solutions :",
        normal_style
    ))

    support_info = [
        "<b>Email :</b> support@onian-easym.com",
        "<b>Téléphone :</b> +228 XX XX XX XX",
        "<b>Horaires :</b> Lundi - Vendredi, 8h - 17h",
    ]

    for info in support_info:
        story.append(Paragraph(f"• {info}", normal_style))

    # Footer
    story.append(Spacer(1, 2 * cm))
    story.append(Paragraph(
        "─────────────────────────────────────────────────────",
        ParagraphStyle('Footer', parent=normal_style, alignment=TA_CENTER, textColor=HexColor('#999999'))
    ))
    story.append(Paragraph(
        f"Document généré le {datetime.now().strftime('%d/%m/%Y à %H:%M')}",
        ParagraphStyle('Footer', parent=normal_style, fontSize=8, alignment=TA_CENTER, textColor=HexColor('#999999'))
    ))
    story.append(Paragraph(
        "ONIAN EasyM - Système de Gestion des Ressources Humaines - Version 1.2",
        ParagraphStyle('Footer', parent=normal_style, fontSize=8, alignment=TA_CENTER, textColor=HexColor('#999999'))
    ))

    # Générer le PDF
    doc.build(story)

    print(f"✅ PDF généré avec succès : {filename}")
    return filename


if __name__ == '__main__':
    create_roles_guide()