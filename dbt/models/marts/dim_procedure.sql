select procedure_code, procedure_libelle, avec_publicite, ordre
from {{ ref('procedures') }}
