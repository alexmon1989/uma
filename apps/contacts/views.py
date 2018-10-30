from django.shortcuts import render


def contacts(request):
    """Отображает страницу контактов."""
    return render(request, 'contacts/contacts.html')
