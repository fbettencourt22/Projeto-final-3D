from django.urls import path

from .views import (
    calculator_view,
    dashboard_view,
    inventory_add_piece_view,
    inventory_filament_edit_view,
    inventory_filament_delete_view,
    inventory_item_edit_view,
    inventory_item_delete_view,
    inventory_view,
    logout_view,
    piece_delete_view,
    piece_edit_view,
    piece_export_view,
    piece_import_view,
    pieces_list_view,
)

urlpatterns = [
    path("", dashboard_view, name="dashboard"),
    path("inventory/", inventory_view, name="inventory"),
    path("inventory/add/<int:pk>/", inventory_add_piece_view, name="inventory_add_piece"),
    path("inventory/filaments/<int:pk>/editar/", inventory_filament_edit_view, name="inventory_filament_edit"),
    path("inventory/filaments/<int:pk>/apagar/", inventory_filament_delete_view, name="inventory_filament_delete"),
    path("inventory/pecas/<int:pk>/editar/", inventory_item_edit_view, name="inventory_item_edit"),
    path("inventory/pecas/<int:pk>/apagar/", inventory_item_delete_view, name="inventory_item_delete"),
    path("logout/", logout_view, name="logout"),
    path("calculator/", calculator_view, name="calculator"),
    path("pieces/", pieces_list_view, name="pieces_list"),
    path("pieces/exportar/", piece_export_view, name="piece_export"),
    path("pieces/importar/", piece_import_view, name="piece_import"),
    path("pieces/<int:pk>/editar/", piece_edit_view, name="piece_edit"),
    path("pieces/<int:pk>/apagar/", piece_delete_view, name="piece_delete"),
]
