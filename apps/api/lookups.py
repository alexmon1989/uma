from django.db.models import Lookup
from django.db.models.fields import Field


@Field.register_lookup
class FullTextContains(Lookup):
    lookup_name = 'contains_ft'

    def as_sql(self, compiler, connection):
        lhs, lhs_params = self.process_lhs(compiler, connection)
        rhs, rhs_params = self.process_rhs(compiler, connection)
        params = lhs_params + rhs_params
        return 'CONTAINS(%s, %s)' % (lhs, rhs), params
