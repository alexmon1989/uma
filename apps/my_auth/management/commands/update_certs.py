from django.core.management.base import BaseCommand, CommandError

from apps.my_auth.services import CertsUpdateService


class Command(BaseCommand):
    help = "Оновлює файли CAs.json та CACertificates.p7b з серверів ІІТ / ЦЗО."

    def add_arguments(self, parser):
        parser.add_argument(
            "--no-backup",
            action="store_true",
            help="Не створювати резервні копії (.bak) перед перезаписом файлів",
        )

    def handle(self, *args, **options):
        self.stdout.write("Початок оновлення кореневих сертифікатів та списку ЦСК...")

        service = CertsUpdateService()
        backup = not options.get("no_backup", False)
        result = service.update_certs(backup=backup)

        if result["success"]:
            source = result.get("source_used", "unknown")
            self.stdout.write(
                self.style.SUCCESS(
                    f"Успішно оновлено CAs.json та CACertificates.p7b із джерела '{source}'."
                )
            )
        else:
            errors = "; ".join(result.get("errors", []))
            raise CommandError(
                f"Не вдалося оновити сертифікати з жодного джерела. Помилки: {errors}"
            )

