from django.shortcuts import render
from django.db.models import Prefetch, Q
from django.views.generic.detail import DetailView
from .models import Help, Section, Question


def help_page(request):
    """Отображает страницу Помощь"""
    data, created = Help.objects.get_or_create()
    sections = Section.objects.filter(
        is_enabled=True
    ).order_by(
        '-weight'
    ).prefetch_related(
        Prefetch(
            'question_set',
            queryset=Question.objects.filter(is_enabled=True).order_by('-weight'))
    )
    lang = request.LANGUAGE_CODE
    return render(
        request,
        'help/index/index.html',
        {
            'title': getattr(data, f"title_{lang}"),
            'content': getattr(data, f"content_{lang}"),
            'sections': sections,
            'lang': lang,
        }
    )


class SectionDetailView(DetailView):
    """Отображает страницу раздела помощи."""
    model = Section
    template_name = 'help/section/section.html'

    def get_queryset(self):
        return Section.objects.filter(
            is_enabled=True
        ).prefetch_related(
            Prefetch(
                'question_set',
                queryset=Question.objects.filter(is_enabled=True).order_by('-weight'))
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['lang'] = self.request.LANGUAGE_CODE
        context['sections'] = Section.objects.filter(
            is_enabled=True
        ).order_by(
            '-weight'
        ).prefetch_related(
            Prefetch(
                'question_set',
                queryset=Question.objects.filter(is_enabled=True).order_by('-weight'))
        )
        return context


class QuestionDetailView(DetailView):
    """Отображает страницу вопроса."""
    model = Question
    template_name = 'help/question/question.html'

    def get_queryset(self):
        return Question.objects.filter(is_enabled=True)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['lang'] = self.request.LANGUAGE_CODE
        context['sections'] = Section.objects.filter(
            is_enabled=True
        ).order_by(
            '-weight'
        ).prefetch_related(
            Prefetch(
                'question_set',
                queryset=Question.objects.filter(is_enabled=True).order_by('-weight'))
        )
        return context


def search(request):
    """Производит поиск и отображает страницу с результатами."""
    results = None
    if request.GET.get('q'):
        results_title = Question.objects.filter(
            Q(title_en__icontains=request.GET['q'])
            | Q(title_uk__icontains=request.GET['q'])
        ).prefetch_related('section')
        results_content = Question.objects.filter(
            Q(content_en__icontains=request.GET['q'])
            | Q(content_uk__icontains=request.GET['q']),
        ).exclude(
            pk__in=results_title
        ).prefetch_related('section')
        # Запросы выполняются отдельно и объединяются.
        # Таким образом в начале результ. списка окажутся результаты, содержащие поисковый запрос в заголовке
        results = list(results_title)
        results.extend(list(results_content))

    return render(
        request,
        'help/search/search.html',
        {
            'q': request.GET.get('q', ''),
            'results': results,
            'lang': request.LANGUAGE_CODE,
        }
    )
