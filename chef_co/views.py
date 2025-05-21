from django.shortcuts import render
from rest_framework import viewsets, permissions, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
import json
from django.conf import settings
import openai
import os
from decimal import Decimal
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from .models import Menu, Course, MenuItem, QuantityReference, PartyOrder, PredictionResult
from .serializers import (
    MenuSerializer, CourseSerializer, MenuItemSerializer,
    QuantityReferenceSerializer, PartyOrderSerializer, PredictionResultSerializer
)
from .apiutils import tags, prediction_name_schema


class IsAdminOrReadOnly(permissions.BasePermission):
    """
    Custom permission to only allow admins to create/edit objects.
    """
    def has_permission(self, request, view):
        # Read permissions are allowed to any request
        if request.method in permissions.SAFE_METHODS:
            return True
        # Write permissions are only allowed to admin users
        return request.user and request.user.is_staff


class MenuViewSet(viewsets.ModelViewSet):
    """
    API endpoints for managing menus.
    """
    queryset = Menu.objects.all()
    serializer_class = MenuSerializer
    permission_classes = [permissions.IsAuthenticated, IsAdminOrReadOnly]
    
    @swagger_auto_schema(
        operation_summary="Create a new menu",
        operation_description="Creates a new menu with the current user as creator.",
        tags=[tags['menus']]
    )
    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)


class CourseViewSet(viewsets.ModelViewSet):
    """
    API endpoints for managing courses within menus.
    """
    queryset = Course.objects.all()
    serializer_class = CourseSerializer
    permission_classes = [permissions.IsAuthenticated, IsAdminOrReadOnly]
    
    @swagger_auto_schema(
        operation_summary="List all courses",
        operation_description="List all courses across all menus.",
        tags=[tags['courses']]
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)
    
    @swagger_auto_schema(
        operation_summary="Create a new course",
        operation_description="Create a new course within a menu.",
        tags=[tags['courses']]
    )
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)


class MenuItemViewSet(viewsets.ModelViewSet):
    """
    API endpoints for managing menu items within courses.
    """
    queryset = MenuItem.objects.all()
    serializer_class = MenuItemSerializer
    permission_classes = [permissions.IsAuthenticated, IsAdminOrReadOnly]
    
    @swagger_auto_schema(
        operation_summary="List all menu items",
        operation_description="List all menu items across all courses.",
        tags=[tags['menu_items']]
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)


class QuantityReferenceViewSet(viewsets.ModelViewSet):
    """
    API endpoints for managing quantity references for menu items.
    """
    queryset = QuantityReference.objects.all()
    serializer_class = QuantityReferenceSerializer
    permission_classes = [permissions.IsAuthenticated, IsAdminOrReadOnly]
    
    @swagger_auto_schema(
        operation_summary="List all quantity references",
        operation_description="List all quantity references for menu items.",
        tags=[tags['quantity_references']]
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)


