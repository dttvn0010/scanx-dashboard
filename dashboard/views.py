from django.http import HttpResponseRedirect
from django.contrib.auth.decorators import login_required

@login_required
def home(request):
    if request.user.username == "admin":
        return HttpResponseRedirect("/admin_app")
    else:
        return HttpResponseRedirect("/user_app")