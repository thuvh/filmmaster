import logging
from django.core.management import base

class BaseCommand(base.BaseCommand):
    _LEVELS = (logging.WARNING, logging.INFO, logging.DEBUG)

    def execute(self, *args, **opts):
        # set console level according to verbosity
        for h in logging.getLogger('film20').handlers:
            if isinstance(h, logging.StreamHandler):
                h.level = self._LEVELS[int(opts.get('verbosity',0))]
        super(BaseCommand, self).execute(*args, **opts)
        