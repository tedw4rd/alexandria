from tastypie.resources import ModelResource, ALL, ALL_WITH_RELATIONS
from tastypie.authentication import ApiKeyAuthentication
from tastypie import fields
from datastore.models import *
from django.db.models import Q
from datastore.utils import get_build_query_set


class EmuBabyResource(ModelResource):
	def determine_format(self, request):
		return 'application/json'


class MetaDataCategoryResource(EmuBabyResource):
	class Meta:
		queryset = MetaDataCategory.objects.all()
		resource_name = 'metadatacategory'
		filtering = {
			'slug': ALL,
			'is_extra_data': ALL
		}
		authentication = ApiKeyAuthentication()


class MetaDataResource(EmuBabyResource):
	def apply_filters(self, request, applicable_filters):
		base_list = super(MetaDataResource, self).apply_filters(request, applicable_filters)
		if request.GET.get('distinct', None):
			return base_list.distinct('value')
		else:
			return base_list


	category = fields.ForeignKey(MetaDataCategoryResource, 'category', full=True, full_detail=True)
	class Meta:
		queryset = MetaData.objects.all()
		resource_name = 'metadata'
		filtering = {
			'category': ALL_WITH_RELATIONS
		}
		authentication = ApiKeyAuthentication()


class ArtifactTypeResource(EmuBabyResource):
	class Meta:
		queryset = ArtifactType.objects.all()
		resource_name = 'artifacttype'
		authentication = ApiKeyAuthentication()
		filtering = {
			'installer_type': ALL
		}


class ArtifactResource(EmuBabyResource):
	a_type = fields.ForeignKey(ArtifactTypeResource, 'a_type', full=True, full_detail=True)
	class Meta:
		queryset = Artifact.objects.all()
		resource_name = 'artifact'
		filtering = {
			'a_type': ALL_WITH_RELATIONS
		}
		authentication = ApiKeyAuthentication()


class BuildResource(EmuBabyResource):
	metadata = fields.ToManyField(	MetaDataResource, 
									attribute=lambda bundle: MetaData.objects.filter(build__id=bundle.obj.id, 
									category__is_extra_data=False), 
									null=True,
									use_in='detail',
									full=True,
									full_detail=True)

	extra_data = fields.ToManyField(MetaDataResource, 
									attribute=lambda bundle: MetaData.objects.filter(build__id=bundle.obj.id, category__is_extra_data=True), 
									null=True,
									use_in='detail',
									full=True,
									full_detail=True)

	installers = fields.ToManyField(ArtifactResource, 
									attribute=lambda bundle: Artifact.objects.filter(build__id=bundle.obj.id).exclude(a_type__installer_type=ArtifactType.INSTALLER_TYPE_NONE),
									null=True,
									use_in='detail',
									full=True,
									full_detail=True)

	other_artifacts = fields.ToManyField(ArtifactResource, 
										attribute=lambda bundle: Artifact.objects.filter(build__id=bundle.obj.id, 
																						a_type__installer_type=ArtifactType.INSTALLER_TYPE_NONE), 
										null=True,
										use_in='detail',
										full=True,
										full_detail=True)

	def apply_filters(self, request, applicable_filters):
		base_list = super(BuildResource, self).apply_filters(request, applicable_filters)

		q_list = get_build_query_set(request.GET, base_list)

		if q_list is None:
			return base_list
		else:
			return q_list


	def dehydrate_metadata(self, bundle):
		dehydrated_metadata = []
		for m in bundle.data['metadata']:
			value = m.data['value']
			cat = m.data['category'].data['friendly_name']
			dehydrated_metadata.append({'category_name': cat, 'value': value, 'resource_uri': m.data['resource_uri']})
		return dehydrated_metadata


	def dehydrate_extra_data(self, bundle):
		dehydrated_extra_data = []
		for m in bundle.data['extra_data']:
			value = m.data['value']
			cat = m.data['category'].data['friendly_name']
			dehydrated_extra_data.append({'category_name': cat, 'value': value})
		return dehydrated_extra_data


	def dehydrate_installers(self, bundle):
		dehydrated_installers = []
		for m in bundle.data['installers']:
			download_url = m.data['download_url']
			type_name = m.data['a_type'].data['friendly_name']
			dehydrated_installers.append({'type_name': type_name, 'download_url': download_url, 'resource_uri': m.data['resource_uri']})
		return dehydrated_installers


	def dehydrate_other_artifacts(self, bundle):
		dehydrate_other_artifacts = []
		for m in bundle.data['other_artifacts']:
			download_url = m.data['download_url']
			type_name = m.data['a_type'].data['friendly_name']
			dehydrate_other_artifacts.append({'type_name': type_name, 'download_url': download_url, 'resource_uri': m.data['resource_uri']})
		return dehydrate_other_artifacts


	class Meta:
		queryset = Build.objects.all()
		resource_name = 'build'
		authentication = ApiKeyAuthentication()
