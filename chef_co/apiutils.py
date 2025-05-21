"""
Utility functions and constants for API documentation
"""
from drf_yasg import openapi

# Common response schemas
token_response = openapi.Response(
    description="Returns an authentication token",
    schema=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'token': openapi.Schema(type=openapi.TYPE_STRING)
        }
    )
)

# Parameter schemas
party_size_param = openapi.Parameter(
    'party_size', 
    openapi.IN_QUERY,
    description="Size of the party for food quantity calculation",
    type=openapi.TYPE_INTEGER,
    required=True
)

save_prediction_param = openapi.Parameter(
    'save', 
    openapi.IN_QUERY,
    description="Whether to save the prediction (true/false)",
    type=openapi.TYPE_BOOLEAN,
    default=False
)

prediction_name_param = openapi.Parameter(
    'name', 
    openapi.IN_QUERY,
    description="Name for the saved prediction",
    type=openapi.TYPE_STRING
)

# Request body schemas
rename_prediction_schema = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    required=['name'],
    properties={
        'name': openapi.Schema(type=openapi.TYPE_STRING)
    }
)

prediction_name_schema = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    properties={
        'name': openapi.Schema(
            type=openapi.TYPE_STRING,
            description="Optional name for the prediction"
        )
    }
)

# Standard API tags
tags = {
    'auth': 'Authentication',
    'menus': 'Menus',
    'courses': 'Courses',
    'menu_items': 'Menu Items',
    'quantity_references': 'Quantity References',
    'party_orders': 'Party Orders',
    'predictions': 'Predictions',
} 