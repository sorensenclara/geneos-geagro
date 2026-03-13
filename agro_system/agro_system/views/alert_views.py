from django.shortcuts import redirect, render
from django.contrib.auth.decorators import login_required


@login_required
def AlertView(request):
    
    data = {
    
    }

    return render(request, 'pages/alert.html', data)
