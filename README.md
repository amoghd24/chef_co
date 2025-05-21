# Chef Co - Menu Planner

A Django application for chefs to predict ingredient quantities for different party sizes.

## Overview

The Chef Co app helps chefs determine how much of each ingredient is needed when preparing food for various party sizes. Using reference data for standard party sizes (50, 100, 250, 500 people), the app can predict quantities for any arbitrary party size using OpenAI's predictive capabilities.

## Features

- Menu management system with courses and menu items
- Quantity reference database for standard party sizes
- AI-powered predictions for arbitrary party sizes
- RESTful API for all functionality
- User/admin role separation

## Tech Stack

- Django 5.1
- Django REST Framework
- SQLite database
- OpenAI API for predictions

## Installation

1. Clone the repository
2. Install requirements: `pip install django djangorestframework openai python-dotenv`
3. Apply migrations: `python manage.py migrate`
4. Run the server: `python manage.py runserver`

## API Endpoints

- `/api/menus/` - Manage menu types
- `/api/courses/` - Manage menu sections
- `/api/menu-items/` - Manage food items
- `/api/quantity-references/` - Reference quantities for party sizes
- `/api/party-orders/` - Create orders with party sizes
- `/api/party-orders/{id}/predict_quantities/` - Get AI predictions for a party size

## Admin Access

The admin interface is available at `/admin/` with these credentials:

- Username: admin
- Password: password

## Environment Variables

Create a `.env` file with your OpenAI API key:

```
OPENAI_API_KEY=your_api_key_here
``` 