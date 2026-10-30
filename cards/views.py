from django.conf import settings
from django.contrib.admin.views.decorators import staff_member_required
from django.core.exceptions import PermissionDenied
from django.http import FileResponse, Http404, HttpResponse
from django.shortcuts import get_object_or_404, render
from django.views.decorators.http import require_GET
from .models import EmployeeCard
from .services.qr import make_qr
from .services.vcard import build_vcard


def not_found(request, exception=None):
    return render(request, 'cards/unavailable.html', status=404)


@require_GET
def home(request):
    return render(request, 'cards/home.html')


@require_GET
def robots(request):
    return HttpResponse('User-agent: *\nDisallow: /\n', content_type='text/plain')


def render_card(request, employee, preview=False):
    return render(request, 'cards/card.html', {
        'card': employee, 'company': settings.COMPANY_NAME,
        'company_website': settings.COMPANY_WEBSITE, 'preview': preview,
        'public_url': settings.PUBLIC_BASE_URL + employee.get_absolute_url(),
    })


@require_GET
def card(request, pk):
    employee = EmployeeCard.objects.filter(pk=pk, is_active=True).first()
    if not employee:
        return not_found(request)
    return render_card(request, employee)


def photo_response(employee):
    if not employee.photo:
        raise Http404
    try:
        stream = employee.photo.open('rb')
    except (OSError, ValueError):
        raise Http404
    return FileResponse(stream, content_type='image/jpeg')


@require_GET
def photo(request, pk):
    return photo_response(get_object_or_404(EmployeeCard, pk=pk, is_active=True))


def check_preview_permission(request):
    if not request.user.has_perm('cards.view_employeecard'):
        raise PermissionDenied


@staff_member_required(login_url='/manage/login/')
@require_GET
def preview(request, pk):
    check_preview_permission(request)
    return render_card(request, get_object_or_404(EmployeeCard, pk=pk), preview=True)


@staff_member_required(login_url='/manage/login/')
@require_GET
def preview_photo(request, pk):
    check_preview_permission(request)
    return photo_response(get_object_or_404(EmployeeCard, pk=pk))


@require_GET
def contact_file(request, pk):
    employee = get_object_or_404(EmployeeCard, pk=pk, is_active=True)
    response = HttpResponse(build_vcard(employee), content_type='text/vcard; charset=utf-8')
    response['Content-Disposition'] = f'attachment; filename="contact-{employee.pk}.vcf"'
    return response


@require_GET
def qr_file(request, pk, format):
    employee = get_object_or_404(EmployeeCard, pk=pk, is_active=True)
    response = HttpResponse(make_qr(employee, format), content_type='image/png' if format == 'png' else 'image/svg+xml')
    disposition = 'inline' if request.GET.get('inline') == '1' else 'attachment'
    response['Content-Disposition'] = f'{disposition}; filename="kmz-{employee.pk}.{format}"'
    return response
