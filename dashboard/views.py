from django.shortcuts import render


def dashboard_page(request):
    return render(request, "dashboard/dashboard.html")