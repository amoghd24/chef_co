from django.db import models
from django.contrib.auth.models import User


class Menu(models.Model):
    """
    Represents a menu type (e.g., "Basic Menu 1", "Premium Menu", etc.)
    """
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.name


class Course(models.Model):
    """
    Represents a section of a menu (e.g., "Appetizers", "Main Course", etc.)
    """
    name = models.CharField(max_length=100)
    menu = models.ForeignKey(Menu, related_name='courses', on_delete=models.CASCADE)
    order = models.PositiveIntegerField(default=0)  # To maintain course order
    
    def __str__(self):
        return f"{self.menu.name} - {self.name}"
    
    class Meta:
        ordering = ['order']


class MenuItem(models.Model):
    """
    Represents a specific food item within a course
    """
    name = models.CharField(max_length=100)
    course = models.ForeignKey(Course, related_name='menu_items', on_delete=models.CASCADE)
    
    def __str__(self):
        return self.name


class QuantityReference(models.Model):
    """
    Stores reference quantities for menu items based on party size
    This data will be used by OpenAI for predictions
    """
    menu_item = models.ForeignKey(MenuItem, related_name='quantity_references', on_delete=models.CASCADE)
    party_size = models.PositiveIntegerField()  # e.g., 50, 100, 250, 500
    quantity_value = models.DecimalField(max_digits=10, decimal_places=2)  # numeric value (e.g., 2.0)
    unit = models.CharField(max_length=20)  # e.g., "KG", "PC"
    
    def __str__(self):
        return f"{self.menu_item.name} - {self.quantity_value} {self.unit} for {self.party_size} people"
    
    class Meta:
        unique_together = ['menu_item', 'party_size']


class PartyOrder(models.Model):
    """
    Represents a user's request for a menu for a specific party size
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    menu = models.ForeignKey(Menu, on_delete=models.CASCADE)
    party_size = models.PositiveIntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.menu.name} for {self.party_size} people"


class PredictionResult(models.Model):
    """
    Stores saved predictions for future reference
    """
    party_order = models.ForeignKey(PartyOrder, related_name='predictions', on_delete=models.CASCADE)
    result_data = models.JSONField()  # Stores the complete prediction JSON
    created_at = models.DateTimeField(auto_now_add=True)
    name = models.CharField(max_length=255, blank=True)  # Optional name for the prediction
    
    def save(self, *args, **kwargs):
        # Replace empty or "string" names with party order string representation
        if not self.name or self.name == "string":
            self.name = str(self.party_order)
        super().save(*args, **kwargs)
    
    def __str__(self):
        if self.name:
            return self.name
        return f"Prediction for {self.party_order} - {self.created_at.strftime('%Y-%m-%d %H:%M')}"
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = "Past order prediction"
        verbose_name_plural = "Past order predictions"
