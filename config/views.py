from django.views.generic import TemplateView


class TermsView(TemplateView):
    """Render the Terms and Conditions page."""
    template_name = 'legal/terms.html'


class PrivacyView(TemplateView):
    """Render the Privacy Policy page."""
    template_name = 'legal/privacy.html'
