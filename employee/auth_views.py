from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordChangeForm, PasswordResetForm
from django.contrib.auth.tokens import default_token_generator
from django.contrib.auth.views import PasswordResetConfirmView
from django.core.mail import send_mail
from django.shortcuts import render, redirect
from django.contrib import messages
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.conf import settings
from .models import ZY00
from django.contrib.auth.models import User


def login_view(request):
    """Vue de connexion pour les employés"""
    # Si l'utilisateur est déjà connecté, rediriger vers le dashboard
    if request.user.is_authenticated:
        return redirect('dashboard')  # ← CHANGEMENT ICI

    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        # Authentifier l'utilisateur
        user = authenticate(request, username=username, password=password)

        if user is not None:
            # Vérifier si l'employé existe et est actif
            try:
                employe = user.employe
                if employe.etat != 'actif':
                    messages.error(request, "❌ Votre compte est inactif. Contactez l'administrateur.")
                    return redirect('login')

                # Connexion réussie
                login(request, user)
                # Rediriger vers la page demandée ou le dashboard
                next_url = request.GET.get('next', 'dashboard')  # ← CHANGEMENT ICI
                return redirect(next_url)

            except ZY00.DoesNotExist:
                messages.warning(request, "⚠️ Aucun profil employé associé à ce compte.")
                login(request, user)
                return redirect('dashboard')  # ← CHANGEMENT ICI
        else:
            messages.error(request, "❌ Nom d'utilisateur ou mot de passe incorrect.")

    return render(request, 'employee/login.html')

def logout_view(request):
    """Vue de déconnexion"""
    if request.user.is_authenticated:
        # Correction pour récupérer le nom de l'employé
        try:
            username = request.user.employe.nom if hasattr(request.user, 'employe') else request.user.username
        except:
            username = request.user.username
        logout(request)
        messages.success(request, f"👋 Au revoir {username}, vous avez été déconnecté avec succès.")
    return redirect('login')

@login_required
def dashboard_view(request):
    """Tableau de bord après connexion"""
    try:
        employe = request.user.employe
        context = {
            'employe': employe,
        }
        # Si votre template s'appelle home.html, utilisez-le ici
        return render(request, 'home.html', context)  # ← CHANGEMENT ICI
    except ZY00.DoesNotExist:
        messages.warning(request, "⚠️ Aucun profil employé trouvé.")
        return redirect('dashboard')

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

    # ⚠️ FORCER LE BACKEND CONSOLE (SOLUTION TEMPORAIRE)
    from django.core.mail import get_connection

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

            except User.DoesNotExist:
                print(f"❌ AUCUN utilisateur trouvé avec l'email: {email}")
                messages.success(
                    request,
                    '✅ Si un compte existe avec cet email, vous recevrez un lien de réinitialisation.'
                )
                return redirect('login')

            # Générer le token
            token = default_token_generator.make_token(user)
            uid = urlsafe_base64_encode(force_bytes(user.pk))

            print(f"\n🔐 Token généré: {token}")
            print(f"🆔 UID généré: {uid}")

            # Construire l'URL
            reset_url = request.build_absolute_uri(
                f'/password-reset-confirm/{uid}/{token}/'
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
                    '✅ Un email de réinitialisation a été envoyé.'
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
        messages.success(self.request, '✅ Votre mot de passe a été réinitialisé avec succès !')
        return super().form_valid(form)

    def get_success_url(self):
        return '/login/'