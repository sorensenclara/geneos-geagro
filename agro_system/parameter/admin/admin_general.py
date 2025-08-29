from django.contrib import admin
from user.admin.adminSite import adminSite
from parameter.models.country import Country
from parameter.models.province import Province
from parameter.models.city import City
from parameter.models.gender import Gender
from parameter.models.countrysideCondition import CountrysideCondition
from parameter.models.lotRating import LotRating
from parameter.models.campaign import Campaing
from parameter.models.action import Action
from parameter.models.cultivationState import CiltivationState  
from parameter.models.otState import OTState
from parameter.models.port import Port
from parameter.models.varCropTechnique import VarCropTechnique
from parameter.models.specie import Specie
from parameter.models.area import Area
from parameter.models.measureUnit import MaensureUnit
from parameter.models.currency import Currency
from parameter.models.exchangeRate import exchangeRate


adminSite.register(Country)
adminSite.register(Province)
adminSite.register(City)
adminSite.register(Gender)
adminSite.register(CountrysideCondition)
adminSite.register(LotRating)
adminSite.register(Campaing)
adminSite.register(Action)
adminSite.register(CiltivationState)
adminSite.register(OTState)
adminSite.register(Port)
adminSite.register(VarCropTechnique)
adminSite.register(Specie)
adminSite.register(Area)
adminSite.register(MaensureUnit)
adminSite.register(Currency)
adminSite.register(exchangeRate)