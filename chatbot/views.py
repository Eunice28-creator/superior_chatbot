from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from openai import OpenAI  # Updated import for OpenAI 1.0.0+
import os
import re
import logging
from rest_framework.response import Response
from rest_framework.decorators import api_view
from datetime import datetime
from dotenv import load_dotenv
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure

# Load environment variables
load_dotenv()

# OpenAI API Key
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
MONGO_URI = os.getenv("MONGO_URI")
MONGO_DB_NAME = os.getenv("MONGO_DB_NAME")

# Logger
logger = logging.getLogger(__name__)

# Initialize OpenAI client
client = OpenAI(api_key=OPENAI_API_KEY)

# MongoDB Connection
def get_mongo_client():
    try:
        return MongoClient(
            MONGO_URI,
            tls=True,  # Enable TLS/SSL
            tlsAllowInvalidCertificates=True,  # Allow invalid certificates (for testing only)
            socketTimeoutMS=30000,  # Increase socket timeout
            connectTimeoutMS=30000,  # Increase connection timeout
        )
    except ConnectionFailure as e:
        logger.error(f"MongoDB connection error: {e}")
        raise Exception(f"Failed to connect to MongoDB: {e}")

# Email validation
def is_valid_email(email):
    return re.match(r"[^@]+@[^@]+\.[^@]+", email)

@csrf_exempt
def health_check(request):
    """
    Health check endpoint to monitor the status of the application.
    """
    return JsonResponse({"status": "ok"})

@csrf_exempt
@api_view(["POST"])
def superior_chat(request):
    if request.method == "POST":
        try:
            user_email = request.data.get("user_email")
            user_message = request.data.get("message")
            business_type = request.data.get("business_type", "General Business")

            # Input validation
            if not user_email or not is_valid_email(user_email):
                return Response({"response": "Please provide a valid email address."}, status=400)
            if not user_message or len(user_message.strip()) == 0:
                return Response({"response": "Please provide a valid message."}, status=400)

            # MongoDB connection
            mongo_client = get_mongo_client()
            db = mongo_client[MONGO_DB_NAME]
            superior_conversations = db.superior_chatbot_conversations

            # Retrieve past conversations
            user_history = list(superior_conversations.find({"user_email": user_email}).sort("timestamp", -1))

            # Chatbot personality
            if business_type == "Real Estate":
                chatbot_personality = "You are an AI assistant for a real estate agency. You help users find properties."
            elif business_type == "Law Firm":
                chatbot_personality = "You are an AI assistant for a law firm. You answer legal service questions."
            elif business_type == "E-Commerce":
                chatbot_personality = "You are an AI chatbot for an online store. You help customers with orders and refunds."
            else:
                chatbot_personality = "You are an AI assistant for a business."

            # Lead qualification prompt
            lead_qualification_prompt = """
            You are an advanced AI chatbot that helps businesses qualify leads. 
            When a user asks about services, do the following:
            - Ask about their budget
            - Ask what services they need
            - Ask for their preferred timeline
            - If they answer all, confirm their details and say a representative will contact them.
            """

            # Build the prompt
            prompt = f"""
            {chatbot_personality}
            {lead_qualification_prompt}
            Previous conversation:
            {"".join([f"User: {chat['message']}\nChatbot: {chat['response']}\n" for chat in user_history[:5]])}
            User: {user_message}
            Chatbot:
            """

            # Generate AI response
            response = client.chat.completions.create(
                model="gpt-4",  # Use the correct model name
                messages=[{"role": "user", "content": prompt}],
                max_tokens=150,
                temperature=0.7,
            )

            # Extract the AI response
            ai_response = response.choices[0].message.content

            # Save conversation to MongoDB
            superior_conversations.insert_one({
                "user_email": user_email,
                "message": user_message,
                "response": ai_response,
                "business_type": business_type,
                "timestamp": datetime.utcnow()
            })

            return Response({"response": ai_response})

        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            return JsonResponse({"error": f"An internal error occurred: {e}"}, status=500)
    else:
        return JsonResponse({"error": "Only POST requests are allowed."}, status=405)

@csrf_exempt
def superior_chat_view(request):
    if request.method == 'POST':
        # Process the request and return a response
        return JsonResponse({'message': 'Success!'})
    else:
        return JsonResponse({'error': 'Method not allowed'}, status=405)

