from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    full_name = models.CharField(max_length=50)  
    bio = models.TextField()
    resume = models.FileField(upload_to="user/resumes/")
    linkedin_url = models.URLField()
    github_url = models.URLField()
    portfolio_url = models.URLField()
    email = models.EmailField()
    phone_number = models.CharField(max_length=10)
    def __str__(self):
        return self.full_name
 
class FundedCompany(models.Model):
    name = models.CharField(max_length=255)
    website = models.URLField()
    industry = models.CharField(max_length=255, blank=True, null=True)
    funding_round = models.CharField(max_length=100)
    funding_amount = models.DecimalField(max_digits=30, decimal_places=2, blank=True, null=True)
    investors = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name 
    
class JobListing(models.Model):
    company = models.ForeignKey(FundedCompany, on_delete=models.CASCADE, related_name="job_listings")
    title = models.CharField(max_length=500)
    job_description = models.TextField(null=True, blank=True)
    location = models.CharField(max_length=255, blank=True, null=True)
    job_type = models.CharField(max_length=50, blank=True, null=True)  # Full-time, Part-time, etc.
    job_link = models.URLField(max_length=500)
    salary = models.CharField(max_length=100, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f'{self.title} at {self.company}'
    
class JobApplication(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    job = models.ForeignKey('JobListing', on_delete=models.CASCADE)
    subject = models.CharField(max_length=255)
    body = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_applied = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.user.username} - {self.job.title}"