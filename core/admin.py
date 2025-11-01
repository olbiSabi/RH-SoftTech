from django.contrib import admin
from .models import ZDLOG


@admin.register(ZDLOG)
class ZDLOGAdmin(admin.ModelAdmin):
    list_display = (
    'DATE_MODIFICATION', 'TABLE_NAME', 'RECORD_ID', 'TYPE_MOUVEMENT', 'USER_NAME', 'get_description_short')
    list_filter = ('TABLE_NAME', 'TYPE_MOUVEMENT', 'DATE_MODIFICATION', 'USER')
    search_fields = ('TABLE_NAME', 'RECORD_ID', 'USER_NAME', 'DESCRIPTION')
    readonly_fields = ('TABLE_NAME', 'RECORD_ID', 'TYPE_MOUVEMENT', 'DATE_MODIFICATION',
                       'USER', 'USER_NAME', 'ANCIENNE_VALEUR', 'NOUVELLE_VALEUR',
                       'DESCRIPTION', 'IP_ADDRESS')
    ordering = ('-DATE_MODIFICATION',)
    date_hierarchy = 'DATE_MODIFICATION'

    def get_description_short(self, obj):
        if len(obj.DESCRIPTION) > 50:
            return obj.DESCRIPTION[:50] + '...'
        return obj.DESCRIPTION

    get_description_short.short_description = 'Description'

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser

    def has_change_permission(self, request, obj=None):
        return False