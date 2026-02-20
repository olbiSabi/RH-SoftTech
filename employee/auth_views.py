import logging
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordChangeForm, PasswordResetForm
from django.contrib.auth.tokens import default_token_generator
from django.contrib.auth.views import PasswordResetConfirmView
from django.http import HttpResponse
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode, url_has_allowed_host_and_scheme
from django.utils.encoding import force_bytes, force_str
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.conf import settings
from .models import UserSecurity
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Count, Sum
from django.utils import timezone
from datetime import timedelta
from employee.models import ZY00, ZYCO
from absence.models import Absence, AcquisitionConges
from departement.models import ZDDE

# Configuration du logger
logger = logging.getLogger(__name__)

def login_view(request):
    """Vue de connexion pour les employés avec sécurité renforcée"""
    # Si l'utilisateur est déjà connecté, rediriger vers le dashboard
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        logger.info("🔐 TENTATIVE DE CONNEXION pour {username}")

        # Vérifier d'abord si l'utilisateur existe
        try:
            user = User.objects.get(username=username)
            security, created = UserSecurity.objects.get_or_create(user=user)

            # DEBUG: Afficher l'état du compte
            logger.debug("🔍 ÉTAT DU COMPTE:")
            logger.debug("   - Username: {user.username}")
            logger.info("   - Login attempts: {security.login_attempts}")
            logger.debug("   - Is locked: {security.is_locked}")
            logger.debug("   - Locked until: {security.locked_until}")
            logger.debug("   - is_account_locked(): {security.is_account_locked()}")

            # Vérifier si le compte est bloqué
            if security.is_account_locked():
                logger.error("❌ COMPTE BLOQUÉ DÉTECTÉ")
                messages.error(
                    request,
                    "❌ Votre compte est temporairement bloqué suite à trop de tentatives de connexion. "
                    "Veuillez réinitialiser votre mot de passe ou attendre 24 heures."
                )
                # Envoyer un email d'alerte
                send_lock_notification_email(user, request)
                return redirect('login')
            else:
                logger.info("✅ COMPTE NON BLOQUÉ - Procéder à l'authentification")

        except User.DoesNotExist:
            logger.error("❌ UTILISATEUR NON TROUVÉ: {username}")
            messages.error(request, "❌ Nom d'utilisateur ou mot de passe incorrect.")
            return redirect('login')

        # Authentifier l'utilisateur
        user = authenticate(request, username=username, password=password)

        if user is not None:
            logger.info("✅ AUTHENTIFICATION RÉUSSIE pour {username}")
            # Réinitialiser les tentatives en cas de succès
            security.reset_attempts()
            logger.info("✅ Tentatives réinitialisées pour {username}")

            # Vérifier si l'employé existe et est actif
            try:
                employe = user.employe
                if employe.etat != 'actif':
                    messages.error(request, "❌ Votre compte est inactif. Contactez l'administrateur.")
                    return redirect('login')

                # Connexion réussie
                login(request, user)
                logger.info("✅ CONNEXION RÉUSSIE - Redirection vers dashboard")
                # Rediriger vers la page demandée ou le dashboard
                next_url = request.GET.get('next', '')
                if next_url and url_has_allowed_host_and_scheme(next_url, allowed_hosts={request.get_host()}, require_https=request.is_secure()):
                    return redirect(next_url)
                return redirect('dashboard')

            except ZY00.DoesNotExist:
                messages.warning(request, "⚠️ Aucun profil employé associé à ce compte.")
                login(request, user)
                return redirect('dashboard')

        else:
            logger.error("❌ AUTHENTIFICATION ÉCHOUÉE pour {username}")
            # Authentification échouée - incrémenter les tentatives
            try:
                user = User.objects.get(username=username)
                security = UserSecurity.objects.get(user=user)

                # Incrémenter et vérifier le blocage
                is_now_locked = security.increment_attempts()
                logger.info("📈 Tentative incrémentée: {security.login_attempts}/3")

                remaining_attempts = 3 - security.login_attempts

                if is_now_locked:
                    logger.info("🔒 COMPTE BLOQUÉ après 3 tentatives")
                    messages.error(
                        request,
                        "❌ Votre compte a été bloqué suite à 3 tentatives de connexion échouées. "
                        "Un email a été envoyé avec les instructions de déblocage."
                    )
                    # Envoyer l'email de blocage
                    send_lock_notification_email(user, request)
                else:
                    messages.error(
                        request,
                        f"❌ Nom d'utilisateur ou mot de passe incorrect. "
                        f"Il vous reste {remaining_attempts} tentative(s)."
                    )

            except User.DoesNotExist:
                messages.error(request, "❌ Nom d'utilisateur ou mot de passe incorrect.")

    else:
        logger.info("📝 AFFICHAGE PAGE LOGIN (GET request)")

    return render(request, 'employee/login.html')

