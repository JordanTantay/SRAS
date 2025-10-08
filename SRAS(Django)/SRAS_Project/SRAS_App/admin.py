from django.contrib import admin
from .models import Camera, Violation, Enforcer

admin.site.register(Camera)
admin.site.register(Violation)
admin.site.register(Enforcer)
