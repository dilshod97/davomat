from django.urls import path

from .stats_views import DocumentStatsListView, DocumentStatsView
from .views import (
    DocumentReadView,
    MyDocumentsView,
    QuizView,
    SubmitQuizView,
)

urlpatterns = [
    # Xodim (WebApp)
    path("my/", MyDocumentsView.as_view(), name="knowledge-my"),
    path("documents/<int:document_id>/", DocumentReadView.as_view(), name="knowledge-read"),
    path("documents/<int:document_id>/quiz/", QuizView.as_view(), name="knowledge-quiz"),
    path("documents/<int:document_id>/submit/", SubmitQuizView.as_view(), name="knowledge-submit"),

    # Mas'ul xodim (statistika)
    path("stats/", DocumentStatsListView.as_view(), name="knowledge-stats-list"),
    path("stats/<int:document_id>/", DocumentStatsView.as_view(), name="knowledge-stats"),
]
