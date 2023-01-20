from django.views.generic.base import TemplateView


class AboutAuthorPage(TemplateView):
    template_name = 'about/author.html'


class AboutTechPage(TemplateView):
    template_name = 'about/tech.html'
