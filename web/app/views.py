

from django.shortcuts import render

from django.http import HttpResponseRedirect
from django.core.exceptions import ObjectDoesNotExist

from .scraping import ScrapingHelper
from .models import Media, Hashtag, User

MYINSTAGRAM_URL = 'https://www.instagram.com/ivanivanov8923'


def index(request):
    hashtags = Hashtag.objects.all()
    try:
        user = User.objects.get(username=MYINSTAGRAM_URL.split('/')[-1])
    except ObjectDoesNotExist:
        user = User(username=MYINSTAGRAM_URL.split('/')[-1])

    context = {'user': user,
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
    finally:
        sh.destroy_wd()
    return HttpResponseRedirect('/')