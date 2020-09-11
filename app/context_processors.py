from django.conf import settings

def google_api_key(request):
    return {'GOOGLE_API_KEY': settings.GMAP_API}