def send_lock_notification_email(user, request):
    """Envoyer un email de notification de blocage de compte"""
    try:
        employe = user.employe
        nom_complet = f"{employe.prenoms} {employe.nom}"
    except Exception:
        nom_complet = user.username

    subject = "🔒 Compte bloqué - ONIAN-EasyM"

    # Construire l'URL de réinitialisation avec gestion d'erreur
    token = default_token_generator.make_token(user)
    uid = urlsafe_base64_encode(force_bytes(user.pk))

    # Utiliser request pour construire l'URL ou une valeur par défaut
    try:
        reset_url = request.build_absolute_uri(
            f'/employe/password-reset-confirm/{uid}/{token}/'
        )
    except Exception:
        reset_url = f"{settings.SITE_URL}/employe/password-reset-confirm/{uid}/{token}/"

    message = f"""
    Bonjour {nom_complet},

    Votre compte ONIAN-EasyM a été temporairement bloqué suite à 3 tentatives de connexion infructueuses.

    Pour débloquer votre compte, veuillez réinitialiser votre mot de passe en cliquant sur le lien suivant :
    {reset_url}

    Ce lien expirera dans 24 heures.

    Si vous n'êtes pas à l'origine de ces tentatives de connexion, veuillez contacter immédiatement votre administrateur système.

    Cordialement,
    L'équipe ONIAN-EasyM
    """

    html_message = render_to_string('employee/password/account_locked_email.html', {
        'user': user,
        'employe': getattr(user, 'employe', None),
        'reset_url': reset_url,
        'site_name': 'ONIAN-EasyM',
    })

    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'ONIAN-EasyM <noreply@onian-easym.com>'),
            recipient_list=[user.email],
            html_message=html_message,
            fail_silently=False,
        )
        logger.info("✅ Email de blocage envoyé à {user.email}")
    except Exception as e:
        logger.error("❌ Erreur envoi email blocage: {e}")

def logout_view(request):
    """Vue de déconnexion"""
    if request.user.is_authenticated:
        # Correction pour récupérer le nom de l'employé
        try:
            username = request.user.employe.nom if hasattr(request.user, 'employe') else request.user.username
        except Exception:
            username = request.user.username
        logout(request)
        #messages.success(request, f"👋 Au revoir {username}, vous avez été déconnecté avec succès.")
    return redirect('login')




