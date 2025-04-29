from django.db import models

class Furits(models.Model):
    name = models.CharField(max_length=50)
    descrip = models.TextField()
    price = models.FloatField()
    quantity = models.IntegerField()
    cdate = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return [self.id, self.name, self.descrip]