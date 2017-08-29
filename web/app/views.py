from datetime import datetime


from django.shortcuts import render

# Create your views here.
from django.http import HttpResponse, HttpRequest, HttpResponseRedirect

from .scraping import ScrapingHelper
from .models import Media, Hashtag, User

MYINSTAGRAM_URL = 'https://www.instagram.com/ivanivanov8923'


def index(request):
    hashtags = Hashtag.objects.all()
    context = {'user': User.objects.all()[0],
               'hashtags': hashtags}
    if request.method == 'GET' and 'hashtag' in request.GET:
        if request.GET['hashtag'] == 'all':
            context['medias'] = Media.objects.order_by('-created_date')
        else:
            hashtag = Hashtag.objects.get(text=request.GET['hashtag'])
            context['medias'] = Media.objects.filter(hashtags=hashtag).order_by('-created_date')
        return render(request, 'app/index.html', context)

    context['medias'] = Media.objects.order_by('-created_date')
    return render(request, 'app/index.html', context)


def scraping(request):
    sh = ScrapingHelper(MYINSTAGRAM_URL)
    try:
        sh.scrap()
    except Exception as error:
        print('ERROR:', error)
        raise
    finally:
        sh.destroy_wd()
    return HttpResponseRedirect('/')