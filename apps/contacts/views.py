from django.views.generic import FormView
from django.http import HttpResponse
from .models import ContactsPage
from .forms import ContactForm


class ContactView(FormView):
    """Отображает страницу Контакты."""
    template_name = 'contacts/contacts.html'
    form_class = ContactForm

    def form_valid(self, form):
        # This method is called when valid form data has been POSTed.
        # It should return an HttpResponse.
        form.send_email()
        return HttpResponse(status=200)

    def form_invalid(self, form):
        response = HttpResponse()
        response.status_code = 400
        return response

    def get_context_data(self, **kwargs):
        context = super(ContactView, self).get_context_data(**kwargs)
        context['data'], created = ContactsPage.objects.get_or_create()
        context['lang_code'] = self.request.LANGUAGE_CODE
        context['title'] = getattr(context['data'], f"title_{context['lang_code']}")
        context['content'] = getattr(context['data'], f"content_{context['lang_code']}")
        context['operating_mode'] = getattr(context['data'], f"operating_mode_{context['lang_code']}")
        context['lunch_break'] = getattr(context['data'], f"lunch_break_{context['lang_code']}")
        return context
