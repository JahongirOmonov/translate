

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # DOWNLOAD
    'ckeditor',
    # LOCAL
    'common',

]


index = INSTALLED_APPS.index('django.contrib.staticfiles')
print(index)



