from django.core.management.base import BaseCommand

from apps.search.services.st_37_dossier import (
    St37DossierCreatorService, St37XMLFileCreator, St37DocumentsRepository, St37CoverageCalculator
)


class Command(BaseCommand):

    def handle(self, *args, **options):
        service = St37DossierCreatorService(
            repository=St37DocumentsRepository(),
            coverage_calculator=St37CoverageCalculator(),
            file_creator=St37XMLFileCreator()
        )
        service.execute()

        self.stdout.write(self.style.SUCCESS('Finished'))
