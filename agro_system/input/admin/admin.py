from django.contrib import admin
from user.admin.adminSite import adminSite

from input.models.category_input import CategoryInput
from input.models.provider import Provider
from input.models.type_input import TypeInput
from input.models.type_provider import TypeProvider


# Register your models here.

adminSite.register(CategoryInput)
adminSite.register(Provider)
adminSite.register(TypeInput)
adminSite.register(TypeProvider)
