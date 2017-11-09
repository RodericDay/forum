from django.conf import settings
from django.conf.urls import url, include
from django.contrib.auth import login
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import logout
from django.http import JsonResponse
from django.shortcuts import redirect, render

from api import views


def login_view(request):
    form = AuthenticationForm()
    if request.POST:
        form = AuthenticationForm(data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('home')
    return render(request, 'login.html', {'form': form})

def register_view(request):
    form = UserCreationForm()
    if request.POST:
        form = UserCreationForm(data=request.POST)
        if form.is_valid() and request.POST['secret'] == settings.PASS:
            user = form.save()
            login(request, user)
            return redirect('home')
    return render(request, 'register.html', {'form': form})


def home(request):
    return render(request, 'index.html')


urlpatterns = [
    url(r'^$', login_required(home), name='home'),
    url(r'^login/$', login_view, name='login'),
    url(r'^register/$', register_view, name='register'),
    url(r'^logout/$', logout, name='logout'),

    url(r'^api/topics/$', views.TopicList.as_view()),
    url(r'^api/topics/(?P<topic_id>\d+)/$', views.PostList.as_view()),
    url(r'^api/topics/(?P<pk>\d+)/edit/$', views.TopicDetail.as_view()),
    url(r'^api/posts/(?P<pk>\d+)/$', views.PostDetail.as_view()),
    url(r'^api/users/$', views.UserList.as_view()),
    url(r'^api/', lambda request: JsonResponse({"error": "Not found."}, status=404)),
]
