#-------------------------------------------------------------------------------
# Filmaster - a social web network and recommendation engine
# Copyright (c) 2009 Filmaster (Borys Musielak, Adam Zielinski).
# 
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
# 
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#-------------------------------------------------------------------------------
import os

from django import template

import ajax_validation

register = template.Library()

VALIDATION_SCRIPT = open(os.path.join(os.path.dirname(ajax_validation.__file__), 'static', 'js', 'jquery-ajax-validation.js')).read()

def include_validation():
    return '''<script type="text/javascript">%s</script>''' % VALIDATION_SCRIPT
register.simple_tag(include_validation)
