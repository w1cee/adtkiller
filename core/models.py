from django.db import models
import re


class Aid(models.Model):
    aid = models.PositiveIntegerField(unique=True, db_index=True)
    name = models.CharField(max_length=255, blank=True, null=True)

    parser_template = models.TextField(
        help_text="Worker template (with [replace_me])"
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def get_required_params(self):
        return re.findall(r"([a-zA-Z0-9_]+)=\[replace_me\]", self.parser_template)

    def __str__(self):
        return f"Aid {self.aid}"


class Campaign(models.Model):
    aid = models.OneToOneField(
        Aid, on_delete=models.CASCADE, related_name="campaign"
    )
    campaign_name = models.CharField(max_length=255)

    url_template = models.TextField(
        help_text="Template with {placeholders}"
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Campaign {self.campaign_name} for Aid {self.aid.aid}"
