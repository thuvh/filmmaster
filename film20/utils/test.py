from django.test import TestCase as DjangoTestCase, Client as DjangoClient
import logging
logger = logging.getLogger(__name__)

from django.db.models import signals
from django.conf import settings

is_postgres = 'postgresql' in settings.DATABASES['default']['ENGINE']

class Client(DjangoClient):
    def _get_path(self, parsed):
        from django.conf import settings
        self.http_host = parsed[1] or settings.DOMAIN
        return super(Client, self)._get_path(parsed)

    def request(self, **kw):
        logger.info("request: %r", kw)
        kw.setdefault('HTTP_HOST', self.http_host)
        return super(Client, self).request(**kw)

class TestCase(DjangoTestCase):
    client_class = Client

    def _pre_setup(self):
        from film20.middleware import threadlocals

        self.__class__._created_models = []
        signals.post_save.connect(self._model_postsave)

        logger.info("running test %r", self.id())

        threadlocals._thread_locals.request = None

        DjangoTestCase._pre_setup(self)

    def _post_teardown(self):
        signals.post_save.disconnect(self._model_postsave)
        for cls in reversed(self._created_models):
            logger.debug("%s.objects.all().delete()", cls.__name__)
            cls.objects.all().delete()
        DjangoTestCase._post_teardown(self)

    @classmethod
    def _model_postsave(cls, sender, instance, created, **kw):
        if not instance.__class__ in cls._created_models:
            cls._created_models.append(instance.__class__)