@login_required
def dashboard_view(request):
    """Tableau de bord après connexion"""
    try:
        employe = request.user.employe
        date_actuelle = timezone.now().date()

        # ========================================
        # VÉRIFIER LE TYPE D'UTILISATEUR
        # ========================================

        # Vérifier si l'employé a des droits admin (utiliser getattr pour éviter AttributeError)
        est_admin = any([
            getattr(employe, 'peut_embaucher', False),
            getattr(employe, 'peut_gerer_parametrage_app', False),
            getattr(employe, 'est_drh', False),
            getattr(employe, 'est_assistant_rh', False),
            request.user.is_superuser
        ])

        # ========================================
        # DONNÉES POUR DASHBOARD EMPLOYÉ
        # (Toujours nécessaires)
        # ========================================

        # Solde de congés de l'employé connecté
        annee_acquisition = date_actuelle.year - 1
        try:
            solde_conges = AcquisitionConges.objects.get(
                employe=employe,
                annee_reference=annee_acquisition
            )
        except AcquisitionConges.DoesNotExist:
            solde_conges = None

        # Ses absences récentes
        mes_absences = Absence.objects.filter(
            employe=employe
        ).select_related('type_absence').order_by('-date_debut')[:5]

        # Ses absences en attente
        absences_en_attente = Absence.objects.filter(
            employe=employe,
            statut__in=['EN_ATTENTE_MANAGER', 'EN_ATTENTE_RH', 'BROUILLON']
        ).count()

        # Jours pris cette année par l'employé
        jours_pris_annee = Absence.objects.filter(
            employe=employe,
            date_debut__year=date_actuelle.year,
            statut='VALIDE'
        ).aggregate(total=Sum('jours_ouvrables'))['total'] or 0

        # Taux de présence
        jours_travailles_annee = (date_actuelle - date_actuelle.replace(month=1, day=1)).days
        if jours_travailles_annee > 0:
            taux_presence = round(((jours_travailles_annee - jours_pris_annee) / jours_travailles_annee) * 100)
        else:
            taux_presence = 100

        # Son contrat actuel
        contrat_actuel = ZYCO.objects.filter(
            employe=employe,
            actif=True
        ).first()

        # Son manager
        manager = None
        try:
            affectation = employe.affectation_actuelle
            if affectation and affectation.poste and affectation.poste.DEPARTEMENT:
                from departement.models import ZYMA
                manager_obj = ZYMA.get_manager_actif(affectation.poste.DEPARTEMENT)
                manager = manager_obj.employe if manager_obj else None
        except Exception:
            pass

        # Context de base (pour employé)
        context = {
            'employe': employe,
            'date_actuelle': date_actuelle,
            'solde_conges': solde_conges,
            'mes_absences': mes_absences,
            'absences_en_attente': absences_en_attente,
            'jours_pris_annee': jours_pris_annee,
            'taux_presence': taux_presence,
            'contrat_actuel': contrat_actuel,
            'manager': manager,
        }

        # ========================================
        # DONNÉES SUPPLÉMENTAIRES POUR DASHBOARD ADMIN
        # (Uniquement si l'utilisateur est admin)
        # ========================================

        if est_admin:
            # Total employés
            total_employes = ZY00.objects.count()

            # Employés actifs
            employes_actifs = ZY00.objects.filter(etat='actif').count()

            # Employés en attente
            employes_attente = ZY00.objects.filter(
                Q(etat='en_attente') | Q(etat='nouveau')
            ).count()

            # Contrats actifs (tous les employés)
            contrats_actifs = ZYCO.objects.filter(
                Q(date_fin__gte=date_actuelle) | Q(date_fin__isnull=True),
                actif=True
            ).count()

            # Nouveaux employés (30 derniers jours)
            date_limite = date_actuelle - timedelta(days=30)

            embauches_attente = ZY00.objects.filter(
                etat='en_attente',
                date_entree_entreprise__gte=date_limite
            ).select_related('entreprise').order_by('-date_entree_entreprise')[:5]

            dernieres_embauches = ZY00.objects.filter(
                etat='actif',
                date_entree_entreprise__gte=date_limite
            ).select_related('entreprise').order_by('-date_entree_entreprise')[:5]

            # Absences en attente de validation (tous les employés)
            absences_attente_manager = Absence.objects.filter(
                statut='EN_ATTENTE_MANAGER'
            ).count()

            absences_attente_rh = Absence.objects.filter(
                statut='EN_ATTENTE_RH'
            ).count()

            absences_total_attente = absences_attente_manager + absences_attente_rh

            # Absences du mois en cours (tous les employés)
            premier_jour_mois = date_actuelle.replace(day=1)
            absences_mois = Absence.objects.filter(
                date_debut__gte=premier_jour_mois,
                statut='VALIDE'
            ).count()

            # Départements
            total_departements = ZDDE.objects.filter(STATUT=True).count()

            try:
                departements_effectifs = ZDDE.objects.filter(STATUT=True).annotate(
                    effectif=Count('postes__affectations', filter=Q(
                        postes__affectations__date_fin__isnull=True,
                        postes__affectations__employe__etat='actif'
                    ))
                ).order_by('-effectif')[:5]
            except Exception:
                departements_effectifs = ZDDE.objects.filter(STATUT=True).order_by('CODE')[:5]

            # Anniversaires de travail
            mois_actuel = date_actuelle.month
            try:
                anniversaires = ZY00.objects.filter(
                    etat='actif',
                    date_entree_entreprise__month=mois_actuel
                ).exclude(
                    date_entree_entreprise__year=date_actuelle.year
                ).select_related('entreprise').order_by('date_entree_entreprise')[:10]
            except Exception:
                anniversaires = []

            # Contrats arrivant à échéance
            date_limite_contrat = date_actuelle + timedelta(days=60)
            try:
                contrats_echeance = ZYCO.objects.filter(
                    date_fin__gte=date_actuelle,
                    date_fin__lte=date_limite_contrat,
                    actif=True
                ).select_related('employe', 'employe__entreprise').order_by('date_fin')[:5]
            except Exception:
                contrats_echeance = []

            # Soldes de congés faibles
            try:
                soldes_faibles = AcquisitionConges.objects.filter(
                    annee_reference=annee_acquisition,
                    jours_restants__lte=5,
                    jours_restants__gt=0,
                    employe__etat='actif'
                ).select_related('employe').order_by('jours_restants')[:5]
            except Exception:
                soldes_faibles = []

            # Ajouter les données admin au context
            context.update({
                'total_employes': total_employes,
                'employes_actifs': employes_actifs,
                'employes_attente': employes_attente,
                'contrats_actifs': contrats_actifs,
                'embauches_attente': embauches_attente,
                'dernieres_embauches': dernieres_embauches,
                'absences_total_attente': absences_total_attente,
                'absences_attente_manager': absences_attente_manager,
                'absences_attente_rh': absences_attente_rh,
                'absences_mois': absences_mois,
                'total_departements': total_departements,
                'departements_effectifs': departements_effectifs,
                'anniversaires': anniversaires,
                'contrats_echeance': contrats_echeance,
                'soldes_faibles': soldes_faibles,
            })

        return render(request, 'home.html', context)

    except ZY00.DoesNotExist:
        messages.warning(request, "⚠️ Aucun profil employé trouvé.")
        return redirect('login')

