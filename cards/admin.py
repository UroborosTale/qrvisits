from django.contrib import admin
from django.conf import settings
from django.urls import reverse
from django.utils.html import format_html
from .forms import EmployeeCardForm
from .models import EmployeeCard

admin.site.site_header = 'КМЗ · Электронные визитки'
admin.site.site_title = 'КМЗ'
admin.site.index_title = 'Управление визитками сотрудников'
admin.site.site_url = None


@admin.register(EmployeeCard)
class EmployeeCardAdmin(admin.ModelAdmin):
    form = EmployeeCardForm
    list_display = ['full_name', 'job_title', 'department', 'is_active', 'updated_at', 'card_links']
    list_filter = ['is_active']
    search_fields = ['full_name', 'job_title', 'department', 'phone', 'mobile_phone', 'email']
    readonly_fields = ['id', 'created_at', 'updated_at', 'card_links', 'company_website']
    fieldsets = [
        ('Данные визитки', {'fields': ['photo', 'full_name', 'job_title', 'department',
            'phone', 'phone_extension', 'mobile_phone', 'company_website']}),
        ('Публикация', {'fields': ['is_active', 'card_links']}),
        ('Дополнительно', {'fields': ['email', 'description', 'messenger_url'], 'classes': ['collapse']}),
        ('Служебные данные', {'fields': ['id', 'created_at', 'updated_at'], 'classes': ['collapse']}),
    ]
    actions = ['disable_cards']

    @admin.display(description='Сайт КМЗ (общий для всех визиток)')
    def company_website(self, obj):
        return format_html('<a href="{}" target="_blank" rel="noopener noreferrer">{}</a>',
            settings.COMPANY_WEBSITE, settings.COMPANY_WEBSITE)

    def has_delete_permission(self, request, obj=None):
        return False

    @admin.action(description='Отключить выбранные визитки', permissions=['change'])
    def disable_cards(self, request, queryset):
        count = queryset.update(is_active=False)
        self.message_user(request, f'Отключено визиток: {count}')

    @admin.display(description='Просмотр и QR')
    def card_links(self, obj):
        if not obj or not obj.pk:
            return 'Сначала сохраните визитку.'
        preview = reverse('card-preview', args=[obj.pk])
        if not obj.is_active:
            return format_html('<a href="{}">Предпросмотр черновика</a>', preview)
        return format_html('<a href="{}">Предпросмотр</a> · <a href="{}">Открыть</a> · '
            '<a href="{}qr.png">QR PNG</a> · <a href="{}qr.svg">QR SVG</a>',
            preview, obj.get_absolute_url(), obj.get_absolute_url(), obj.get_absolute_url())
