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
from django.utils.translation import gettext_lazy as _
from django import forms
from film20.import_ratings.import_ratings_helper import SCORE_CONVERTIONS, SCORE_AUTO

class ImportImdbRatingsForm(forms.Form):
    file = forms.FileField(label=_('File'))
    overwrite = forms.BooleanField(label=_('Overwrite ratings'), required=False)

class ImportFilmwebRatingsForm(forms.Form):
#    filmweb_url = forms.URLField(label=_('Filmweb URL'))
    filmweb_user = forms.CharField(label=_('Filmweb user'))
#    filmweb_id = forms.CharField(label=_('Filmweb ID'))
    overwrite = forms.BooleanField(label=_('Overwrite ratings'), required=False)

#    filmweb_id_as_int = None
#
#    def clean_filmweb_id(self):
#        filmweb_id = self.cleaned_data.get('filmweb_id', '')
#        if filmweb_id:
#            try:
#                self.filmweb_id_as_int = int(filmweb_id)
#                return self.filmweb_id_as_int
#            except ValueError:
#                raise forms.ValidationError(_("filmweb_id must be integer!"))
#        else:
#            return None
#
#    def get_url(self):
#        if self.filmweb_id_as_int:
#            return "http://www.filmweb.pl/splitString/user/" + str(self.filmweb_id_as_int) + "/filmVotes"
#        else:
#            return None

class ImportCritickerFileForm(forms.Form):
    file = forms.FileField(label=_('File'))
    overwrite = forms.BooleanField(label=_('Overwrite ratings'), required=False)
    import_reviews = forms.BooleanField(label=_('Import reviews'), required=False)
    score_convertion = forms.ChoiceField(label=_('Score convertion'), required=True,
        choices=SCORE_CONVERTIONS, initial=SCORE_AUTO,
        widget=forms.RadioSelect(choices=SCORE_CONVERTIONS))