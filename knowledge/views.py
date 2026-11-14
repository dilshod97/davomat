from django.shortcuts import render


def read_page(request, document_id):
    """Hujjatni o'qish WebApp sahifasi."""
    return render(request, "knowledge/read.html", {
        "document_id": document_id,
        "token": request.GET.get("token", ""),
    })


def quiz_page(request, document_id):
    """Test topshirish WebApp sahifasi."""
    return render(request, "knowledge/quiz.html", {
        "document_id": document_id,
        "token": request.GET.get("token", ""),
    })
