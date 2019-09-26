from collections import OrderedDict

from django.conf import settings
from django.db import models
from django.utils import translation
from django.utils.functional import cached_property
from django.utils.translation import ugettext_lazy as _
from wagtail.admin.edit_handlers import PageChooserPanel
from wagtail.core.models import Page

# should be added to your configuration / settings.py
OUR_I18N_METADATA = {
    # iso15897 uses "_DE" because Facebook does not recognize _AT. And we have to use
    # opengraph metatags
    "de": {"display_name": "Deutsch", "flag_code": "at", "iso15897": "de_DE"},
    "en": {"display_name": "English", "flag_code": "gb", "iso15897": "en_US"},
}


class TranslatablePageMixin(models.Model):
    """Mixin for translatable pages""""
    # One link for each alternative language
    # These should only be used on the main language page (german)
    english_link = models.ForeignKey(
        Page,
        null=True,
        on_delete=models.SET_NULL,
        blank=True,
        related_name="+",
        help_text=_(
            "IMPORTANT! Only choose a page here if this is a main language page!"
        ),
    )

    panels = [PageChooserPanel("english_link")]

    @cached_property
    def i18n_pages(self) -> OrderedDict:
        """Outputs all the translated pages for this page and some useful infos.

        Returns:
            OrderedDict: An ordered dictionary, where the languages are sorted
                alphabetically. It looks like this::

                {
                    "de": {
                        "page": <Page instance german>,
                        "url": "/de/meine-seite",
                        "display_name": "Deutsch",
                        "is_active": False,
                    },
                    "en": {
                        # ...
                    }
                }
        """
        # keep languages sorted alphabetically.
        languages = sorted(
            [("de", self.get_german_page()), ("en", self.get_english_page())],
            key=lambda x: x[0],
        )
        pages = OrderedDict(languages)
        i18n: OrderedDict = OrderedDict()
        for lang_code, page in pages.items():
            lang_data = {}
            lang_data["page"] = page
            lang_data["url"] = None
            if page:
                lang_data["url"] = page.get_url()
            lang_data["is_active"] = translation.get_language() == lang_code
            lang_data.update(settings.OUR_I18N_METADATA[lang_code])
            i18n[lang_code] = lang_data
        return i18n

    def get_context(self, request):
        context = super().get_context(request)
        context["i18n_pages"] = self.i18n_pages
        # no translation means that we have no URLs or only a single one to redirect
        # to.
        context["i18n_pages_no_translation"] = (
            len([trans["url"] for trans in self.i18n_pages.values() if trans["url"]])
            <= 1
        )
        return context

    def get_language(self):
        """This returns the language code for this page."""
        # Look through ancestors of this page for its language homepage
        # The language homepage is located at depth 3
        language_homepage = self.get_ancestors(inclusive=True).get(depth=3)
        # The slug of language homepages should always be set to the language code
        return language_homepage.slug

    def get_german_page(self):
        """returns the german version of this page"""
        language = self.get_language()

        if language == "de":
            return self
        elif language == "en":
            german_page = type(self).objects.filter(english_link=self).first()
            if german_page:
                return german_page.specific
        return None

    def get_english_page(self):
        """returns the english version of this page"""
        german_page = self.get_german_page()

        if german_page and german_page.english_link:
            return german_page.english_link.specific
        return None

    class Meta:
        abstract = True

