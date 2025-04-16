from django.urls import path
from rest_framework_simplejwt.views import  TokenRefreshView
from .views import MyTokenObtainPairView,UserRegisterationView,CreateGetJobPosition,ApplyforJob,JobApplicationView,SendEmailView,UserAppliedJobsAPIView
urlpatterns = [
    
    path('job/',CreateGetJobPosition.as_view()),  
    path('apply/<int:job_id>/',ApplyforJob.as_view()),
    path('job_application/<int:job_id>',JobApplicationView.as_view()),
    path('send_application/<int:appl_id>',SendEmailView.as_view()),
    path('user-applied-jobs/', UserAppliedJobsAPIView.as_view()),
    path('register/',UserRegisterationView.as_view()),  
    path('token/',MyTokenObtainPairView.as_view()),  
    path('refresh/', TokenRefreshView.as_view())
]
