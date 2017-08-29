from django.db import models


class User(models.Model):
    user_id = models.CharField(max_length=15, unique=True)
    username = models.CharField(max_length=30)

    def __str__(self):
        return '%s(%s)' % (self.username, self.user_id)


class Hashtag(models.Model):
    text = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return "%s" % (self.text,)


class Media(models.Model):
    media_id = models.CharField(max_length=35, blank=True, unique=True)
    filepath = models.CharField(max_length=200, blank=True, null=True)
    link = models.CharField(max_length=300, blank=True)
    url = models.CharField(max_length=200, blank=True, null=True)
    TYPE_CHOICES = (('i', 'image'),
                    ('v', 'video'),)
    type = models.CharField(max_length=10,
                            choices=TYPE_CHOICES)
    author = models.ForeignKey(User, models.SET_DEFAULT, blank=True, null=True, default=None)
    hashtags = models.ManyToManyField(Hashtag, blank=True)
    created_date = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return "Media: %s, link: %s, (%s);" % (self.media_id, self.link, self.type)



