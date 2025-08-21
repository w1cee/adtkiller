from django.contrib import admin
from .models import Aid, Campaign


@admin.register(Aid)
class AidAdmin(admin.ModelAdmin):
    list_display = ("aid", "name", "created_at")
    search_fields = ("aid", "name")
    readonly_fields = ("created_at",)


@admin.register(Campaign)
class CampaignAdmin(admin.ModelAdmin):
    list_display = ("campaign_name", "aid", "created_at")
    search_fields = ("campaign_name", "aid__aid")
    readonly_fields = ("created_at",)
