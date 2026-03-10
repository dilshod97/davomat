from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from tasks.api.web_views import SummaryReportView, ReportView, LocationDetail

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/davomat/', include('tasks.api.urls')),
    path('api/account/', include('account.api.urls')),
    path('att/summary', SummaryReportView.as_view(), name='summary'),
    path('att/generate/reports', ReportView.as_view(), name='report'),
    path('att/my/gps-snaps/', LocationDetail.as_view(), name='report'),
]
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
