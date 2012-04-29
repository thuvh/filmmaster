from django.conf.urls.defaults import *
from film20.register.views import registration_view
from film20.config.urls import *

registerpatterns = patterns('',
    # Example:
    # (r'^filmaster_info/', include('filmaster_info.foo.urls')),
    (r'^'+urls["MOBILE"]+'/$', registration_view),

)