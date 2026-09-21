from django.urls import path

from flights import views

urlpatterns = [
    path("search/", views.SearchView.as_view()),
    path("airports/", views.AirportsView.as_view()),
    path("health/", views.HealthView.as_view()),
]
