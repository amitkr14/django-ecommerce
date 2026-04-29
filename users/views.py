from django.shortcuts import render,redirect
from django.http import HttpResponse
from .forms import CreateUserForm
from django.template.loader import render_to_string
from django.contrib.sites.shortcuts import get_current_site
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes,force_str
from .token import account_activation_token
from django.contrib.auth.models import User
from .forms import LoginForm,UserUpdateForm
from django.contrib.auth import authenticate,login,logout
import random
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth import update_session_auth_hash

# Create your views here.
def register(request):
    form = CreateUserForm()
    if request.method=="POST":
        form = CreateUserForm(request.POST)
        if form.is_valid():
            user = form.save()
            user.is_active = False
            user.save()
            current_site = get_current_site(request)

            #email verification logic

            subject = 'Verify your email to activate account'
            message = render_to_string('users/email-verification.html',{
                'user': user,
                'domain': current_site.domain,
                'uid':urlsafe_base64_encode(force_bytes(user.pk)),
                'token': account_activation_token.make_token(user),

            })
            user.email_user(subject=subject,message=message)
            return redirect('email-verification-sent')
            

    return render(request,'users/register.html',{'form':form})

def email_verification(request,uidb64,token):
    unique_id = force_str(urlsafe_base64_decode(uidb64))
    user = User.objects.get(pk=unique_id)
    if user and account_activation_token.check_token(user,token):
        user.is_active=True
        user.save()
        return redirect('email-verification-success')
    else:
        return redirect('email-verification-failed')    

    
def email_verification_sent(request):
    return render(request,'users/email-verification-sent.html')


def email_verification_success(request):
    return render(request,'users/email-verification-success.html')

def email_verification_failed(request):
    return render(request,'users/email-verification-failed.html')


def user_login(request):
    form = LoginForm()
    if request.method=="POST":
        form= LoginForm(request,data=request.POST)
        if form.is_valid():
            username = request.POST.get('username')
            password = request.POST.get('password')
            user= authenticate(request,username=username,password= password)
            if user is not None:
                login(request,user)
                return redirect('index')

    return render(request,'users/login.html',{'form':form})


def user_logout(request):
    logout(request)
    return redirect('index')

@login_required
def profile(request):
    return render(request, 'users/profile.html')
# def profile(request):
    
#     if request.method=="POST":
#         user_form= UserUpdateForm(request.POST,instance=request.user)
#         if user_form.is_valid():
#             user_form.save()
#             return redirect('index')
#     user_form = UserUpdateForm(instance=request.user)    
#     return render(request,'users/profile.html',{'user_form':user_form})

@login_required
def generate_otp(request):
    
    otp = str(random.randint(100000, 999999))
    
    request.session['change_password_otp']=otp
    
    messages.info(request, f"Your OTP is: {otp}")
    
    return redirect('verify_otp')

@login_required
def verify_otp(request):
    if request.method == "POST":
        entered_otp = request.POST.get('otp')
        real_otp = request.session.get('change_password_otp')
        
        if entered_otp == real_otp:
            # OTP matches! Give them a temporary "VIP pass" in their session
            request.session['otp_verified'] = True
            return redirect('set_new_password')
        else:
            messages.error(request, "Invalid OTP. Please try again.")
            
    return render(request, 'users/verify_otp.html')

@login_required
def set_new_password(request):
    
    if not request.session.get('otp_verified'):
        return redirect('generate_otp')
        
    if request.method == "POST":
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')
        
        if new_password == confirm_password:
            user = request.user
            user.set_password(new_password)
            user.save()
            
            # Keep the user logged in after their password changes
            update_session_auth_hash(request, user)
            
            # Clean up the session data so the OTP can't be reused
            del request.session['change_password_otp']
            del request.session['otp_verified']
            
            messages.success(request, "Password updated successfully!")
            return redirect('profile') 
        else:
            messages.error(request, "Passwords do not match.")
            
    return render(request, 'users/set_new_password.html')

