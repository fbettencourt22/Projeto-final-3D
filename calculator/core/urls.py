from django.urls import path

from .views import (
    calculator_view,
    logout_view,
    piece_delete_view,
    piece_edit_view,
    pieces_list_view,
)

urlpatterns = [
    path("logout/", logout_view, name="logout"),
    path("", calculator_view, name="calculator"),
    path("pieces/", pieces_list_view, name="pieces_list"),
    path("pieces/<int:pk>/editar/", piece_edit_view, name="piece_edit"),
    path("pieces/<int:pk>/apagar/", piece_delete_view, name="piece_delete"),
]
