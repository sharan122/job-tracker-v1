from django.shortcuts import render
from rest_framework_simplejwt.views import TokenObtainPairView
from .serializer import MyTokenObtainPairSerializer,UserSerializer,JobPositionSerializer,JobApplicationSerializer
from rest_framework.response import Response
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny,IsAuthenticated
from .models import User,JobListing,JobApplication
import google.generativeai as genai
from django.conf import settings
import json
from django.core.mail import EmailMessage, BadHeaderError
from smtplib import SMTPException

# Create your views here.
class MyTokenObtainPairView(TokenObtainPairView):
    serializer_class = MyTokenObtainPairSerializer
    
class UserRegisterationView(APIView):
    permission_classes = [AllowAny]
    def post(self,request):
        serializer = UserSerializer(data=request.data)
        if serializer.is_valid():
            User.objects.create_user(
                **serializer.validated_data
            )
            return Response({"username":serializer.validated_data['username'],"email":serializer.validated_data['email']},status=status.HTTP_201_CREATED)
        print(serializer.errors,'error')
        return Response(serializer.errors,status=status.HTTP_400_BAD_REQUEST)
    

    
class CreateGetJobPosition(APIView):
    permission_classes = [IsAuthenticated]
    # def post(self,request):
    #     seriallizer = JobPositionSerializer(data=request.data)
    #     if seriallizer.is_valid():
    #         seriallizer.save()
    #         return Response({"messafe":'Job Positin Created '},status=status.HTTP_201_CREATED)
    #     return Response(seriallizer.errors,status=status.HTTP_400_BAD_REQUEST)
    def get (self,request):
        job_positions = JobListing.objects.all()
        serializer = JobPositionSerializer(job_positions,many=True )
        return Response(serializer.data,status=status.HTTP_200_OK)
    
class ApplyforJob(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, job_id=None):
        try:
            job = JobListing.objects.get(id=job_id)
        except JobListing.DoesNotExist:
            return Response({"error": "Job not found"}, status=status.HTTP_404_NOT_FOUND)

        user = request.user

        if JobApplication.objects.filter(user=user, job=job).exists():
            return Response({"error": "You have already applied for this job."}, status=status.HTTP_400_BAD_REQUEST)

        genai.configure(api_key=settings.GEN_AI_API_KEY)

        prompt = f"""
        Generate a professional job application email for the following job:
        
        Job Title: {job.title}
        Company: {job.company}
        Description: {job.job_description}
        
        Applicant Information:
        Name: {user.full_name}
        Bio: {user.bio}
        Email: {user.email}
        Phone: {user.phone_number}
        Linkedin: {user.linkedin_url}
        GitHub: {user.github_url}
        Portfolio: {user.portfolio_url}

        Return the result in JSON format:
        {{"subject": "The email subject line", "body": "The complete email body"}}
        also make the subject a bit short not more than 10 lines.
        """

        model = genai.GenerativeModel("gemini-1.5-flash")

        try:
            response = model.generate_content(prompt)
            if response:
                import re
                bot_response = response.text
                bot_response = re.sub(r"^```json\n|\n```$", "", bot_response.strip())
                try:
                    data = json.loads(bot_response)
                    formatted_dict = {
                        "subject": data["subject"],
                        "body": data["body"]
                    }
                    job_application = JobApplication.objects.create(
                        user=user,
                        job=job,
                        subject=formatted_dict.get("subject"),
                        body=formatted_dict.get("body"),
                        is_applied=True  
                    )

                    return Response({
                        "message": "Application saved successfully",
                        "data": {
                            "subject": job_application.subject,
                            "body": job_application.body,
                            "is_applied": job_application.is_applied
                        }
                    }, status=status.HTTP_201_CREATED)

                except json.JSONDecodeError as e:
                    return Response({"error": f"JSON Decode Error: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            else:
                return Response({"error": "Failed to generate response"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        except Exception as e:
            return Response({"error": f"Something went wrong: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        
class JobApplicationView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, job_id=None):
        
        applications = JobApplication.objects.filter(user=request.user)
        if job_id:
            applications = applications.filter(job__id=job_id)
            if not applications:
                return Response({"error": "No application found for this job"}, status=status.HTTP_404_NOT_FOUND)
            
        serializer = JobApplicationSerializer(applications, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
        
    def put(self, request, job_id):
        try:
            application = JobApplication.objects.get(user=request.user, job__id=job_id)
        except JobApplication.DoesNotExist:
            return Response({"error": "Application not found"}, status=status.HTTP_404_NOT_FOUND)
        serializer = JobApplicationSerializer(application, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            print(serializer.data,'serdata')
            return Response({"message": "Application updated ", "data": serializer.data}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class SendEmailView(APIView):
    def post(self, request, appl_id):
        try:
            application = JobApplication.objects.get(user=request.user, id=appl_id)
        except JobApplication.DoesNotExist:
            return Response({"error": "Application not found"}, status=status.HTTP_404_NOT_FOUND)

        user_resume = application.user.resume
        if not user_resume or not hasattr(user_resume, "path"):
            return Response({"error": "Resume file not found"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            send_email = EmailMessage(
                application.subject, 
                application.body, 
                settings.EMAIL_HOST_USER, 
                [application.job.email]
            )

            with open(user_resume.path, "rb") as resume_file:
                send_email.attach(user_resume.name, resume_file.read(), "application/pdf")

            send_email.send()
            return Response({"message": "Application has been sent to the employer"}, status=status.HTTP_200_OK)
        
        except BadHeaderError:
            return Response({"error": "Invalid header found in the email"}, status=status.HTTP_400_BAD_REQUEST)
        except SMTPException as e:
            return Response({"error": f"SMTP error: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except Exception as e:
            return Response({"error": f"Unexpected error: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
class UserAppliedJobsAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user_applications = JobApplication.objects.filter(user=request.user).values_list("job_id", flat=True)
        return Response({"applied_jobs": list(user_applications)})