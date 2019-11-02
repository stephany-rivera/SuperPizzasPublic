### Para correr se debe tener las siguientes librerias
- Django
- django-tenants
- psycopg2
- django-bootstrap4
- django-role-permissions
- django-tenant-schemas
- *(usar **`pip install -r requirements.txt`** para ello)*

### Dentro del proyecto hacer
- `python manage.py makemigrations` (solo si se cambian modelos)
- **`python manage.py migrate_schemas --shared`**
- **`python manage.py createsuperuser`** (para administrar franquicias)

### Correr los siguientes scripts SQL dentro de la base de datos
```SQL
INSERT INTO "franquicias_tipofranquicia" ("nombre","precio") VALUES ('basico',79);
INSERT INTO "franquicias_tipofranquicia" ("nombre","precio") VALUES ('premium',135);
INSERT INTO "franquicias_franquicia" ("schema_name", "nombre","fecha_corte","tipo_id") VALUES ('public', 'public',CURRENT_DATE,1);
INSERT INTO "franquicias_dominio" ("domain", "is_primary", "tenant_id") VALUES ('localhost', true, 1);
```