from django.shortcuts import render
from django.contrib.auth import logout

# Create your views here.
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from .forms import LoginForm
    
def LoginPage(request):
    if request.user.is_authenticated:
        return redirect('Index:index')  # si ya está loggeado, redirige directo

    form = LoginForm(request.POST or None)
    msg = ''
    
    if request.method == 'POST':
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user = authenticate(request, username=username, password=password)
            if user:
                login(request, user)
                return redirect('Index:index')  # redirige al index después del login
            else:
                msg = 'Usuario o contraseña incorrectos'
    
    return render(request, 'Login/Login.html', {'form': form, 'msg': msg})


def LogoutPage(request):
    logout(request)
    return redirect('Login:LoginPage')  # Redirige al login después de cerrar sesión