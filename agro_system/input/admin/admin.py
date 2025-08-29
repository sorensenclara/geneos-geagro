from django.contrib import admin
from user.admin.adminSite import adminSite

from input.models.categoryInput import CategoryInput
from input.models.provider import Provider
from input.models.typeInput import TypeInput
from input.models.typeProvider import TypeProvider


# Register your models here.

adminSite.register(CategoryInput)
adminSite.register(Provider)
adminSite.register(TypeInput)
adminSite.register(TypeProvider)
