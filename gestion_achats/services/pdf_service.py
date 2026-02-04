"""
Service métier pour la génération de PDF.

Ce service encapsule toute la logique métier liée à la génération de documents PDF,
notamment les bons de commande.
"""

import logging
from io import BytesIO
from django.conf import settings
from django.template.loader import render_to_string

from gestion_achats.exceptions import PDFGenerationError

logger = logging.getLogger(__name__)


class PDFService:
    """Service pour la génération de documents PDF."""

    @staticmethod
    def generer_pdf_bon_commande(bc):
        """
        Génère le PDF d'un bon de commande.

        Args:
            bc: Le bon de commande

        Returns:
            bytes: Contenu du PDF

        Raises:
            PDFGenerationError: Si la génération échoue
        """
        try:
            # Importer WeasyPrint (ou ReportLab selon préférence)
            # Pour l'instant, on utilise WeasyPrint qui est plus simple pour HTML->PDF
            try:
                from weasyprint import HTML, CSS
                from weasyprint.text.fonts import FontConfiguration
            except ImportError:
                logger.error(
                    "WeasyPrint n'est pas installé. "
                    "Installez-le avec: pip install weasyprint"
                )
                raise PDFGenerationError(
                    "La bibliothèque WeasyPrint n'est pas installée"
                )

            # Préparer les données pour le template
            context = {
                'bc': bc,
                'entreprise': {
                    'nom': getattr(settings, 'COMPANY_NAME', 'ONIAN'),
                    'adresse': getattr(settings, 'COMPANY_ADDRESS', ''),
                    'code_postal': getattr(settings, 'COMPANY_ZIP', ''),
                    'ville': getattr(settings, 'COMPANY_CITY', ''),
                    'telephone': getattr(settings, 'COMPANY_PHONE', ''),
                    'email': getattr(settings, 'COMPANY_EMAIL', ''),
                    'nif': getattr(settings, 'COMPANY_NIF', ''),
                    'logo_url': getattr(settings, 'COMPANY_LOGO_PATH', None),
                },
                'date_generation': bc.date_emission or bc.date_creation,
            }

            # Rendre le template HTML
            html_content = render_to_string(
                'gestion_achats/pdf/bon_commande.html',
                context
            )

            # CSS personnalisé pour le PDF
            css_content = """
                @page {
                    size: A4;
                    margin: 2cm;
                }

                body {
                    font-family: 'DejaVu Sans', Arial, sans-serif;
                    font-size: 10pt;
                    color: #333;
                }

                h1 {
                    color: #2c3e50;
                    font-size: 18pt;
                    margin-bottom: 10px;
                }

                h2 {
                    color: #34495e;
                    font-size: 14pt;
                    margin-top: 15px;
                    margin-bottom: 8px;
                    border-bottom: 2px solid #3498db;
                    padding-bottom: 5px;
                }

                table {
                    width: 100%;
                    border-collapse: collapse;
                    margin-top: 10px;
                    margin-bottom: 10px;
                }

                table th {
                    background-color: #3498db;
                    color: white;
                    padding: 8px;
                    text-align: left;
                    font-weight: bold;
                }

                table td {
                    padding: 6px 8px;
                    border-bottom: 1px solid #ddd;
                }

                table tr:nth-child(even) {
                    background-color: #f9f9f9;
                }

                .header {
                    display: flex;
                    justify-content: space-between;
                    margin-bottom: 20px;
                }

                .info-block {
                    margin-bottom: 15px;
                }

                .totals {
                    text-align: right;
                    margin-top: 15px;
                }

                .totals table {
                    width: 40%;
                    margin-left: auto;
                }

                .footer {
                    margin-top: 30px;
                    padding-top: 15px;
                    border-top: 1px solid #ddd;
                    font-size: 9pt;
                    color: #666;
                }
            """

            # Convertir HTML en PDF
            font_config = FontConfiguration()
            html = HTML(string=html_content)
            css = CSS(string=css_content, font_config=font_config)

            pdf_bytes = html.write_pdf(stylesheets=[css], font_config=font_config)

            logger.info(f"PDF généré pour le BC {bc.numero}")

            return pdf_bytes

        except ImportError as e:
            logger.error(f"Erreur d'import lors de la génération du PDF: {str(e)}")
            raise PDFGenerationError(f"Bibliothèque manquante: {str(e)}")
        except Exception as e:
            logger.error(f"Erreur lors de la génération du PDF: {str(e)}")
            raise PDFGenerationError(f"Impossible de générer le PDF: {str(e)}")

    @staticmethod
    def generer_pdf_reception(reception):
        """
        Génère le PDF d'un bon de réception.

        Args:
            reception: La réception

        Returns:
            bytes: Contenu du PDF

        Note:
            À implémenter selon les besoins
        """
        # TODO: Implémenter la génération de PDF pour les réceptions
        logger.warning("Génération de PDF pour réception non encore implémentée")
        raise PDFGenerationError("Fonctionnalité non encore implémentée")

    @staticmethod
    def generer_rapport_budget(budget):
        """
        Génère un rapport PDF pour un budget.

        Args:
            budget: L'enveloppe budgétaire

        Returns:
            bytes: Contenu du PDF

        Note:
            À implémenter selon les besoins
        """
        # TODO: Implémenter la génération de rapport budgétaire
        logger.warning("Génération de rapport budgétaire non encore implémentée")
        raise PDFGenerationError("Fonctionnalité non encore implémentée")