@login_required
def change_password_view(request):
    """Vue pour changer le mot de passe"""
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            # Mettre à jour la session pour éviter la déconnexion
            update_session_auth_hash(request, user)
            messages.success(request, '✅ Votre mot de passe a été modifié avec succès !')
            return redirect('dashboard')
        else:
            messages.error(request, '❌ Veuillez corriger les erreurs ci-dessous.')
    else:
        form = PasswordChangeForm(request.user)

    return render(request, 'employee/password/change_password.html', {'form': form})

def password_reset_request(request):
    """Vue pour demander une réinitialisation de mot de passe"""

    if request.method == 'POST':
        form = PasswordResetForm(request.POST)

        logger.debug("=" * 80)
        logger.debug("🔍 DÉBUT PASSWORD RESET REQUEST")
        logger.debug("=" * 80)

        if form.is_valid():
            email = form.cleaned_data['email']
            logger.debug("📧 Email saisi: {email}")

            try:
                user = User.objects.get(email=email)
                logger.info("✅ Utilisateur trouvé: {user.username}")
                logger.debug("   - Email: {user.email}")
                logger.debug("   - ID: {user.pk}")

                try:
                    employe = user.employe
                    logger.debug("   - Employé: {employe.nom} {employe.prenoms}")
                except Exception:
                    logger.debug("   - Pas de profil employé associé")

                # ✅ DÉBLOQUER LE COMPTE SI IL ÉTAIT BLOQUÉ (UNIQUEMENT ICI)
                try:
                    security = UserSecurity.objects.get(user=user)
                    if security.is_locked:
                        logger.debug("🔓 Déblocage du compte {user.username}")
                        security.reset_attempts()  # Réinitialiser complètement
                        messages.info(request,
                                      "Votre compte a été débloqué. Vous pouvez maintenant réinitialiser votre mot de passe.")
                    else:
                        logger.debug("ℹ️ Compte {user.username} n'était pas bloqué")
                except UserSecurity.DoesNotExist:
                    # Créer le profil de sécurité s'il n'existe pas
                    UserSecurity.objects.create(user=user)
                    logger.info("✅ Profil de sécurité créé pour {user.username}")

                # Générer le token
                token = default_token_generator.make_token(user)
                uid = urlsafe_base64_encode(force_bytes(user.pk))

                logger.info("\n🔐 Token généré: {token}")
                logger.debug("🆔 UID généré: {uid}")

                # Construire l'URL - CORRECTION DU CHEMIN
                reset_url = request.build_absolute_uri(
                    f'/employe/password-reset-confirm/{uid}/{token}/'  # ← AJOUTEZ 'employe/'
                )
                logger.debug("🔗 URL de réinitialisation: {reset_url}")

                # Préparer le contexte de l'email
                employe = None
                try:
                    employe = user.employe
                except Exception:
                    pass

                email_context = {
                    'user': user,
                    'employe': employe,
                    'reset_url': reset_url,
                    'site_name': 'ONIAN-EasyM',
                }

                # Générer le message
                subject = "Réinitialisation de votre mot de passe - ONIAN-EasyM"
                message = render_to_string('employee/password/password_reset_email.html', email_context)

                logger.debug("\n📨 Sujet: {subject}")
                logger.debug("📄 Message généré (longueur: {len(message)} caractères)")

                # ✅ CRÉER UNE CONNEXION EMAIL CONSOLE FORCÉE
                try:
                    logger.info("\n🚀 TENTATIVE D'ENVOI DE L'EMAIL AVEC BACKEND CONSOLE FORCÉ...")

                    # Importer le backend console directement
                    from django.core.mail.backends.console import EmailBackend as ConsoleBackend

                    # Créer une connexion console
                    console_connection = ConsoleBackend()

                    # Créer le message email
                    from django.core.mail import EmailMessage

                    email_message = EmailMessage(
                        subject=subject,
                        body=message,
                        from_email='ONIAN-EasyM <noreply@hronian.local>',
                        to=[email],
                        connection=console_connection
                    )
                    email_message.content_subtype = 'html'  # Pour envoyer en HTML

                    # Envoyer
                    email_message.send()

                    logger.info("✅ EMAIL ENVOYÉ AVEC SUCCÈS VIA CONSOLE!")
                    logger.debug("📧 Vérifiez la console ci-dessus pour voir l'email")
                    logger.debug("=" * 80)

                    messages.success(
                        request,
                        '✅ Un email de réinitialisation a été envoyé. Votre compte a été débloqué.'
                    )

                    return redirect('login')

                except Exception as e:
                    logger.error("\n💥 ERREUR LORS DE L'ENVOI:")
                    logger.debug("   Type: {type(e).__name__}")
                    logger.debug("   Message: {str(e)}")

                    import traceback
                    logger.debug("\n🔍 TRACEBACK COMPLET:")
                    logger.exception("Traceback complet:")
                    logger.debug("=" * 80)

                    messages.error(
                        request,
                        "❌ Une erreur est survenue lors de l'envoi de l'email. Veuillez réessayer."
                    )
                    # Même en cas d'erreur d'envoi, le compte est débloqué
                    return redirect('login')

            except User.DoesNotExist:
                logger.error("❌ AUCUN utilisateur trouvé avec l'email: {email}")
                messages.success(
                    request,
                    '✅ Si un compte existe avec cet email, vous recevrez un lien de réinitialisation.'
                )
                return redirect('login')

        else:
            logger.error("❌ Formulaire invalide: {form.errors}")
            messages.error(request, '❌ Veuillez corriger les erreurs ci-dessous.')

    else:
        form = PasswordResetForm()

    return render(request, 'employee/password/password_reset_request.html', {'form': form})

