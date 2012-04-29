from django.contrib import admin
from models import FilmOnChannel, Country, Town, Screening, Channel, Fetcher
from forms import FilmOnChannelForm
from django.contrib.admin.filterspecs import FilterSpec
import datetime
from django.utils.safestring import mark_safe

def rematch(modeladmin, request, queryset):
    for f in queryset.all():
        f.match_and_save()

rematch.short_description = u"match selected films"

class ImdbFilterSpec(FilterSpec):
  def __init__(self, f, request, params, model, model_admin, **kw):
    super(ImdbFilterSpec, self).__init__(f, request, params, model, model_admin, **kw)
    self.current_params = dict((k, v) for k, v in params.items() if (k.startswith("imdb_code" or k.startswith("id__gt"))))
    self.links = (('Wszystko', {}),
                  ('Bez imdb code',{'imdb_code__isnull':'true'}),
                  ('Z imdb code',{"imdb_code__isnull":''}),
                 )
            
  def choices(self,cl):
    return ({'selected':params == self.current_params, 
            'query_string':cl.get_query_string(params, ["imdb_code"]),
            'display':title,
            } for title, params in self.links)
    
  def title(self): return u"imdb_code"

FilterSpec.filter_specs.insert(0,(lambda f: f.name=='imdb_code', ImdbFilterSpec))

class ModelAdmin(admin.ModelAdmin):
    def lookup_allowed(self, lookup, value=None):
        return True

class FilmOnChannelAdmin(ModelAdmin):
    list_display = ('key', 'title', 'match', )
    raw_id_fields = ('film',)
    list_filter = ('match', 'imdb_code', 'source', 'created_at')
    search_fields = ('title',)

    form = FilmOnChannelForm
    
    actions = [rematch]

class ScreeningAdmin(ModelAdmin):
    list_display = ('id', 'film', 'channel', 'utc_time')
    list_filter = ('channel__name', 'channel__type', )
    raw_id_fields = ('film', 'channel')
    search_fields = ('channel__name',)

class FetcherInline(admin.TabularInline):
    model = Fetcher

def last_screening_time(obj):
    tm = obj.last_screening_time
    if tm and tm < datetime.datetime.now():
        style = "font-weight:bold; color:red"
    else:
        style = ""
    return mark_safe("<span style='%s'>%s</span>" % (style, tm or ''))
last_screening_time.allow_tags = True

class ChannelAdmin(ModelAdmin):
    search_fields = ('name',)
    list_display = ('name', 'is_active', last_screening_time)
    list_filter = ('is_active', 'type', 'country', 'town')
    ordering = ('name', )
    
    inlines = [FetcherInline]

    @classmethod
    def enable(cls, modeladmin, request, queryset):
        for item in queryset:
            item.is_active = True
            item.save()

    @classmethod
    def disable(cls, modeladmin, request, queryset):
        for item in queryset:
            item.is_active = False
            item.save()

    actions = ['enable', 'disable']

class CountryAdmin(ModelAdmin):
    ordering = ('name',)

class TownAdmin(ModelAdmin):
    ordering = ('name',)
    list_filter = ('country', )

admin.site.register(FilmOnChannel, FilmOnChannelAdmin)
admin.site.register(Screening, ScreeningAdmin)
admin.site.register(Country, CountryAdmin)
admin.site.register(Town, TownAdmin)
admin.site.register(Channel, ChannelAdmin)
