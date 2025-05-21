from django.apps import AppConfig


class ChefCoConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'chef_co'
    verbose_name = 'Chef Co - Menu Planner'
    
    def ready(self):
        from django.db.models.signals import post_migrate
        from django.dispatch import receiver
        
        @receiver(post_migrate)
        def update_model_labels(sender, **kwargs):
            if sender.name == self.name:
                from django.apps import apps
                prediction_model = apps.get_model('chef_co', 'PredictionResult')
                prediction_model._meta.verbose_name = "Past order prediction"
                prediction_model._meta.verbose_name_plural = "Past order predictions"
