from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordChangeForm, PasswordResetForm
from django.contrib.auth.tokens import default_token_generator
from django.contrib.auth.views import PasswordResetConfirmView
from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.contrib import messages
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from .models import ZY00
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.conf import settings
from .models import UserSecurity


def login_view(request):
    """Vue de connexion pour les employés avec sécurité renforcée"""
    # Si l'utilisateur est déjà connecté, rediriger vers le dashboard
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        print(f"🔐 TENTATIVE DE CONNEXION pour {username}")

        # Vérifier d'abord si l'utilisateur existe
        try:
            user = User.objects.get(username=username)
            security, created = UserSecurity.objects.get_or_create(user=user)

            # DEBUG: Afficher l'état du compte
            print(f"🔍 ÉTAT DU COMPTE:")
            print(f"   - Username: {user.username}")
            print(f"   - Login attempts: {security.login_attempts}")
            print(f"   - Is locked: {security.is_locked}")
            print(f"   - Locked until: {security.locked_until}")
            print(f"   - is_account_locked(): {security.is_account_locked()}")

            # Vérifier si le compte est bloqué
            if security.is_account_locked():
                print(f"❌ COMPTE BLOQUÉ DÉTECTÉ")
                messages.error(
                    request,
                    "❌ Votre compte est temporairement bloqué suite à trop de tentatives de connexion. "
                    "Veuillez réinitialiser votre mot de passe ou attendre 24 heures."
                )
                # Envoyer un email d'alerte
                send_lock_notification_email(user, request)
                return redirect('login')
            else:
                print(f"✅ COMPTE NON BLOQUÉ - Procéder à l'authentification")

        except User.DoesNotExist:
            print(f"❌ UTILISATEUR NON TROUVÉ: {username}")
            messages.error(request, "❌ Nom d'utilisateur ou mot de passe incorrect.")
            return redirect('login')

        # Authentifier l'utilisateur
        user = authenticate(request, username=username, password=password)

        if user is not None:
            print(f"✅ AUTHENTIFICATION RÉUSSIE pour {username}")
            # Réinitialiser les tentatives en cas de succès
            security.reset_attempts()
            print(f"✅ Tentatives réinitialisées pour {username}")

            # Vérifier si l'employé existe et est actif
            try:
                employe = user.employe
                if employe.etat != 'actif':
                    messages.error(request, "❌ Votre compte est inactif. Contactez l'administrateur.")
                    return redirect('login')

                # Connexion réussie
                login(request, user)
                print(f"✅ CONNEXION RÉUSSIE - Redirection vers dashboard")
                # Rediriger vers la page demandée ou le dashboard
                next_url = request.GET.get('next', 'dashboard')
                return redirect(next_url)

            except ZY00.DoesNotExist:
                messages.warning(request, "⚠️ Aucun profil employé associé à ce compte.")
                login(request, user)
                return redirect('dashboard')

        else:
            print(f"❌ AUTHENTIFICATION ÉCHOUÉE pour {username}")
            # Authentification échouée - incrémenter les tentatives
            try:
                user = User.objects.get(username=username)
                security = UserSecurity.objects.get(user=user)

                # Incrémenter et vérifier le blocage
                is_now_locked = security.increment_attempts()
                print(f"📈 Tentative incrémentée: {security.login_attempts}/3")

                remaining_attempts = 3 - security.login_attempts

                if is_now_locked:
                    print(f"🔒 COMPTE BLOQUÉ après 3 tentatives")
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
        print(f"📝 AFFICHAGE PAGE LOGIN (GET request)")

    return render(request, 'employee/login.html')

def send_lock_notification_email(user, request):
    """Envoyer un email de notification de blocage de compte"""
    try:
        employe = user.employe
        nom_complet = f"{employe.prenoms} {employe.nom}"
    except:
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
    except:
        # Fallback si SITE_URL n'est pas défini
        reset_url = f"http://127.0.0.1:8000/employe/password-reset-confirm/{uid}/{token}/"

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
        print(f"✅ Email de blocage envoyé à {user.email}")
    except Exception as e:
        print(f"❌ Erreur envoi email blocage: {e}")

def logout_view(request):
    """Vue de déconnexion"""
    if request.user.is_authenticated:
        # Correction pour récupérer le nom de l'employé
        try:
            username = request.user.employe.nom if hasattr(request.user, 'employe') else request.user.username
        except:
            username = request.user.username
        logout(request)
        #messages.success(request, f"👋 Au revoir {username}, vous avez été déconnecté avec succès.")
    return redirect('login')


# employee/auth_views.py

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Count, Sum
from django.utils import timezone
from datetime import timedelta
from employee.models import ZY00, ZYCO
from absence.models import Absence, AcquisitionConges
from departement.models import ZDDE