class CustomPasswordResetConfirmView(PasswordResetConfirmView):
    """Vue personnalisée pour confirmer la réinitialisation du mot de passe"""
    template_name = 'employee/password/password_reset_confirm.html'

    def form_valid(self, form):
        # Récupérer l'utilisateur AVANT la réinitialisation
        user = form.user  # ← Utiliser form.user au lieu de form.save()

        logger.debug("🔄 RÉINITIALISATION MOT DE PASSE pour {user.username}")

        # ✅ DÉBLOQUER LE COMPTE AVANT la réinitialisation
        try:
            security = UserSecurity.objects.get(user=user)
            logger.debug("🔍 ÉTAT AVANT DÉBLOCAGE:")
            logger.info("   - attempts: {security.login_attempts}")
            logger.debug("   - locked: {security.is_locked}")

            # Réinitialisation FORCÉE
            security.login_attempts = 0
            security.is_locked = False
            security.locked_until = None
            security.last_login_attempt = None
            security.save()

            # Recharger pour vérifier
            security.refresh_from_db()
            logger.info("✅ ÉTAT APRÈS DÉBLOCAGE:")
            logger.info("   - attempts: {security.login_attempts}")
            logger.debug("   - locked: {security.is_locked}")

        except UserSecurity.DoesNotExist:
            UserSecurity.objects.create(user=user)
            logger.info("✅ Profil sécurité créé pour {user.username}")

        # Maintenant sauvegarder le nouveau mot de passe
        response = super().form_valid(form)

        messages.success(
            self.request,
            '✅ Votre mot de passe a été réinitialisé avec succès et votre compte a été débloqué !'
        )

        return response

    def get_success_url(self):
        return '/employe/login/'

