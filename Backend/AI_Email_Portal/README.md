# **Email Sending Portal - Documentation**



## **Overview**

This project is an email-sending portal that leverages AI (Google Gemini) to generate personalized job application emails. Users can log in, view job opportunities, generate emails, edit them, attach documents, and send them to HR/Tech contacts. The system also tracks emails that have been sent.

## **Features**

* User Authentication (JWT-based)
* List of companies with job descriptions
* AI-generated email content using Google Gemini
* Option to edit emails before sending
* Attach documents to emails
* Track sent emails
* API tested with Postman (Postman collection included)

## **Technologies Used**

* **Backend:** Django REST Framework (DRF)
* **Authentication:** JWT (JSON Web Token)
* **AI Integration:** Google Gemini
* **Database:** SQLite
* **Frontend:** React.js
* **Deployment:** EC2/AWS

  Installation Guide
* 1. Clone the Repository
  2. Set Up Virtual Environment

     python -m venv venv
     source venv/bin/activate  # On macOS/Linux
     venv\Scripts\activate  # On Windows
  3. Install Dependencies

     pip install -r requirements.txt

  ## **Conclusion**

  This portal automates email generation for job applications using AI and tracks sent emails. It integrates JWT authentication, Google Gemini, and allows email customization before sending.
