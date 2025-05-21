from django.shortcuts import render
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.conf import settings
import openai
import os
from decimal import Decimal

from .models import Menu, Course, MenuItem, QuantityReference, PartyOrder
from .serializers import (
    MenuSerializer, CourseSerializer, MenuItemSerializer,
    QuantityReferenceSerializer, PartyOrderSerializer
)


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
    queryset = Menu.objects.all()
    serializer_class = MenuSerializer
    permission_classes = [permissions.IsAuthenticated, IsAdminOrReadOnly]
    
    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)


class CourseViewSet(viewsets.ModelViewSet):
    queryset = Course.objects.all()
    serializer_class = CourseSerializer
    permission_classes = [permissions.IsAuthenticated, IsAdminOrReadOnly]


class MenuItemViewSet(viewsets.ModelViewSet):
    queryset = MenuItem.objects.all()
    serializer_class = MenuItemSerializer
    permission_classes = [permissions.IsAuthenticated, IsAdminOrReadOnly]


class QuantityReferenceViewSet(viewsets.ModelViewSet):
    queryset = QuantityReference.objects.all()
    serializer_class = QuantityReferenceSerializer
    permission_classes = [permissions.IsAuthenticated, IsAdminOrReadOnly]


class PartyOrderViewSet(viewsets.ModelViewSet):
    queryset = PartyOrder.objects.all()
    serializer_class = PartyOrderSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        # Regular users can only see their own orders
        if not self.request.user.is_staff:
            return PartyOrder.objects.filter(user=self.request.user)
        # Admins can see all orders
        return PartyOrder.objects.all()
    
    @action(detail=True, methods=['get'])
    def predict_quantities(self, request, pk=None):
        """
        Use OpenAI to predict quantities for the menu items based on party size
        """
        party_order = self.get_object()
        menu_id = party_order.menu.id
        party_size = party_order.party_size
        
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
            
            # Return the response
            content = response.choices[0].message.content
            return Response(content, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response(
                {"error": f"Failed to predict quantities: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
