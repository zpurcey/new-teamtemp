from django.shortcuts import render

def home(request):
    return render(request, 'index.html')

def submit(request, id):
    return render(request, 'form.html', {'id': id})

def admin(request, id):
    return render(request, 'results.html', {'id': id})