class PartyOrderViewSet(viewsets.ModelViewSet):
    """
    API endpoints for managing party orders.
    """
    queryset = PartyOrder.objects.all()
    serializer_class = PartyOrderSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    @swagger_auto_schema(
        operation_summary="List party orders",
        operation_description="List all party orders for the current user (or all users for admins).",
        tags=[tags['party_orders']]
    )
    def get_queryset(self):
        # Regular users can only see their own orders
        if not self.request.user.is_staff:
            return PartyOrder.objects.filter(user=self.request.user)
        # Admins can see all orders
        return PartyOrder.objects.all()
    
    @swagger_auto_schema(
        operation_summary="Generate quantity predictions",
        operation_description="Use AI to predict quantities for a party order based on reference data and save the result.",
        request_body=prediction_name_schema,
        tags=[tags['predictions']]
    )
    @action(detail=True, methods=['post'])
    def predict_quantities(self, request, pk=None):
        """
        Use OpenAI to predict quantities for the menu items based on party size and save the result
        """
        party_order = self.get_object()
        menu_id = party_order.menu.id
        party_size = party_order.party_size
        
        # Get custom name or use party order as default
        prediction_name = request.data.get('name', '').strip()
        if not prediction_name:
            prediction_name = str(party_order)  # Use the party order's string representation
        
        # Get all reference quantities from the database
        menu = Menu.objects.prefetch_related(
            'courses__menu_items__quantity_references'
        ).get(id=menu_id)
        
        # Create a simpler, more explicit reference structure
        reference_data = {"party_size": party_size, "courses": []}
        
        for course in menu.courses.all():
            course_data = {
                "course_name": course.name,
                "items": []
            }
            
            for item in course.menu_items.all():
                item_data = {
                    "item_name": item.name,
                    "reference_quantities": []
                }
                
                # Collect references in a simpler format
                references = list(item.quantity_references.all().order_by('party_size'))
                for ref in references:
                    item_data["reference_quantities"].append({
                        "party_size": ref.party_size,
                        "quantity": float(ref.quantity_value),
                        "unit": ref.unit
                    })
                
                course_data["items"].append(item_data)
            
            reference_data["courses"].append(course_data)
        
        # Create a very explicit prompt with clear examples
        prompt = f"""
        Your task is to predict food quantities needed for a party of {party_size} people.
        
        The reference data contains known quantities for standard party sizes (typically 50, 100, 250, 500 people).
        
        The relationship between party size and quantity is typically linear. For example:
        - If 50 people need 2KG and 100 people need 4KG, then 75 people would need 3KG.
        - If 50 people need 200 pieces and 100 people need 500 pieces, then 75 people would need 350 pieces.
        
        Here is the reference data:
        {reference_data}
        
        For each menu item, calculate the appropriate quantity for {party_size} people by using linear interpolation/extrapolation from the reference data.
        
        Return a JSON object with the following structure:
        {{
          "predictions": [
            {{
              "course_name": "COURSE_NAME",
              "items": [
                {{ 
                  "item_name": "ITEM_NAME", 
                  "quantity_value": NUMERIC_VALUE, 
                  "unit": "ORIGINAL_UNIT" 
                }},
                ...
              ]
            }},
            ...
          ]
        }}
        
        Important:
        1. Preserve the original units exactly as they appear in the reference data (KG, PC, etc.)
        2. Include ALL courses and ALL items from the reference data in your prediction
        3. Calculate each value by proper linear scaling based on party size
        """
        
        try:
            # Initialize OpenAI client
            client = openai.OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
            
            # Call OpenAI API with strict parameters
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "system", 
                        "content": "You are a calculator for food quantities. Your only job is to perform linear interpolation based on party sizes and return correctly formatted JSON. Maintain the original units."
                    },
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"},
                temperature=0.0,  # Zero temperature for deterministic outputs
                max_tokens=2000
            )
            
            # Get the response content
            content = response.choices[0].message.content
            
            # Parse JSON to ensure it's valid
            result_data = json.loads(content)
            
            # Always save the prediction
            prediction = PredictionResult.objects.create(
                party_order=party_order,
                result_data=result_data,
                name=prediction_name
            )
            
            # Return both the prediction and its metadata
            return Response({
                "prediction_id": prediction.id,
                "name": prediction.name,
                "created_at": prediction.created_at,
                "data": result_data
            }, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            return Response(
                {"error": f"Failed to predict quantities: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class PredictedQuantitiesViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoints for retrieving past predictions.
    """
    serializer_class = PredictionResultSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'party_order__menu__name']
    ordering_fields = ['created_at', 'name']
    
    @swagger_auto_schema(
        operation_summary="List all past predictions",
        operation_description="List all saved predictions for the current user (or all users for admins).",
        tags=[tags['predictions']]
    )
    def get_queryset(self):
        # Regular users can only see their own predictions
        if not self.request.user.is_staff:
            return PredictionResult.objects.filter(party_order__user=self.request.user)
        # Admins can see all predictions
        return PredictionResult.objects.all()
    
    @swagger_auto_schema(
        operation_summary="List all past predictions",
        operation_description="Get a list of all past quantity predictions.",
        tags=[tags['predictions']]
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)
    
    @swagger_auto_schema(
        operation_summary="Get a specific prediction",
        operation_description="Retrieve details for a specific past prediction.",
        tags=[tags['predictions']]
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)
