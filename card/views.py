import random
from decimal import Decimal
from django.shortcuts import render, redirect
from django.core.mail import send_mail
from django.contrib import messages
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login as auth_login, logout
from django.db.models import Sum
from .models import Card, Transaction

# LOGIN
def login_view(request):
    if request.method == "POST":
        card_num = request.POST.get('card_number')
        password = request.POST.get('password')
        
        card = Card.objects.filter(card_number=card_num).first()
        if card:
            user = authenticate(username=card.user.username, password=password)
            if user:
                auth_login(request, user)
                request.session['card_id'] = card.id
                
                if user.is_staff:
                    return redirect('admin_dashboard')
                else:
                    return redirect('user_dashboard')
        
        messages.error(request, "Karta raqami yoki parol xato!")
    return render(request, 'login.html')

# RO'YXATDAN O'TISH
def register_view(request):
    if request.method == "POST":
        username = request.POST.get('username')
        email = request.POST.get('email')
        card_num = request.POST.get('card_number')
        password = request.POST.get('password')
        password_confirm = request.POST.get('password_confirm')

        if User.objects.filter(username=username).exists():
            messages.error(request, "Bu username band!")
            return render(request, 'register.html')
        
        if Card.objects.filter(card_number=card_num).exists():
            messages.error(request, "Bu karta raqami allaqachon ro'yxatdan o'tgan!")
            return render(request, 'register.html')

        if password != password_confirm:
            messages.error(request, "Parollar mos kelmadi!")
            return render(request, 'register.html')

        otp_code = str(random.randint(100000, 999999))
        request.session['temp_reg_data'] = {
            'username': username, 'email': email, 'card_number': card_num,
            'password': password, 'otp': otp_code
        }

        try:
            send_mail(
                'UzBank Tasdiqlash Kodi', 
                f'Sizning tasdiqlash kodingiz: {otp_code}', 
                'yoqubov11nodir@gmail.com', # Yuboruvchi email
                [email],
                fail_silently=False,
            )
            return redirect('verify_email')
        except Exception as e:
            messages.error(request, f"Email yuborishda xato: {e}")
    return render(request, 'register.html')

# EMAIL TASDIQLASH (TUZATILGAN)
def verify_email(request):
    data = request.session.get('temp_reg_data')
    if not data: 
        return redirect('register')
    
    if request.method == "POST":
        if request.POST.get('otp') == data['otp']:
            # Foydalanuvchi allaqachon yaratilmaganini tekshiramiz
            if not User.objects.filter(username=data['username']).exists():
                user = User.objects.create_user(
                    username=data['username'], 
                    email=data['email'], 
                    password=data['password']
                )
                
                # Card modelida PIN yo'qligi uchun uni olib tashladik
                card = Card.objects.create(
                    user=user, 
                    card_number=data['card_number'], 
                    balance=Decimal('0.00')
                )
                
                # Avtomatik login
                auth_login(request, user)
                request.session['card_id'] = card.id
                
                # Sessiyani xavfsiz o'chirish (KeyError oldini olish)
                request.session.pop('temp_reg_data', None)
                
                messages.success(request, "Muvaffaqiyatli ro'yxatdan o'tdingiz!")
                return redirect('user_dashboard')
            else:
                return redirect('login')
        else:
            messages.error(request, "Kod noto'g'ri!")
            
    return render(request, 'verify_email.html')

# DASHBOARD (USER)
def dashboard(request):
    card_id = request.session.get('card_id')
    if not card_id:
        return redirect('login')
    
    try:
        my_card = Card.objects.get(id=card_id)
    except Card.DoesNotExist:
        return redirect('logout')
    
    if request.method == "POST":
        action = request.POST.get('action')
        
        if action == "deposit":
            amount = request.POST.get('amount')
            if amount:
                my_card.balance += Decimal(amount) 
                my_card.save()
                Transaction.objects.create(sender=my_card.user, amount=Decimal(amount), type="Deposit")
                messages.success(request, f"{amount} UZS qo'shildi!")
            return redirect('user_dashboard')
            
        elif action == "transfer":
            target = request.POST.get('target')
            amount_str = request.POST.get('amount')
            
            if target and amount_str:
                amount = Decimal(amount_str) 
                to_card = Card.objects.filter(card_number=target).first()
                
                if not to_card:
                    messages.error(request, "Karta topilmadi!")
                elif target == my_card.card_number:
                    messages.error(request, "O'zingizga pul o'tkaza olmaysiz!")
                elif my_card.balance < amount:
                    messages.error(request, "Mablag' yetarli emas!")
                else:
                    my_card.balance -= amount 
                    to_card.balance += amount 
                    my_card.save()
                    to_card.save()
                    Transaction.objects.create(sender=my_card.user, receiver_card=target, amount=amount, type="Transfer")
                    messages.success(request, "O'tkazma bajarildi!")
            return redirect('user_dashboard')
                    
    return render(request, 'user_dashboard.html', {'card': my_card})

# PROFIL
def profile_view(request):
    card_id = request.session.get('card_id')
    if not card_id: return redirect('login')
    
    my_card = Card.objects.get(id=card_id)
    user = my_card.user

    if request.method == "POST":
        new_username = request.POST.get('username')
        if User.objects.filter(username=new_username).exclude(id=user.id).exists():
            messages.error(request, "Bu username band!")
        else:
            user.username = new_username
            user.email = request.POST.get('email')
            user.save()
            messages.success(request, "Yangilandi!")
        return redirect('profile')

    return render(request, 'profile.html', {'card': my_card, 'user': user})

# LOGOUT
def logout_view(request):
    logout(request)
    request.session.flush() 
    return redirect('login')

# ====== ADMIN SEKSIYASI ==========

def admin_login(request):
    if request.method == "POST":
        name = request.POST.get('name')
        password = request.POST.get('password')
        user = authenticate(username=name, password=password)
        if user is not None and user.is_staff:
            auth_login(request, user)
            return redirect('admin_dashboard')
        messages.error(request, "Admin xatosi!")
    return render(request, 'admin_login.html')

def admin_dashboard(request):
    if not request.user.is_authenticated or not request.user.is_staff:
        return redirect('admin_login')

    if request.method == "POST":
        action = request.POST.get('action')

        if action == "create_user":
            username = request.POST.get('username')
            if not User.objects.filter(username=username).exists():
                u = User.objects.create_user(username=username, password=request.POST.get('password'))
                Card.objects.create(user=u, card_number=request.POST.get('card_number'), balance=Decimal('0.00'))
                messages.success(request, "Mijoz qo'shildi!")
            else:
                messages.error(request, "User band!")

        elif action == "update_balance":
            try:
                card = Card.objects.get(id=request.POST.get('card_id'))
                new_balance = request.POST.get('balance', 0)
                card.balance = Decimal(str(new_balance))
                card.save()
                messages.success(request, "Balans o'zgardi!")
            except Exception as e:
                messages.error(request, f"Xato: {e}")

        elif action == "delete_user":
            User.objects.filter(id=request.POST.get('user_id')).delete()
            messages.warning(request, "O'chirildi.")

        return redirect('admin_dashboard')

    context = {
        'cards': Card.objects.all(),
        'user_count': User.objects.count(),
        'total_money': Card.objects.aggregate(Sum('balance'))['balance__sum'] or 0,
        'transactions': Transaction.objects.all().order_by('-date')
    }
    return render(request, 'admin_dashboard.html', context)