from django.urls import path

from . import views

urlpatterns = [
    path("login/", views.login_view, name="panel-login"),
    path("logout/", views.logout_view, name="panel-logout"),
    path("", views.dashboard, name="panel-dashboard"),
    path("documents/new/", views.document_new, name="panel-document-new"),
    path("documents/<int:document_id>/", views.document_detail, name="panel-document-detail"),
    path("documents/<int:document_id>/analyze/", views.action_analyze, name="panel-analyze"),
    path("documents/<int:document_id>/save/", views.save_document, name="panel-save"),
    path("documents/<int:document_id>/cover/", views.upload_cover, name="panel-cover"),
    path("documents/<int:document_id>/publish/", views.action_publish, name="panel-publish"),
    path("documents/<int:document_id>/stats/", views.document_stats, name="panel-stats"),
]
