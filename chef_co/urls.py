from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'menus', views.MenuViewSet)
router.register(r'courses', views.CourseViewSet)
router.register(r'menu-items', views.MenuItemViewSet)
router.register(r'quantity-references', views.QuantityReferenceViewSet)
router.register(r'party-orders', views.PartyOrderViewSet)

urlpatterns = [
    path('api/', include(router.urls)),
] 