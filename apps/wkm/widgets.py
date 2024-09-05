from django.contrib.admin.widgets import AdminSplitDateTime


class MyAdminSplitDateTime(AdminSplitDateTime):
    """
    Кастомний віджет дати та часу, у якому не відображається поле часу.
    Використовуєтсья для того, щоб у адмін-панелі поля DateTimeField виглядали як DateField
    """
    template_name = "wkm/widgets/split_datetime.html"
