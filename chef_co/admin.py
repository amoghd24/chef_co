from django.contrib import admin
from .models import Menu, Course, MenuItem, QuantityReference, PartyOrder
from django import forms
from django.shortcuts import render, redirect
from django.urls import path
import csv
from io import TextIOWrapper
from decimal import Decimal
import re


class CSVUploadForm(forms.Form):
    csv_file = forms.FileField()


class CourseInline(admin.TabularInline):
    model = Course
    extra = 1


class MenuItemInline(admin.TabularInline):
    model = MenuItem
    extra = 1


class QuantityReferenceInline(admin.TabularInline):
    model = QuantityReference
    extra = 1


@admin.register(Menu)
class MenuAdmin(admin.ModelAdmin):
    list_display = ('name', 'created_by', 'created_at')
    search_fields = ('name', 'description')
    inlines = [CourseInline]


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ('name', 'menu', 'order')
    list_filter = ('menu',)
    search_fields = ('name',)
    inlines = [MenuItemInline]


@admin.register(MenuItem)
class MenuItemAdmin(admin.ModelAdmin):
    list_display = ('name', 'course')
    list_filter = ('course__menu', 'course')
    search_fields = ('name',)
    inlines = [QuantityReferenceInline]


@admin.register(QuantityReference)
class QuantityReferenceAdmin(admin.ModelAdmin):
    list_display = ('menu_item', 'party_size', 'quantity_value', 'unit')
    list_filter = ('menu_item__course__menu', 'menu_item__course', 'party_size')
    search_fields = ('menu_item__name',)
    
    def get_urls(self):
        urls = super().get_urls()
        new_urls = [
            path('upload-csv/', self.upload_csv, name='upload_csv'),
        ]
        return new_urls + urls
    
    def upload_csv(self, request):
        if request.method == 'POST':
            form = CSVUploadForm(request.POST, request.FILES)
            if form.is_valid():
                csv_file = request.FILES['csv_file']
                decoded_file = TextIOWrapper(csv_file.file, encoding='utf-8')
                reader = csv.reader(decoded_file)
                data = list(reader)
                
                # First row is header, find indexes for party sizes
                header = data[0]
                party_sizes = []
                party_size_indexes = []
                
                for i, col in enumerate(header):
                    if col.strip().endswith('PAX'):
                        try:
                            # Extract the number from strings like "50 PAX"
                            size = int(col.strip().split()[0])
                            party_sizes.append(size)
                            party_size_indexes.append(i)
                        except (ValueError, IndexError):
                            pass
                
                # Process data
                current_course = None
                success_count = 0
                error_count = 0
                
                for row in data[1:]:  # Skip header
                    if not row or all(not cell.strip() for cell in row):
                        continue  # Skip empty rows
                    
                    # Check if this is a course header
                    if row[0].strip().upper() in ['APPETIZERS', 'MAIN COURSE', 'BREADS', 'DESSERTS']:
                        current_course_name = row[0].strip()
                        try:
                            # Find the course by name - assumes the menu is already created
                            # Here we find the first menu and use it - in production you'd want to specify which menu
                            menu = Menu.objects.first()
                            if not menu:
                                self.message_user(request, "No menus found. Please create a menu first.", level='ERROR')
                                return redirect('..')
                            
                            current_course = Course.objects.filter(menu=menu, name=current_course_name).first()
                            if not current_course:
                                self.message_user(
                                    request, 
                                    f"Course '{current_course_name}' not found for the selected menu.", 
                                    level='ERROR'
                                )
                        except Exception as e:
                            self.message_user(request, f"Error finding course: {str(e)}", level='ERROR')
                        continue
                    
                    # Process menu item
                    if current_course and row[0].strip() and row[0].strip().upper() != 'MENU':
                        item_name = row[0].strip()
                        try:
                            # Find or create the menu item
                            menu_item, _ = MenuItem.objects.get_or_create(
                                course=current_course, 
                                name=item_name
                            )
                            
                            # Process quantities for each party size
                            for i, party_size in enumerate(party_sizes):
                                col_index = party_size_indexes[i]
                                
                                if col_index < len(row) and row[col_index].strip():
                                    quantity_str = row[col_index].strip()
                                    
                                    # Parse values like "200 PC(1PC=50GM)" or "4KG"
                                    match = re.match(r'(\d+)\s*([A-Za-z]+)(?:\(.*\))?', quantity_str)
                                    if match:
                                        value = Decimal(match.group(1))
                                        unit = match.group(2)
                                        
                                        # Create or update quantity reference
                                        QuantityReference.objects.update_or_create(
                                            menu_item=menu_item,
                                            party_size=party_size,
                                            defaults={
                                                'quantity_value': value,
                                                'unit': unit
                                            }
                                        )
                                        success_count += 1
                                    else:
                                        error_count += 1
                        except Exception as e:
                            self.message_user(
                                request, 
                                f"Error processing row for '{item_name}': {str(e)}", 
                                level='ERROR'
                            )
                            error_count += 1
                
                self.message_user(
                    request, 
                    f"Successfully imported {success_count} quantity references with {error_count} errors."
                )
                return redirect('..')
        else:
            form = CSVUploadForm()
        
        context = {
            'form': form,
            'title': 'Upload Quantity References CSV',
            'site_title': 'Chef Co Admin',
            'site_header': 'Chef Co Administration',
        }
        return render(request, 'admin/csv_upload.html', context)
    
    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        extra_context['csv_upload_form'] = CSVUploadForm()
        return super().changelist_view(request, extra_context=extra_context)


@admin.register(PartyOrder)
class PartyOrderAdmin(admin.ModelAdmin):
    list_display = ('menu', 'user', 'party_size', 'created_at')
    list_filter = ('menu', 'user', 'created_at')
    search_fields = ('menu__name', 'user__username')