@login_required
def dashboard_view(request):
    """Tableau de bord après connexion"""
    try:
        employe = request.user.employe

        # ========================================
        # STATISTIQUES EMPLOYÉS
        # ========================================

        # Total employés
        total_employes = ZY00.objects.count()

        # Employés actifs
        employes_actifs = ZY00.objects.filter(etat='actif').count()

        # Employés en attente
        employes_attente = ZY00.objects.filter(
            Q(etat='en_attente') | Q(etat='nouveau')
        ).count()

        # Contrats actifs
        date_actuelle = timezone.now().date()
        contrats_actifs = ZYCO.objects.filter(
            Q(date_fin__gte=date_actuelle) | Q(date_fin__isnull=True),
            actif=True
        ).count()

        # ========================================
        # NOUVEAUX EMPLOYÉS (30 derniers jours)
        # ========================================

        date_limite = date_actuelle - timedelta(days=30)

        # Employés en attente de validation
        embauches_attente = ZY00.objects.filter(
            etat='en_attente',
            date_entree_entreprise__gte=date_limite
        ).select_related('entreprise').order_by('-date_entree_entreprise')[:5]

        # Dernières embauches validées
        dernieres_embauches = ZY00.objects.filter(
            etat='actif',
            date_entree_entreprise__gte=date_limite
        ).select_related('entreprise').order_by('-date_entree_entreprise')[:5]

        # ========================================
        # STATISTIQUES ABSENCES
        # ========================================

        # Absences en attente de validation
        absences_attente_manager = Absence.objects.filter(
            statut='EN_ATTENTE_MANAGER'
        ).count()

        absences_attente_rh = Absence.objects.filter(
            statut='EN_ATTENTE_RH'
        ).count()

        absences_total_attente = absences_attente_manager + absences_attente_rh

        # Absences du mois en cours
        premier_jour_mois = date_actuelle.replace(day=1)
        absences_mois = Absence.objects.filter(
            date_debut__gte=premier_jour_mois,
            statut='VALIDE'
        ).count()

        # ========================================
        # DÉPARTEMENTS
        # ========================================

        # ✅ CORRECTION FINALE : STATUT est un BooleanField
        # Total départements actifs (STATUT=True)
        total_departements = ZDDE.objects.filter(STATUT=True).count()

        # Départements avec leur effectif
        try:
            from employee.models import ZYAF
            departements_effectifs = ZDDE.objects.filter(STATUT=True).annotate(
                effectif=Count('postes__affectations', filter=Q(
                    postes__affectations__date_fin__isnull=True,
                    postes__affectations__employe__etat='actif'
                ))
            ).order_by('-effectif')[:5]
        except Exception:
            # Version simplifiée si erreur
            departements_effectifs = ZDDE.objects.filter(STATUT=True).order_by('CODE')[:5]

        # ========================================
        # ANNIVERSAIRES DE TRAVAIL (ce mois)
        # ========================================

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

        # ========================================
        # CONTRATS ARRIVANT À ÉCHÉANCE (60 jours)
        # ========================================

        date_limite_contrat = date_actuelle + timedelta(days=60)
        try:
            contrats_echeance = ZYCO.objects.filter(
                date_fin__gte=date_actuelle,
                date_fin__lte=date_limite_contrat,
                actif=True
            ).select_related('employe', 'employe__entreprise').order_by('date_fin')[:5]
        except Exception:
            contrats_echeance = []

        # ========================================
        # SOLDES DE CONGÉS À SURVEILLER
        # ========================================

        annee_acquisition = date_actuelle.year - 1
        try:
            soldes_faibles = AcquisitionConges.objects.filter(
                annee_reference=annee_acquisition,
                jours_restants__lte=5,
                jours_restants__gt=0,
                employe__etat='actif'
            ).select_related('employe').order_by('jours_restants')[:5]
        except Exception:
            soldes_faibles = []

        # ========================================
        # CONTEXT
        # ========================================

        context = {
            'employe': employe,

            # Statistiques principales
            'total_employes': total_employes,
            'employes_actifs': employes_actifs,
            'employes_attente': employes_attente,
            'contrats_actifs': contrats_actifs,

            # Embauches
            'embauches_attente': embauches_attente,
            'dernieres_embauches': dernieres_embauches,

            # Absences
            'absences_total_attente': absences_total_attente,
            'absences_attente_manager': absences_attente_manager,
            'absences_attente_rh': absences_attente_rh,
            'absences_mois': absences_mois,

            # Départements
            'total_departements': total_departements,
            'departements_effectifs': departements_effectifs,

            # Alertes
            'anniversaires': anniversaires,
            'contrats_echeance': contrats_echeance,
            'soldes_faibles': soldes_faibles,
        }

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

        print("=" * 80)
        print("🔍 DÉBUT PASSWORD RESET REQUEST")
        print("=" * 80)

        if form.is_valid():
            email = form.cleaned_data['email']
            print(f"📧 Email saisi: {email}")

            try:
                user = User.objects.get(email=email)
                print(f"✅ Utilisateur trouvé: {user.username}")
                print(f"   - Email: {user.email}")
                print(f"   - ID: {user.pk}")

                try:
                    employe = user.employe
                    print(f"   - Employé: {employe.nom} {employe.prenoms}")
                except:
                    print("   - Pas de profil employé associé")

                # ✅ DÉBLOQUER LE COMPTE SI IL ÉTAIT BLOQUÉ (UNIQUEMENT ICI)
                try:
                    security = UserSecurity.objects.get(user=user)
                    if security.is_locked:
                        print(f"🔓 Déblocage du compte {user.username}")
                        security.reset_attempts()  # Réinitialiser complètement
                        messages.info(request,
                                      "Votre compte a été débloqué. Vous pouvez maintenant réinitialiser votre mot de passe.")
                    else:
                        print(f"ℹ️ Compte {user.username} n'était pas bloqué")
                except UserSecurity.DoesNotExist:
                    # Créer le profil de sécurité s'il n'existe pas
                    UserSecurity.objects.create(user=user)
                    print(f"✅ Profil de sécurité créé pour {user.username}")

                # Générer le token
                token = default_token_generator.make_token(user)
                uid = urlsafe_base64_encode(force_bytes(user.pk))

                print(f"\n🔐 Token généré: {token}")
                print(f"🆔 UID généré: {uid}")

                # Construire l'URL - CORRECTION DU CHEMIN
                reset_url = request.build_absolute_uri(
                    f'/employe/password-reset-confirm/{uid}/{token}/'  # ← AJOUTEZ 'employe/'
                )
                print(f"🔗 URL de réinitialisation: {reset_url}")

                # Préparer le contexte de l'email
                employe = None
                try:
                    employe = user.employe
                except:
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

                print(f"\n📨 Sujet: {subject}")
                print(f"📄 Message généré (longueur: {len(message)} caractères)")

                # ✅ CRÉER UNE CONNEXION EMAIL CONSOLE FORCÉE
                try:
                    print("\n🚀 TENTATIVE D'ENVOI DE L'EMAIL AVEC BACKEND CONSOLE FORCÉ...")

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

                    print("✅ EMAIL ENVOYÉ AVEC SUCCÈS VIA CONSOLE!")
                    print("📧 Vérifiez la console ci-dessus pour voir l'email")
                    print("=" * 80)

                    messages.success(
                        request,
                        '✅ Un email de réinitialisation a été envoyé. Votre compte a été débloqué.'
                    )

                    return redirect('login')

                except Exception as e:
                    print(f"\n💥 ERREUR LORS DE L'ENVOI:")
                    print(f"   Type: {type(e).__name__}")
                    print(f"   Message: {str(e)}")

                    import traceback
                    print("\n🔍 TRACEBACK COMPLET:")
                    print(traceback.format_exc())
                    print("=" * 80)

                    messages.error(
                        request,
                        f'❌ Erreur lors de l\'envoi de l\'email: {str(e)}'
                    )
                    # Même en cas d'erreur d'envoi, le compte est débloqué
                    return redirect('login')

            except User.DoesNotExist:
                print(f"❌ AUCUN utilisateur trouvé avec l'email: {email}")
                messages.success(
                    request,
                    '✅ Si un compte existe avec cet email, vous recevrez un lien de réinitialisation.'
                )
                return redirect('login')

        else:
            print(f"❌ Formulaire invalide: {form.errors}")
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

        print(f"🔄 RÉINITIALISATION MOT DE PASSE pour {user.username}")

        # ✅ DÉBLOQUER LE COMPTE AVANT la réinitialisation
        try:
            security = UserSecurity.objects.get(user=user)
            print(f"🔍 ÉTAT AVANT DÉBLOCAGE:")
            print(f"   - attempts: {security.login_attempts}")
            print(f"   - locked: {security.is_locked}")

            # Réinitialisation FORCÉE
            security.login_attempts = 0
            security.is_locked = False
            security.locked_until = None
            security.last_login_attempt = None
            security.save()

            # Recharger pour vérifier
            security.refresh_from_db()
            print(f"✅ ÉTAT APRÈS DÉBLOCAGE:")
            print(f"   - attempts: {security.login_attempts}")
            print(f"   - locked: {security.is_locked}")

        except UserSecurity.DoesNotExist:
            UserSecurity.objects.create(user=user)
            print(f"✅ Profil sécurité créé pour {user.username}")

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

        print("=" * 50)
        print(f"🧪 TEST RÉINITIALISATION MANUELLE")
        print(f"Compte: {user.username}")
        print(f"AVANT reset_attempts():")
        print(f"  - login_attempts: {security.login_attempts}")
        print(f"  - is_locked: {security.is_locked}")
        print(f"  - locked_until: {security.locked_until}")

        # Appel de la méthode
        security.reset_attempts()

        # Recharger depuis la base de données
        security.refresh_from_db()

        print(f"APRÈS reset_attempts():")
        print(f"  - login_attempts: {security.login_attempts}")
        print(f"  - is_locked: {security.is_locked}")
        print(f"  - locked_until: {security.locked_until}")
        print("=" * 50)

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