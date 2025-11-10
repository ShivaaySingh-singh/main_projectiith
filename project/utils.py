"""
Utility functions for sending user credential emails
"""
import secrets
import string
from django.core.mail import send_mail
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.conf import settings
from django.urls import reverse


def generate_random_password(length=8):
    """
    Generate a secure random password
    Includes: uppercase, lowercase, digits, and special characters
    """
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
    password = ''.join(secrets.choice(alphabet) for i in range(length))
    return password


def send_credentials_email(user, password, request):
    """
    Send email with username, password, and password reset link
    
    Args:
        user: CustomUser instance (the newly created user)
        password: Plain text password (before hashing)
        request: HttpRequest object (to build full URLs)
    
    Returns:
        bool: True if email sent successfully, False otherwise
    """
    # Generate password reset token (same as Django's built-in reset)
    token = default_token_generator.make_token(user)
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    
    # Build password reset URL (uses your EXISTING URL pattern)
    reset_url = request.build_absolute_uri(
        reverse('password_reset_confirm', kwargs={'uidb64': uid, 'token': token})
    )
    
    # Build login URL
    login_url = request.build_absolute_uri(reverse('login'))
    
    # Email subject
    subject = 'Your Account Login Credentials'
    
    # Plain text version
    text_message = f"""
Hello {user.first_name or user.username},

Your account has been successfully created!

Login Details:
--------------
Username: {user.username}
Password: {password}

Login URL: {login_url}

For security, we recommend changing your password after first login.

Click here to reset your password:
{reset_url}

(This link expires in 24 hours)

If you have any questions, please contact support.

Best regards,
The Team
    """
    
    # HTML version (looks better!)
    html_message = f"""
    <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;">
            <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 30px; border-radius: 10px 10px 0 0; text-align: center;">
                <h1 style="color: white; margin: 0;">Welcome!</h1>
            </div>
            
            <div style="background: #f9f9f9; padding: 30px; border-radius: 0 0 10px 10px;">
                <p style="font-size: 16px;">Hello <strong>{user.first_name or user.username}</strong>,</p>
                
                <p>Your account has been successfully created! Here are your login credentials:</p>
                
                <div style="background: white; padding: 20px; border-left: 4px solid #667eea; margin: 20px 0; border-radius: 5px;">
                    <p style="margin: 5px 0; font-size: 15px;">
                        <strong>Username:</strong> <span style="color: #667eea;">{user.username}</span>
                    </p>
                    <p style="margin: 5px 0; font-size: 15px;">
                        <strong>Password:</strong> <span style="color: #667eea; font-family: monospace;">{password}</span>
                    </p>
                </div>
                
                <div style="text-align: center; margin: 30px 0;">
                    <a href="{login_url}" 
                       style="background: #667eea; color: white; padding: 12px 30px; text-decoration: none; border-radius: 5px; display: inline-block; font-weight: bold;">
                        Login to Your Account
                    </a>
                </div>
                
                <hr style="border: none; border-top: 1px solid #ddd; margin: 30px 0;">
                
                <h3 style="color: #333;">Need to Change Your Password?</h3>
                <p>For security reasons, we recommend changing your password after your first login.</p>
                
                <div style="text-align: center; margin: 20px 0;">
                    <a href="{reset_url}" 
                       style="background: #28a745; color: white; padding: 12px 30px; text-decoration: none; border-radius: 5px; display: inline-block; font-weight: bold;">
                        Reset Your Password
                    </a>
                </div>
                
                <p style="color: #666; font-size: 13px; margin-top: 30px;">
                    <em>Note: The password reset link will expire in 24 hours.</em>
                </p>
                
                <p style="color: #666; font-size: 13px; margin-top: 20px;">
                    If you have any questions, please contact our support team.
                </p>
            </div>
        </body>
    </html>
    """
    
    # Send email
    try:
        send_mail(
            subject,
            text_message,
            settings.DEFAULT_FROM_EMAIL,
            [user.email],
            html_message=html_message,
            fail_silently=False,
        )
        print(f"✅ Email sent successfully to {user.email}")
        return True
    except Exception as e:
        print(f" Error sending email: {e}")
        return False
