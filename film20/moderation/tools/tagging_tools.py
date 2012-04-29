from django import forms
from django.db.models import Q
from django.db import transaction
from django.contrib import messages
from django.shortcuts import render, redirect
from django.utils.translation import gettext_lazy as _

from film20.core.models import ObjectLocalized
from film20.tagging.utils import parse_tag_input
from film20.moderation.registry import registry
from film20.moderation.items import ModeratorTool
from film20.tagging.models import Tag, TagAlias, TaggedItem

def parse_tag( name ):
    parsed = parse_tag_input( name + ", " )
    if len( parsed ) != 1:
        raise forms.ValidationError( _( 'Provide one valid tag name' ) )
    return parsed[0]


class TagRenameForm( forms.Form ):
    tagA = forms.CharField( label=_( "the tag to be renamed" ) )
    tagB = forms.CharField( label=_( "new tag" ) )

    def clean_tagA( self ):
        name = parse_tag( self.cleaned_data['tagA'] )
        try:
            Tag.objects.get( name=name )
            return name
        except Tag.DoesNotExist:
            raise forms.ValidationError( _( 'Tag does not exists' ) )

    def clean_tagB( self ):
        return parse_tag( self.cleaned_data['tagB'] )

    def clean( self ):
        cleaned_data = self.cleaned_data
        tagA = cleaned_data.get( 'tagA' )
        tagB = cleaned_data.get( 'tagB' )

        if tagA is not None and tagB is not None and tagA == tagB:
            raise forms.ValidationError( _( "The tag A and tag B must be different " ) )

        return cleaned_data


class TagCreateAliasForm( forms.Form ):
    tag = forms.CharField( label=_( "the tag to set alias" ) )
    aliases = forms.CharField( label=_( "aliases" ) )

    def clean_tag( self ):
        name = parse_tag( self.cleaned_data['tag'] )
        try:
            return Tag.objects.get( name=name )
        except Tag.DoesNotExist:
            raise forms.ValidationError( _( 'Tag does not exists' ) )

    def clean_aliases( self ):
        aliases = parse_tag_input( self.cleaned_data['aliases'] )
        if len( aliases ) == 0:
            raise forms.ValidationError( _( 'You must enter at least one alias' ) )

        for alias in aliases:
            # alias cannot be existing tag
            if Tag.objects.filter( name=alias ).count() > 0:
                raise forms.ValidationError( _( 'Alias cannot be existing tag, first rename tag:' ) + "'%s'" % alias )

        return aliases
            

    def clean( self ):
        cleaned_data = self.cleaned_data
        tag = cleaned_data.get( 'tag' )
        aliases = cleaned_data.get( 'aliases' )

        # alias cannot be assignet to multiple tags
        for alias in aliases if aliases else []:
            tag_aliases = TagAlias.objects.filter( ~Q( tag=tag ), name=alias )
            if tag_aliases.count() > 0:
                raise forms.ValidationError( _( 'Alias is already assigned to tag:' ) + "'%s'" % tag_aliases[0].tag )

        return cleaned_data


class TagRenamingTool( ModeratorTool ):
    name = "rename-tag"
    permission = "tagging.can_edit_tags"
    verbose_name = _( "Rename a tag" )

    def get_view( self, request ):
        moderated_items = registry.get_by_user( request.user )

        ctx = {
            "moderated_item": registry.get_by_name( self.name ),
            "moderated_items": moderated_items['items'],
            "moderator_tools": moderated_items['tools']
        }

        if request.method == 'POST':
            ctx['form'] = TagRenameForm( request.POST )
            if ctx['form'].is_valid():
                cleaned_data = ctx['form'].cleaned_data
                
                tag_a_name = cleaned_data['tagA']
                tag_a_tag = Tag.objects.get( name=tag_a_name )
                tag_a_count = self._get_tagged_objects_count( tag_a_tag )
                
                tag_b_name = cleaned_data['tagB']
                tag_b_tag = None
                try:
                    tag_b_tag = Tag.objects.get( name=tag_b_name )
                except Tag.DoesNotExist:
                    pass
                tag_b_count = self._get_tagged_objects_count( tag_b_tag ) if tag_b_tag else 0

                if not 'confirm' in request.POST:
                    ctx['to_confirm'] = {
                        'tagA': {
                            'name' : tag_a_name,
                            'count': tag_a_count,
                        },
                        'tagB': {
                            'name' : tag_b_name,
                            'count': tag_b_count,
                        }
                    }

                else:
                    
                    with transaction.commit_on_success():
                        # create tag b if not exists
                        if tag_b_tag is None:
                            tag_b_tag = Tag.objects.create( name=tag_b_name )
     
                        # replace tags
                        for obj in TaggedItem.objects.filter( tag=tag_a_tag ):
                            # if objects is already tagged with tag 'a' 
                            #   we must remove this relation
                            try:
                                ti = TaggedItem.objects.get( tag=tag_b_tag, content_type=obj.content_type, object_id=obj.object_id )
                                ti.delete()

                            except TaggedItem.DoesNotExist:
                                pass

                            obj.tag = tag_b_tag
                            obj.save()
                            
                            # update object localized tag_list
                            if isinstance( obj.object, ObjectLocalized ):
                                obj.object.tag_list = ', '.join( [ tag.name for tag in Tag.objects.get_for_object( obj.object ) ] )
                                obj.object.save()

                        # remove tag a
                        tag_a_tag.delete()
                        
                    messages.add_message( request, messages.INFO, _( "Tag renamed!" ) )
                    return redirect( self.get_absolute_url() )

        else: 
            ctx['form'] = TagRenameForm()

        return render( request, 'moderation/rename_tag/create.html', ctx )

    def _get_tagged_objects_count( self, tag ):
        return TaggedItem.objects.filter( tag=tag ).count()

class TagAliasTool( ModeratorTool ):
    name = "alias-tag"
    permission = "tagging.can_edit_tags"
    verbose_name = _( "Create alias for tag" )

    def get_view( self, request ):
        moderated_items = registry.get_by_user( request.user )

        ctx = {
            "moderated_item": registry.get_by_name( self.name ),
            "moderated_items": moderated_items['items'],
            "moderator_tools": moderated_items['tools']
        }

        if request.method == 'POST':
            ctx['form'] = TagCreateAliasForm( request.POST )
            if ctx['form'].is_valid():
                cleaned_data = ctx['form'].cleaned_data
                
                tag = cleaned_data['tag']
                aliases = cleaned_data['aliases']

                already_added = TagAlias.objects.filter( tag=tag )
                for added in already_added:
                    if added.name in aliases:
                        aliases.remove( added.name )
                    else:
                        added.delete()
               
                for alias in aliases:
                    TagAlias.objects.create( tag=tag, name=alias )
                
                messages.add_message( request, messages.INFO, _( "Alias created!" ) )
                return redirect( self.get_absolute_url() )

        else: 
            ctx['form'] = TagCreateAliasForm()

        return render( request, 'moderation/tag_aliases/create.html', ctx )


registry.register( TagAliasTool() )
registry.register( TagRenamingTool() )
