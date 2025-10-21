from django.db import models

class GoogleSheet(models.Model):
    title = models.CharField(max_length=255)
    sheet_url = models.URLField()

    def __str__(self):
        return self.title
    



