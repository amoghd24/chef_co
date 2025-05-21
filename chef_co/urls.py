from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views
from django.views.generic import RedirectView

router = DefaultRouter()
router.register(r'menus', views.MenuViewSet)
router.register(r'courses', views.CourseViewSet)
router.register(r'menu-items', views.MenuItemViewSet)
router.register(r'quantity-references', views.QuantityReferenceViewSet)
router.register(r'party-orders', views.PartyOrderViewSet)
router.register(r'predicted_quantities', views.PredictedQuantitiesViewSet, basename='predicted_quantities')

urlpatterns = [
    # Redirect root to Swagger UI
    path('', RedirectView.as_view(url='/swagger/', permanent=False), name='home'),
    path('api/', include(router.urls)),
] 