import csv
import re
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from chef_co.models import Menu, Course, MenuItem, QuantityReference


class Command(BaseCommand):
    help = 'Import menu data from BANQUET FOOD TOP SHEET CSV file'
    
    def handle(self, *args, **kwargs):
        # Get or create an admin user if none exists
        try:
            admin_user = User.objects.get(username='admin')
        except User.DoesNotExist:
            self.stdout.write(self.style.ERROR('Admin user not found. Please create one first.'))
            return
        
        # Read the CSV file
        csv_file_path = 'BANQUET FOOD TOP SHEET - BASIC MENU 1.csv'
        
        try:
            with open(csv_file_path, 'r') as file:
                csv_reader = csv.reader(file)
                data = list(csv_reader)
                
                # Create the menu
                menu_name = "Basic Menu 1"
                menu, created = Menu.objects.get_or_create(
                    name=menu_name,
                    defaults={'created_by': admin_user, 'description': 'Standard banquet menu'}
                )
                if created:
                    self.stdout.write(self.style.SUCCESS(f'Created menu: {menu_name}'))
                else:
                    self.stdout.write(self.style.WARNING(f'Menu already exists: {menu_name}'))
                
                # Party sizes from the header
                party_sizes = [50, 100, 250, 500]
                
                # Parse the CSV data
                current_course = None
                course_order = 0
                
                for row in data:
                    # Skip empty rows
                    if not row or all(cell.strip() == '' for cell in row):
                        continue
                    
                    # Check if this is a course header
                    if row[0].strip().upper() in ['APPETIZERS', 'MAIN COURSE', 'BREADS', 'DESSERTS']:
                        course_name = row[0].strip()
                        course_order += 1
                        current_course, created = Course.objects.get_or_create(
                            menu=menu,
                            name=course_name,
                            defaults={'order': course_order}
                        )
                        if created:
                            self.stdout.write(self.style.SUCCESS(f'Created course: {course_name}'))
                        else:
                            self.stdout.write(self.style.WARNING(f'Course already exists: {course_name}'))
                        continue
                    
                    # Skip header row
                    if row[0].strip() == 'MENU':
                        continue
                    
                    # Process menu item if we have a current course
                    if current_course and row[0].strip():
                        item_name = row[0].strip()
                        menu_item, created = MenuItem.objects.get_or_create(
                            course=current_course,
                            name=item_name
                        )
                        if created:
                            self.stdout.write(self.style.SUCCESS(f'Created menu item: {item_name}'))
                        else:
                            self.stdout.write(self.style.WARNING(f'Menu item already exists: {item_name}'))
                        
                        # Process quantities for different party sizes
                        for i, party_size in enumerate(party_sizes):
                            # Column index for this party size (each party size has 2 columns)
                            col_index = (i * 2) + 1
                            
                            if col_index < len(row) and row[col_index].strip():
                                quantity_str = row[col_index].strip()
                                
                                # Parse the quantity (e.g., "2KG" -> value=2, unit="KG")
                                # Parse values like "200 PC(1PC=50GM)" or "4KG"
                                match = re.match(r'(\d+)\s*([A-Za-z]+)(?:\(.*\))?', quantity_str)
                                if match:
                                    value = Decimal(match.group(1))
                                    unit = match.group(2)
                                    
                                    # Create or update the quantity reference
                                    quantity_ref, created = QuantityReference.objects.update_or_create(
                                        menu_item=menu_item,
                                        party_size=party_size,
                                        defaults={
                                            'quantity_value': value,
                                            'unit': unit
                                        }
                                    )
                                    if created:
                                        self.stdout.write(
                                            self.style.SUCCESS(
                                                f'Created quantity reference: {menu_item.name} - {value} {unit} for {party_size} people'
                                            )
                                        )
                                    else:
                                        self.stdout.write(
                                            self.style.WARNING(
                                                f'Updated quantity reference: {menu_item.name} - {value} {unit} for {party_size} people'
                                            )
                                        )
                
                self.stdout.write(self.style.SUCCESS('Import complete!'))
        
        except FileNotFoundError:
            self.stdout.write(self.style.ERROR(f'CSV file not found: {csv_file_path}'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error importing data: {str(e)}')) 