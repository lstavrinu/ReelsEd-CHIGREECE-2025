from django.contrib.auth.models import AbstractUser
from django.db import models
from django.contrib.auth import get_user_model
from django.db.models import Avg, Count


class CustomUser(AbstractUser):
    ROLE_CHOICES = (
        ('Student', 'Student'),
        ('Instructor', 'Instructor'),
    )
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='Student')
    allowed_videos = models.ManyToManyField("Video", related_name="allowed_students", blank=True)

    # Keep these to avoid clashes with Django auth
    groups = models.ManyToManyField(
        'auth.Group',
        related_name='customuser_groups',
        blank=True,
        help_text='The groups this user belongs to.',
        verbose_name='groups',
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        related_name='customuser_user_permissions',
        blank=True,
        help_text='Specific permissions for this user.',
        verbose_name='user permissions',
    )

User = get_user_model()


class Video(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    video_id = models.CharField(max_length=100, unique=True)
    title = models.CharField(max_length=255)
    url = models.URLField()
    file_path = models.FileField(upload_to='videos/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    duration = models.FloatField(null=True, blank=True)
    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("downloading", "Downloading Video"),
        ("extracting", "Extracting Key Moments"),
        ("generating", "Generating Reels"),
        ("completed", "Complete"),
        ("error", "Error"),
    ]

    status = models.CharField(max_length=100, choices=STATUS_CHOICES, default="pending")

    def __str__(self):
        return self.title


class Reel(models.Model):
    video = models.ForeignKey(Video, on_delete=models.CASCADE, related_name='reels')
    start_time = models.FloatField()
    end_time = models.FloatField()
    label = models.CharField(max_length=100)
    summary = models.TextField(blank=True, null=True)
    file_path = models.FileField(upload_to='reels/')
    created_at = models.DateTimeField(auto_now_add=True)
    duration = models.FloatField(null=True, blank=True)
    average_rating = models.FloatField(default=0.0)


class ReelRating(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    reel = models.ForeignKey(Reel, on_delete=models.CASCADE, related_name="ratings")
    rating = models.IntegerField(default=0)

    def update_average_rating(self):
        """Recalculate and store average rating."""
        ratings = self.ratings.aggregate(avg_rating=Avg("rating"), total=Count("rating"))
        self.average_rating = ratings["avg_rating"] or 0
        self.save(update_fields=["average_rating"])

    class Meta:
        unique_together = ("user", "reel")

    def __str__(self):
        return f"Reel for {self.video.title} ({self.start_time}-{self.end_time})"
