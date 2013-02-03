from django.conf.urls import patterns, include, url

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    # Examples:
    # url(r'^$', 'herokuflashcard.views.home', name='home'),
    # url(r'^herokuflashcard/', include('herokuflashcard.foo.urls')),

    # Uncomment the admin/doc line below to enable admin documentation:
    # url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    url(r'^admin/', include(admin.site.urls)),
    url(r'^cookie/$', 'herokuflashcard.apps.flashcard.views.cookie', name='cookie'),
    url(r'^welcome/$', 'herokuflashcard.apps.flashcard.views.welcome', name='welcome'),
    url(r'^create/$', 'herokuflashcard.apps.flashcard.views.create', name='create'),
    url(r'^delete/$', 'herokuflashcard.apps.flashcard.views.delete', name='delete'),
    url(r'^stats/$', 'herokuflashcard.apps.flashcard.views.stats', name='stats'),
    url(r'^session_builder/$', 'herokuflashcard.apps.flashcard.views.session_builder', name='session_builder'),
    url(r'^session_namer/$', 'herokuflashcard.apps.flashcard.views.session_namer', name='session_namer'),
    url(r'^practice/$', 'herokuflashcard.apps.flashcard.views.practice', name='practice'),
    url(r'^edit/$', 'herokuflashcard.apps.flashcard.views.edit', name='edit'),
    url(r'^$', 'herokuflashcard.apps.flashcard.views.home', name='home'),
    url(r'^signup/$', 'herokuflashcard.apps.flashcard.views.signup', name='signup'),
    url(r'^login/$', 'herokuflashcard.apps.flashcard.views.login', name='login'),
    url(r'^logout/$', 'herokuflashcard.apps.flashcard.views.logout', name='logout'),
)
