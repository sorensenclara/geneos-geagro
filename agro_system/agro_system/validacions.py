from django.core.exceptions import ValidationError
from .constant_errors import ERROR_CUIL_CUIT_INVALID
from cffi.backend_ctypes import xrange

def validation_cuit(value):
    try:
        int(value)
    except:
        raise ValidationError(ERROR_CUIL_CUIT_INVALID)
    if value:
        if len(value) != 11:
            raise ValidationError(ERROR_CUIL_CUIT_INVALID)
        base = [5, 4, 3, 2, 7, 6, 5, 4, 3, 2]
        aux = 0
        for i in xrange(10):
            aux += int(value[i]) * base[i]
        aux = 11 - (aux - (int(aux / 11) * 11))
        if aux == 11:
            aux = 0
        if aux == 10:
            aux = 9
        if not aux == int(value[10]):
            raise ValidationError(ERROR_CUIL_CUIT_INVALID)