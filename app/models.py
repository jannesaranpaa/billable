from django.db import models


class User(models.Model):
    username = models.CharField(max_length=100, unique=True)
    password_hash = models.CharField(max_length=255)
    is_admin = models.BooleanField(default=False)
    failed_attempts = models.IntegerField(default=0)


class Entry(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    start = models.DateTimeField()
    end = models.DateTimeField()
    comment = models.TextField()


class Audit(models.Model):
    timestamp = models.DateTimeField(auto_now_add=True)
    action = models.TextField()
    payload = models.TextField()
