from django.contrib.auth import views as auth_views
from django.urls import path

from web.results import views

urlpatterns = [
    path("health/", views.health, name="health"),
    path("login/", auth_views.LoginView.as_view(), name="login"),
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),
    path("", views.overview, name="overview"),
    path("runs/", views.runs, name="runs"),
    path("new/", views.new_run, name="new_run"),
    path("new/composition-total/", views.composition_total, name="composition_total"),
    path("run/<str:run_id>/", views.run_detail, name="run"),
    path("run/<str:run_id>/country/<str:country>/", views.country, name="country"),
    path("run/<str:run_id>/sweden/", views.sweden, name="sweden"),
    path("run/<str:run_id>/thresholds/", views.thresholds, name="thresholds"),
    path("run/<str:run_id>/explain/", views.explain, name="explain"),
    path("run/<str:run_id>/csv/<str:table>.csv", views.csv, name="csv"),
    path("about/", views.about, name="about"),
    path("glossary/", views.glossary, name="glossary"),
    path("data/", views.data, name="data"),
    path("reviewers/", views.reviewers, name="reviewers"),
    path("reviewers/feedback/", views.feedback_list, name="feedback_list"),
]