def test_reset_account(request, username):
    """Vue de test pour réinitialiser manuellement un compte"""
    try:
        user = User.objects.get(username=username)
        security, created = UserSecurity.objects.get_or_create(user=user)

        logger.debug("=" * 50)
        logger.debug("🧪 TEST RÉINITIALISATION MANUELLE")
        logger.debug("Compte: {user.username}")
        logger.debug("AVANT reset_attempts():")
        logger.info("  - login_attempts: {security.login_attempts}")
        logger.debug("  - is_locked: {security.is_locked}")
        logger.debug("  - locked_until: {security.locked_until}")

        # Appel de la méthode
        security.reset_attempts()

        # Recharger depuis la base de données
        security.refresh_from_db()

        logger.debug("APRÈS reset_attempts():")
        logger.info("  - login_attempts: {security.login_attempts}")
        logger.debug("  - is_locked: {security.is_locked}")
        logger.debug("  - locked_until: {security.locked_until}")
        logger.debug("=" * 50)

        return HttpResponse(f"""
        <h1>Test réinitialisation - {user.username}</h1>
        <p><strong>AVANT:</strong></p>
        <ul>
            <li>Attempts: {security.login_attempts}</li>
            <li>Locked: {security.is_locked}</li>
            <li>Locked until: {security.locked_until}</li>
        </ul>
        <p><strong>APRÈS:</strong></p>
        <ul>
            <li>Attempts: 0</li>
            <li>Locked: False</li>
            <li>Locked until: None</li>
        </ul>
        <p><a href="/employe/login/">Tester la connexion</a></p>
        """)

    except User.DoesNotExist:
        return HttpResponse("Utilisateur non trouvé")