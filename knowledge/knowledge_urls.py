from django.urls import path

from .views import quiz_page, read_page

urlpatterns = [
    path("read/<int:document_id>/", read_page, name="knowledge-read-page"),
    path("quiz/<int:document_id>/", quiz_page, name="knowledge-quiz-page"),
]
