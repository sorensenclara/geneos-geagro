# Proyecto GeAgro

### El proyecto cuenta con:

* ***Interfaz de usuario***

Se istalo la interfaz  [JAZZMIN](https://django-jazzmin.readthedocs.io/)


* ***Usuario personalizado***

Se extiende el usuario que viene por defecto para que se ingrese por mail.  
Sus campos son:  
Email, Nombre, Apellido, Grupos, Permiso , Is staff (puede ingresar al admin de django), Password y type.
Type se agisna dependiento del tipo de usuario, si es Administrador general, Organización o Productor. 

Se crearon 2 nuevos usuarios:

**Usuario Productor**

  Con los campos: name, identification_number, address, organization, prefix, sequence.

  * El usuario puede pertenercer o no a una organización, si el usuario productor se crea desde un usuario Organización, se asigna automaticamente el mismo. 

**Usuario Organización**

  Con los campos: company_name, identification_number, address

*Aclaración*: 

  -Los usuarios productor se deben crear desde sus modelos, no desde el usario General. Al crearse se le agina el tipo de usuario automaticamente. 

  -Los usuarios productor deben tener el grupo Productor y los usuarios organizacíon el grupo Organizacion 


* ***Settings***

El settings se separa en:

base.py   
Toda la configuración del proyecto que se utiliza tanto en desarrollo como producción

Extiende a base.py y además tiene configuración utilizada solo en desarrollo.

prod.py  
Extiende a base.py y además tiene configuración utilizada solo en producción.

El proyecto se encuentra configurado para desarrollo.  
Para cambiar a prod se debe cambiar en el archivo manage.py:  
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'proyecto_django_inicial.settings.dev')

por:  
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'proyecto_django_inicial.settings.prod’)


* ***Archivo gitignore***

Ya tiene el archivo .gitignore con todo lo que debe ser ignorado para no subirse

* ***Traducciones** 

Se realizan las traducciones a español:
Para eso se debe poner en cada campo a traduccir  **_('name_field')**

Cuando se agregen nuevas palabras correr:

    python manage.py makemessages -l es 
    (completar archivo .po)
    python manage.py compilemessages

Contiene el archivo locale/django.po dónde están las palabras a traducir al español. 

### Antes de comenzar el proyecto se debe:

* Crear un archivo .env en la app del proyecto (donde esta la carpeta del settings).  
Copiar el contenido del env_template y pegarlo en el .env y completar  los datos. Tener en cuenta que no queden espacios entre la constante=dato. 
  * Para obtener la secret key usar el comando:
python -c 'from django.core.management.utils import get_random_secret_key; \print(get_random_secret_key())'


* Instalar requerimientos

pip install -r requirements.txt

* Correr las migraciones

python manage.py migrate

Hay 1 migracion para importar provincias y otra para ciudades de Argentina


### Grupos Productor 

python manage.py create_producer_group


### Administrador

python manage.py create_admin_group

### Personal
python manage.py create_staff_group


### Organizacion
python manage.py create_organization_group