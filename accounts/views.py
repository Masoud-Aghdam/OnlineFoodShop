from django.contrib import messages, auth
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.tokens import default_token_generator
from django.shortcuts import render, redirect
from django.template.defaultfilters import slugify
from django.utils.http import urlsafe_base64_decode

from accounts.forms import UserForm
from accounts.models import User, UserProfile
from accounts.utils import detectUser, check_role_customer, check_role_vendor, send_verification_email
from vendor.forms import VendorForm
from vendor.models import Vendor


# Create your views here.
def registerUser(request):
    if request.user.is_authenticated:
        messages.warning(request, 'You are already logged in!')
        return redirect("dashboard")
    elif request.method == "POST":
        form = UserForm(request.POST)
        if form.is_valid():
            #  Create the user using the form
            # password = form.cleaned_data['password']
            # user = form.save(commit=False)
            # user.role = User.CUSTOMER
            # user.set_password(password)
            # user.save()

            #  Create the user using create_user method
            first_name = form.cleaned_data['first_name']
            last_name = form.cleaned_data['last_name']
            username = form.cleaned_data['username']
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']
            user = User.objects.create_user(first_name=first_name, last_name=last_name,
                                            username=username, email=email, password=password
                                            )
            user.role = User.CUSTOMER
            user.save()

            #  send verification email
            email_template = 'accounts/emails/account_verification_email.html'
            mail_subject = 'Please activate your account.'
            send_verification_email(request, user, mail_subject, email_template)
            messages.success(request, 'Your account has been registered successfully!')
            return redirect('registerUser')
    else:
        form = UserForm()
    context = {
        'form': form,
        'errors': form.errors,
    }
    return render(request, 'accounts/registerUser.html', context)


def registerVendor(request):
    if request.user.is_authenticated:
        messages.warning(request, 'You are already logged in!')
        return redirect("myAccount")
    elif request.method == "POST":
        form = UserForm(request.POST)
        v_form = VendorForm(request.POST, request.FILES)  # request.FILES is for pdf or image receiving
        if form.is_valid() and v_form.is_valid():
            first_name = form.cleaned_data['first_name']
            last_name = form.cleaned_data['last_name']
            username = form.cleaned_data['username']
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']
            user = User.objects.create_user(first_name=first_name, last_name=last_name,
                                            username=username, email=email, password=password
                                            )
            user.role = User.VENDOR
            user.save()
            vendor = v_form.save(commit=False)
            vendor.user = user
            vendor_name = v_form.cleaned_data["vendor_name"]
            vendor.vendor_slug = slugify(vendor_name) + '-' + str(user.id)  # we used str to except errors of new registrations with same names
            user_profile = UserProfile.objects.get(user=user)
            vendor.user_profile = user_profile
            vendor.save()

            #  send verification email
            email_template = 'accounts/emails/account_verification_email.html'
            mail_subject = 'Please activate your account.'
            send_verification_email(request, user, mail_subject, email_template)
            messages.success(request, 'Your account has been registered successfully! please wait for approval.')
            return redirect('registerVendor')
    else:
        form = UserForm()
        v_form = VendorForm()

    context = {
        'form': form,
        'v_form': v_form,
    }
    return render(request, 'accounts/registerVendor.html', context)



def activate(request, uidb64, token):
    #  Activate the user by setting the is_active status to True
    try:
        uid = urlsafe_base64_decode(uidb64).decode()
        user = User._default_manager.get(pk=uid)
    except(TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    if user is not None and default_token_generator.check_token(user, token):
        user.is_active = True
        user.save()
        messages.success(request, 'Congratulation! Your account is activated.')
        return redirect('myAccount')
    else:
        messages.error(request, "invalid activation link")
        return redirect('myAccount')


def login(request):
    if request.user.is_authenticated:
        messages.warning(request, 'You are already logged in!')
        return redirect("myAccount")
    elif request.method == 'POST':
        email = request.POST['email']
        password = request.POST['password']

        user = auth.authenticate(email=email, password=password)

        if user is not None:
            auth.login(request, user)
            messages.success(request, "You are now logged in.")
            return redirect('myAccount')
        else:
            messages.error(request, 'Invalid login credentials')
            return redirect('login')
    return render(request, 'accounts/login.html')


def logout(request):
    auth.logout(request)
    messages.info(request, 'You are logged out.')
    return redirect('login')

@login_required(login_url='login')
def myAccount(request):
    user = request.user
    redirectUrl = detectUser(user)
    return redirect(redirectUrl)


@login_required(login_url='login')
@user_passes_test(check_role_customer)
def custDashboard(request):
    return render(request, 'accounts/custDashboard.html')


@login_required(login_url='login')
@user_passes_test(check_role_vendor)
def vendorDashboard(request):
    return render(request, 'accounts/vendorDashboard.html')


def forgot_password(request):
    if request.method == 'POST':
        email = request.POST['email']

        if User.objects.filter(email=email).exists():
            user = User.objects.get(email__exact=email)

            #  send reset password email
            email_template = 'accounts/emails/reset_password_email.html'
            mail_subject = "Reset your password"
            send_verification_email(request, user, mail_subject, email_template)

            messages.success(request, 'Password reset link has been sent to your email address.')
            return redirect('login')
        else:
            messages.error(request, 'Account does not exist.')
            return redirect('forgot_password')
    return render(request, 'accounts/forgot_password.html')


def reset_password_validate(request, uidb64, token):
    #  validate user and decoding the token and user pk
    try:
        uid = urlsafe_base64_decode(uidb64).decode()
        user = User._default_manager.get(pk=uid)
    except(TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    if user is not None and default_token_generator.check_token(user, token):
        request.session['uid'] = uid
        messages.info(request, 'Please reset your password')
        return redirect('reset_password')
    else:
        messages.error(request, 'this link has been expired!')
        return redirect('myAccount')


def reset_password(request):
    if request.method == "POST":
        password = request.POST['password']
        confirm_password = request.POST['confirm_password']

        if password == confirm_password:
            pk = request.session['uid']
            user = User.objects.get(pk=pk)
            user.set_password(password)
            user.is_active = True
            user.save()
            messages.success(request, 'Password reset successful')
            return redirect('login')
        else:
            messages.error(request, 'Password do not match!')
            return redirect('reset_password')
    return render(request, 'accounts/reset_password.html')
