from rest_framework import serializers
from .models import Menu, Course, MenuItem, QuantityReference, PartyOrder
from django.contrib.auth.models import User


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'is_staff']


class QuantityReferenceSerializer(serializers.ModelSerializer):
    class Meta:
        model = QuantityReference
        fields = ['id', 'party_size', 'quantity_value', 'unit']


class MenuItemSerializer(serializers.ModelSerializer):
    quantity_references = QuantityReferenceSerializer(many=True, read_only=True)
    
    class Meta:
        model = MenuItem
        fields = ['id', 'name', 'quantity_references']


class CourseSerializer(serializers.ModelSerializer):
    menu_items = MenuItemSerializer(many=True, read_only=True)
    
    class Meta:
        model = Course
        fields = ['id', 'name', 'order', 'menu_items']


class MenuSerializer(serializers.ModelSerializer):
    courses = CourseSerializer(many=True, read_only=True)
    created_by = UserSerializer(read_only=True)
    
    class Meta:
        model = Menu
        fields = ['id', 'name', 'description', 'created_by', 'created_at', 'courses']


class PartyOrderSerializer(serializers.ModelSerializer):
    menu = MenuSerializer(read_only=True)
    menu_id = serializers.PrimaryKeyRelatedField(
        queryset=Menu.objects.all(), 
        write_only=True, 
        source='menu'
    )
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = PartyOrder
        fields = ['id', 'user', 'menu', 'menu_id', 'party_size', 'created_at']
        
    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data) 