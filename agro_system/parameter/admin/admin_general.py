from django.contrib import admin
from user.admin.adminSite import adminSite
from parameter.models.country import Country
from parameter.models.province import Province
from parameter.models.city import City
from parameter.models.gender import Gender
from parameter.models.countryside_condition import CountrysideCondition
from parameter.models.lot_rating import LotRating
from parameter.models.campaign import Campaing
from parameter.models.action import Action
from parameter.models.cultivation_state import CiltivationState  
from parameter.models.ot_state import OTState
from parameter.models.port import Port
from parameter.models.var_crop_technique import VarCropTechnique
from parameter.models.specie import Specie
from parameter.models.area import Area
from parameter.models.measure_unit import MaensureUnit
from parameter.models.currency import Currency
from parameter.models.exchange_rate import exchangeRate
from parameter.models.type_var_crop_technique  import TypeVarCropTechnique


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
adminSite.register(TypeVarCropTechnique)
