import random
from django.shortcuts import render, redirect
from django.core.mail import send_mail
from django.contrib import messages
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from .models import Card

def login_view(request):
    if request.method == "POST":
        card_num = request.POST.get('card_number')
        password = request.POST.get('password')
        
        card = Card.objects.filter(card_number=card_num).first()
        if card:
            user = authenticate(username=card.user.username, password=password)
            if user:
                request.session['card_id'] = card.id
                return redirect('dashboard')
        
        messages.error(request, "Karta raqami yoki parol xato!")
    return render(request, 'login.html')

def register_view(request):
    if request.method == "POST":
        username = request.POST.get('username')
        email = request.POST.get('email')
        card_num = request.POST.get('card_number')
        password = request.POST.get('password')
        password_confirm = request.POST.get('password_confirm')
        pin = request.POST.get('pin')

        if password != password_confirm:
            messages.error(request, "Parollar mos kelmadi!")
            return render(request, 'register.html')

        otp_code = str(random.randint(100000, 999999))
        request.session['temp_reg_data'] = {
            'username': username, 'email': email, 'card_number': card_num,
            'password': password, 'pin': pin, 'otp': otp_code
        }

        try:
            send_mail('UzBank Kod', f'Kodingiz: {otp_code}', None, [email])
            return redirect('verify_email')
        except:
            messages.error(request, "Email yuborishda xato!")
    return render(request, 'register.html')

def verify_email(request):
    data = request.session.get('temp_reg_data')
    if not data: return redirect('register')
    if request.method == "POST":
        if request.POST.get('otp') == data['otp']:
            user = User.objects.create_user(username=data['username'], email=data['email'], password=data['password'])
            Card.objects.create(user=user, card_number=data['card_number'], pin_code=data['pin'], balance=0)
            del request.session['temp_reg_data']
            return redirect('login')
    return render(request, 'verify_email.html')

def dashboard(request):
    card_id = request.session.get('card_id')
    if not card_id:
        return redirect('login')
    
    my_card = Card.objects.get(id=card_id)
    
    if request.method == "POST":
        action = request.POST.get('action')
        
        if action == "deposit":
            amount = float(request.POST.get('amount', 0))
            my_card.balance += amount
            my_card.save()
            messages.success(request, f"{amount} UZS muvaffaqiyatli qo'shildi!")
            
        elif action == "transfer":
            target_number = request.POST.get('target')
            amount = float(request.POST.get('amount', 0))
            
            # 1. O'ziga o'zi o'tkazishni tekshirish (Siz aytgan muammo)
            if target_number == my_card.card_number:
                messages.error(request, "O'zingizning kartangizga pul o'tkaza olmaysiz!")
            
            else:
                to_card = Card.objects.filter(card_number=target_number).first()
                
                # 2. Qabul qiluvchi karta mavjudligini tekshirish
                if not to_card:
                    messages.error(request, "Bunday karta raqami tizimda topilmadi!")
                
                # 3. Balans yetarli ekanligini tekshirish
                elif my_card.balance < amount:
                    messages.error(request, "Hisobingizda mablag' yetarli emas!")
                
                # 4. Summa noldan katta bo'lishi kerak
                elif amount <= 0:
                    messages.error(request, "O'tkazma summasi noto'g'ri!")
                
                else:
                    # Hammasi yaxshi bo'lsa, pulni o'tkazamiz
                    my_card.balance -= amount
                    to_card.balance += amount
                    my_card.save()
                    to_card.save()
                    messages.success(request, f"{target_number} kartasiga {amount} UZS yuborildi!")
                    
    return render(request, 'dashboard.html', {'card': my_card})

def profile_view(request):
    card_id = request.session.get('card_id')
    if not card_id:
        return redirect('login')
    
    my_card = Card.objects.get(id=card_id)
    user = my_card.user

    if request.method == "POST":
        new_username = request.POST.get('username')
        new_email = request.POST.get('email')
        
        # Username band emasligini tekshirish
        if User.objects.filter(username=new_username).exclude(id=user.id).exists():
            messages.error(request, "Bu foydalanuvchi nomi band!")
        else:
            user.username = new_username
            user.email = new_email
            user.save()
            messages.success(request, "Ma'lumotlar muvaffaqiyatli yangilandi!")
            return redirect('profile')

    return render(request, 'profile.html', {'card': my_card, 'user': user})


def logout_view(request):
    request.session.flush() 
    return redirect('login')