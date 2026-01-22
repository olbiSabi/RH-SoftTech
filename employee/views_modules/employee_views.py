# employee/views_modules/employee_views.py
"""
Vues CRUD pour les employés (ZY00).
"""
from django.db.models import Q
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.urls import reverse, reverse_lazy
from django.http import Http404
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages

from employee.decorators import DRHOrAdminRequiredMixin
from employee.models import ZY00
from employee.forms import ZY00Form
from employee.utils import get_redirect_url_with_tab


class EmployeListView(LoginRequiredMixin, DRHOrAdminRequiredMixin, ListView):
    """Liste de tous les employés"""
    login_url = 'login'
    redirect_field_name = 'next'
    model = ZY00
    template_name = 'employee/employees-list.html'
    context_object_name = 'employes'
    paginate_by = 20

    def get_queryset(self):
        queryset = super().get_queryset()
        # Filtrer par type de dossier
        type_dossier = self.request.GET.get('type_dossier')
        if type_dossier:
            queryset = queryset.filter(type_dossier=type_dossier)

        # Recherche par nom ou matricule
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(nom__icontains=search) |
                Q(prenoms__icontains=search) |
                Q(matricule__icontains=search)
            )

        return queryset.order_by('-matricule')


class EmployeCreateView(LoginRequiredMixin, DRHOrAdminRequiredMixin, CreateView):
    """Créer un employé"""
    login_url = 'login'
    model = ZY00
    form_class = ZY00Form
    template_name = 'employes/employe_form.html'
    success_url = reverse_lazy('employee:liste_employes')

    def form_valid(self, form):
        messages.success(self.request, "Employé créé avec succès!")
        return super().form_valid(form)


class EmployeUpdateView(LoginRequiredMixin, DRHOrAdminRequiredMixin, UpdateView):
    """Modifier un employé"""
    login_url = 'login'
    model = ZY00
    form_class = ZY00Form
    template_name = 'employee/employe_form.html'
    slug_field = 'uuid'
    slug_url_kwarg = 'uuid'
    context_object_name = 'employe'

    def get_object(self, queryset=None):
        """Surcharge pour mieux gérer les erreurs"""
        try:
            return super().get_object(queryset)
        except ZY00.DoesNotExist:
            messages.error(self.request, "Employé non trouvé")
            raise Http404("Employé non trouvé")

    def get_success_url(self):
        messages.success(self.request, "Employé modifié avec succès!")
        base_url = reverse('employee:detail_employe', kwargs={'uuid': self.object.uuid})
        return get_redirect_url_with_tab(self.request, base_url)


class EmployeDeleteView(LoginRequiredMixin, DRHOrAdminRequiredMixin, DeleteView):
    """Supprimer un employé (suppression en cascade)"""
    login_url = 'login'
    model = ZY00
    template_name = 'employee/employe_confirm_delete.html'
    success_url = reverse_lazy('employee:liste_employes')
    slug_field = 'uuid'
    slug_url_kwarg = 'uuid'

    def get_object(self, queryset=None):
        if queryset is None:
            queryset = self.get_queryset()

        uuid = self.kwargs.get('uuid')
        if uuid is not None:
            queryset = queryset.filter(uuid=uuid)

        return get_object_or_404(queryset)

    def form_valid(self, form):
        """Surcharge de form_valid pour gérer la suppression du user"""
        employe = self.object

        try:
            # Sauvegarder les infos pour les messages
            employe_nom = f"{employe.nom} {employe.prenoms}"

            # Gestion de la suppression du user
            if employe.user:
                user = employe.user
                username = user.username

                # Dissocier d'abord
                employe.user = None
                employe.save(update_fields=['user'])

                # Supprimer le user
                user.delete()
                messages.info(self.request, f"Compte utilisateur '{username}' supprimé.")

            # Maintenant supprimer l'employé via la méthode parent
            response = super().form_valid(form)
            messages.success(self.request, f"Employé {employe_nom} supprimé avec succès!")

            return response

        except Exception as e:
            messages.error(self.request, f"Erreur lors de la suppression : {str(e)}")
            return redirect('employee:detail_employe', uuid=employe.uuid)
