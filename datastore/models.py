from django.db import models
from datetime import datetime

DTYPE_STRING="string"
DTYPE_LINK="link"
DTYPE_INT="integer"
DTYPE_DATETIME="datetime"

DATATYPE_CHOICES=(
    (DTYPE_STRING, DTYPE_STRING),
    (DTYPE_LINK, DTYPE_LINK),
    (DTYPE_INT, DTYPE_INT),
    (DTYPE_DATETIME, DTYPE_DATETIME),
        )

INSTALLER_TYPE_NONE = "Not Installer"
INSTALLER_TYPE_NORMAL = "Normal Installer"
INSTALLER_TYPE_IPHONE = "iPhone Installer"
INSTALLER_TYPE_ANDROID = "Android Installer"

INSTALLER_TYPES = (
    (INSTALLER_TYPE_NONE, INSTALLER_TYPE_NONE),
    (INSTALLER_TYPE_NORMAL, INSTALLER_TYPE_NORMAL),
    (INSTALLER_TYPE_IPHONE, INSTALLER_TYPE_IPHONE),
    (INSTALLER_TYPE_ANDROID, INSTALLER_TYPE_ANDROID),
    )



""" A category of data that can be used to describe a Build """
class MetadataCategory(models.Model):
    """ Human readable name (for display only) """
    friendly_name = models.CharField(max_length=128)

    """ Sluggified name, better for searching """
    slug = models.SlugField(unique=True)

    """ Whether Builds require a value of this type """
    required = models.BooleanField(default=False)

    """ The data type this category contains """
    datatype = models.CharField(    choices=DATATYPE_CHOICES,
                    default="string",
                    max_length=16)


""" A value of data that can be used to describe a build """
class MetadataValue(models.Model):
    """ The category of data this object describes """
    category = models.ForeignKey(MetadataCategory, related_name="values")

    """ The stored string value of this data object """
    string_value = models.CharField(max_length=256)
    
    """ The stored value of this data object in its true form """
    @property
    def value(self):
        if( self.category.datatype == DTYPE_INT ):
            return int(self.string_value)
        elif( self.category.datatype == DTYPE_DATETIME ):
            return datetime.strptime(self.string_value, "%Y-%m-%d %H:%M:%S")
        else:
            return self.string_value

    @value.setter
    def value(self, v):
        if( type(v) is int and self.category.datatype == DTYPE_INT ):
            self.string_value = str(v)
        elif( type(v) is datetime and self.category.datatype == DTYPE_DATETIME ):
            self.string_value = v.strftime(v, "%Y-%m-%d %H:%M:%S")
        elif( type(v) is str and self.category.datatype == DTYPE_STRING ):
            self.string_value = v
        elif( type(v) is str and "://" in v and self.category.datatype == DTYPE_LINK ):
            self.string_value = v
        else:
            raise Exception("Value is of invalid type")


""" A tag of arbitrary, category-less data """
class Tag(models.Model):
    """ The value of this tag """
    value = models.CharField(max_length=256)


class Build(models.Model):
    """ A human readable name for this build """
    name = models.CharField(max_length=64)

    """ Metadata by which this build is categorized """
    metadata = models.ManyToManyField(MetadataValue, related_name="builds")

    """ Any arbitrary data associated with this build """
    tags = models.ManyToManyField(Tag, related_name="builds")


""" A type of artifact that can be downloaded. """
class ArtifactCategory(models.Model):
    slug = models.SlugField(unique=True)
    friendly_name = models.CharField(max_length=64)
    installer_type = models.CharField(max_length=32, choices=INSTALLER_TYPES, default=INSTALLER_TYPE_NONE)
    extension = models.CharField(max_length=16)

    def __unicode__(self):
        return unicode(self.friendly_name)

    @property
    def download_decorator(self):
        if self.installer_type == ArtifactType.INSTALLER_TYPE_IPHONE:
            current_site = Site.objects.get_current()
            return "itms-services://?action=download-manifest&url=%s{dl_url}" % (current_site.domain)
        else:
            return "{dl_url}"


""" An artifact of a specific type """
class Artifact(models.Model):
    category = models.ForeignKey(ArtifactCategory, related_name='instances')
    build = models.ForeignKey(Build, related_name='artifacts')
    s3_key = models.CharField(max_length=64, null=True)
    file_size = models.IntegerField(default=0)
    md5_hash = models.CharField(max_length=32, null=True)

    def __unicode__(self):
        return u"%s (Build %s)" % (self.a_type.friendly_name, self.build.id)
