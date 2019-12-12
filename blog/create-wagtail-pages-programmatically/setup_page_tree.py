import json
import logging
from pathlib import Path

import faker
from django.apps import apps
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files import File
from django.core.management.base import BaseCommand
from faker.providers import date_time, lorem
from wagtail.core.models import Page
from wagtail.images.models import Image

User = get_user_model()

APP_DIR = Path(__file__).resolve().parent.parent.parent
FIXTURES_DIR = APP_DIR.joinpath("fixtures")

logger = logging.getLogger("setup_page_tree")

german_fake = faker.Faker("de_DE")
german_fake.add_provider(lorem)
german_fake.add_provider(date_time)


class Command(BaseCommand):
    """
    this command is used to create the initial wagtail cms page tree
    """

    help = "creates initial wagtail cms page tree"
    requires_system_checks = False

    def _setup(self):
        self._setup_language_redirection()
        self._setup_home()
        self._setup_default_pages()
        self._setup_contact_page()
        self._setup_service_overview_page()
        self._setup_project_index()
        self._setup_project_pages()
        self._setup_team_member_index()
        self._setup_team_member_pages()
        # finally, create the menus
        self._create_main_menu()
        self._create_flat_menus()

    def _set_image(self, obj, attr_name, folder_path, img_path):
        """helper to set images for objects"""
        img_path = folder_path.joinpath(img_path)
        # create and set the file if it does not yet exist
        qs = Image.objects.filter(title=img_path.name)
        if not qs.exists():
            with open(img_path, "rb") as f:
                # setting name= is important. otherwise it uses the entire file path as
                # name, which leaks server filesystem structure to the outside.
                image_file = File(f, name=img_path.stem)
                image = Image(title=img_path.name, file=image_file.open())
                image.save()
        else:
            image = qs[0]
        setattr(obj, attr_name, image)
        obj.save()

    def _setup_language_redirection(self):
        """First things first, tear down the dummy root page.

        and setup our language_redirection page
        """
        ContentType = apps.get_model("contenttypes.ContentType")
        Page = apps.get_model("wagtailcore.Page")
        Site = apps.get_model("wagtailcore.Site")
        LanguageRedirectionPage = apps.get_model("cms.LanguageRedirectionPage")
        # Delete the default homepage created by wagtail migrations If migration is run
        # multiple times, it may have already been deleted
        Page.objects.filter(id=2).delete()
        # Get content type for LanguageRedirectionPage model
        language_redirection_page_content_type = ContentType.objects.get(
            model="languageredirectionpage", app_label="cms"
        )
        # Create the base language redirection page which is responsible to redirect
        # the user to the language specific home pages
        root = Page.get_first_root_node()
        language_redirection_page = LanguageRedirectionPage(
            title="codista.com",
            draft_title="codista.com",
            slug="root",
            content_type=language_redirection_page_content_type,
            show_in_menus=True
        )
        root.add_child(instance=language_redirection_page)
        # Create a site with the new LanguageRedirectionPage set as the root
        Site.objects.create(
            hostname="localhost",
            root_page=language_redirection_page,
            is_default_site=True,
            site_name="codista.com",
        )

    def _setup_home(self):
        """Creates the language specific home pages."""
        LanguageRedirectionPage = apps.get_model("cms.LanguageRedirectionPage")
        parent_page = LanguageRedirectionPage.objects.first()
        ContentType = apps.get_model("contenttypes.ContentType")
        HomePage = apps.get_model("cms.HomePage")
        homepage_content_type = ContentType.objects.get(
            model="homepage", app_label="cms"
        )
        # For each supported language, create a new homepage
        for language_code, label in settings.LANGUAGES:
            if language_code == "de":
                hero_title = "Wir sind Codista."
                hero_intro = "Eine Software-Agentur, die sich auf die partnerschaftliche Entwicklung von hochqualitativen, digitalen Produkten spezialisiert hat."
                title = "Home - Deutsch"
                services_teaser = "Wir sind spezialisiert auf die Entwicklung von innovativen Software-Lösungen.  Mit langjähriger Erfahrung in Entwicklung und Design von Websites, Online-Plattformen,  Web-Applikationen und SaaS Lösungen unterstützen wir Ihr Unternehmen in der Realisierung neuer Software-Produkte und der Verbesserung Ihrer Unternehmens-Prozesse."
                services_title = "Wir denken digital."
                team_teaser = "Wir sind ein eingespieltes Team aus Software-Entwicklungs Experten und Design Profis welches komplexe Web-Projekte für unsere Kunden realisiert. Wir stehen für Qualität, Innovation, Umsetzungsgeschwindigkeit, Zuverlässigkeit und lösungsorientiertes Handeln."
                team_title = "Wir sind ein eingespieltes Team aus Software-Entwicklungs Experten und Design Profis."
                team_teaser = "Wir stehen für Qualität, Innovation, Umsetzungsgeschwindigkeit, Zuverlässigkeit und lösungsorientiertes Handeln."
            elif language_code == "en":
                title = "Home - English"
                hero_title = "We are Codista."
                hero_intro = "A software agency specializing in the partnership development of high quality digital products."
                services_teaser = "We specialize in the development of innovative software solutions. With many years of experience in the development and design of websites, online platforms, web applications and SaaS solutions, we support your company in the realization of new software products and the improvement of your business processes."
                services_title = "We think digitally."
                team_title = "We are a well-established team of software development experts and design professionals."
                team_teaser = "We stand for quality, innovation, speed of implementation, reliability and solution-oriented action."
            else:
                raise RuntimeError(f"unsupported language encountered: {language_code}")
            homepage = HomePage(
                language=language_code,
                title=title,
                draft_title=title,
                slug=language_code,
                hero_title=hero_title,
                hero_intro=hero_intro,
                services_teaser=services_teaser,
                services_title=services_title,
                team_title=team_title,
                team_teaser=team_teaser,
                show_in_menus=True,
                content_type=homepage_content_type,
            )
            parent_page.add_child(instance=homepage)

    def _setup_default_pages(self):
        # Get models
        ContentType = apps.get_model("contenttypes.ContentType")

        HomePage = apps.get_model("cms.HomePage")
        DefaultPage = apps.get_model("cms.DefaultPage")
        PrivacyPolicyPage = apps.get_model("cms.PrivacyPolicyPage")
        defaultpage_content_type, __ = ContentType.objects.get_or_create(
            model="defaultpage", app_label="cms"
        )
        privacypolicypage_content_type, __ = ContentType.objects.get_or_create(
            model="privacypolicypage", app_label="cms"
        )

        home_page_de = HomePage.objects.get(language="de")
        home_page_en = HomePage.objects.get(language="en")

        # setup imprint page
        blocks_de = [
            {
                "type": "paragraph",
                "value": "<h3>Informationspflicht laut §5 E-Commerce Gesetz, §14 Unternehmensgesetzbuch, und Offenlegungspflicht laut §25 Mediengesetz</h3>",
            },
            {
                "type": "paragraph",
                "value": "<p>Firmenwortlaut: Simpleloop Technologies GmbH & Co. KG<br/>Unternehmensgegenstand: Software-Entwicklung<br/>UID-Nummer: ATU70408427<br/>Firmenbuchnummer: FN 447839 m<br/>Firmenbuchgericht: Handelsgericht Wien<br/>Firmensitz: 1050 Wien</p>",
            },
            {"type": "paragraph", "value": "<h2>Kontaktdaten</h2>"},
            {
                "type": "paragraph",
                "value": "<p>Franzensgasse 25/15, 1050 Wien, Österreich<br/>Tel.: +43 1 997 425 61 00<br/>E-Mail: <a href='mailto:hello@codista.com'>hello@codista.com</a><br/>Geschäftsführer: Thomas Kremmel<p>",
            },
            {
                "type": "paragraph",
                "value": "<p>Mitgliedschaften/Aufsichtsbehörde: Derzeit liegen keine Mitgliedschaften vor.</p>",
            },
            {
                "type": "paragraph",
                "value": "<p>Angaben zur Online-Streitbeilegung: Verbraucher haben die Möglichkeit, Beschwerden an die Online Streitbeilegungsplattform der EU zu richten: <a href=\\'http://ec.europa.eu\\'>http://ec.europa.eu</a>, oder Sie können allfällige Beschwerden auch an die oben angegebene E-Mail-Adresse richten.</p>",
            },
        ]
        imprint_page_de = DefaultPage(
            title="Impressum",
            draft_title="Impressum",
            slug="impressum",
            hero_title="Impressum",
            body=json.dumps(blocks_de),
            show_in_menus=True,
            content_type=defaultpage_content_type,
        )
        home_page_de.add_child(instance=imprint_page_de)

        # setup imprint page
        blocks_en = [
            {
                "type": "paragraph",
                "value": "<h3>Information obligation according to §5 E-Commerce Law, §14 Corporate Code, and disclosure obligation according to §25 Media Act</h3>",
            },
            {
                "type": "paragraph",
                "value": "<p>Company name: Simpleloop Technologies GmbH & Co. KG <br/> Corporate object: Software development <br/> VAT number: ATU70408427 <br/> Commercial register number: FN 447839 m <br/> Commercial register court: Handelsgericht Wien <br/> Registered office: 1050 Vienna</p>",
            },
            {"type": "paragraph", "value": "<h2>Contact details</h2>"},
            {
                "type": "paragraph",
                "value": "<p>Franzensgasse 25/15, 1050 Vienna, Austria Phone: +43 1 997 425 61 00 <br/> E-mail: <a href='mailto:hello@codista.com'>hello@codista.com </a> <br/> Managing Director: Thomas Kremmel<p>",
            },
            {
                "type": "paragraph",
                "value": "<p>Memberships / Supervisory Authority: Currently there are no memberships.</p>",
            },
            {
                "type": "paragraph",
                "value": "<p>Information on online dispute resolution: Consumers have the opportunity to submit complaints to the EU's online dispute resolution platform: <a href=\\'http://ec.europa.eu\\> http://ec.europa.eu </a>, or you can also address any complaints to the above e-mail address.</p>",
            },
        ]
        imprint_page_en = DefaultPage(
            title="Imprint",
            draft_title="Imprint",
            slug="imprint",
            hero_title="Imprint",
            body=json.dumps(blocks_en),
            show_in_menus=True,
            content_type=defaultpage_content_type,
        )
        home_page_en.add_child(instance=imprint_page_en)
        # connect these pages for translation
        home_page_de.english_link = home_page_en
        home_page_de.save()

        terms_page_de = DefaultPage(
            title="AGB",
            draft_title="AGB",
            slug="agb",
            hero_title="AGB",
            show_in_menus=True,
            content_type=defaultpage_content_type,
        )
        home_page_de.add_child(instance=terms_page_de)

        terms_page_en = DefaultPage(
            title="Terms",
            draft_title="Terms",
            slug="terms",
            hero_title="Terms",
            show_in_menus=True,
            content_type=defaultpage_content_type,
        )
        home_page_en.add_child(instance=terms_page_en)

        # connect these pages for translation
        terms_page_de.english_link = terms_page_en
        terms_page_de.save()

        # setup privacy policy page
        blocks_de = [
            {"type": "paragraph", "value": "<h3>Datenschutz-Bestimmungen</h3>"},
            {
                "type": "paragraph",
                "value": "<p>Die Codista GmbH & Co. KG betreibt diese Website (https://www.codista.com). Diese Seite informiert Sie über unsere Datenschutzrichtlinien in Bezug auf die Erfassung, Verwendung und Weitergabe persönlicher Informationen, die wir von Benutzern der Website erhalten.</p>",
            },
            {
                "type": "paragraph",
                "value": "<h2>Cookies</h2><p>Wir respektieren Ihr Recht auf Privatsphäre. Diese Website verwendet daher keine Cookies.</p>",
            },
            {"type": "paragraph", "value": "<h2>Hosting</h2><p>TODO</p>"},
            {
                "type": "paragraph",
                "value": "<h2>Analytics</h2><p>Diese Website <strong>verwendet</strong> weder Google Analytics noch einen anderen Nutzeranalysedienst.</p>",
            },
            {
                "type": "paragraph",
                "value": "<h2>An uns gesendete E-Mails</h2> <p>Wenn Sie uns per E-Mail kontaktieren werden Ihre Nachricht und die damit verbundenen Daten gespeichert. Wir werden diese Informationen verwenden, um Ihre Anfrage zu bearbeiten und mögliche Folge-E-Mails zu bearbeiten. Diese Informationen werden ohne Ihre ausdrückliche Zustimmung nicht weitergegeben.</p>",
            },
            {
                "type": "paragraph",
                "value": "<h2> Ihre Datenschutzrechte</h2><p>Sie haben das Recht auf Offenlegung, Korrektur, Löschung, Beschränkung, Übertragung, Widerruf und Widerspruch. Wenn Sie der Meinung sind, dass unsere Verwendung Ihrer Daten gegen die Datenschutzgrundverordnung (DSGVO) verstößt oder dass Ihre Daten anderweitig falsch behandelt werden, kontaktieren Sie uns bitte.</p><p>Sie können dies direkt über unseren eigenen Ansprechpartner tun Informationen weiter unten oder wenden Sie sich an die zuständige Datenschutzbehörde.</p>",
            },
        ]
        privacy_policy_page_de = PrivacyPolicyPage(
            title="Datenschutz-Bestimmungen",
            draft_title="Datenschutz-Bestimmungen",
            slug="datenschutz",
            hero_title="Datenschutz-Bestimmungen",
            body=json.dumps(blocks_de),
            show_in_menus=True,
            content_type=privacypolicypage_content_type,
        )
        home_page_de.add_child(instance=privacy_policy_page_de)

        # setup privacy policy page
        blocks_en = [
            {"type": "paragraph", "value": "<h3>Privacy Policy</h3>"},
            {
                "type": "paragraph",
                "value": "<p>Codista GmbH & Co. KG operates this site (https://www.codista.com). This page informs you of our privacy policies regarding the collection, use and disclosure of personal information we receive from users of the site.</p>",
            },
            {
                "type": "paragraph",
                "value": "<h2>Cookies</h2><p>We respect your right to privacy. This website does not use any cookies or track you in any other way.</p>",
            },
            {"type": "paragraph", "value": "<h2>Hosting</h2><p>TODO</p>"},
            {
                "type": "paragraph",
                "value": "<h2>Analytics</h2><p>This website does <strong>not</strong> use Google Analytics or any other user analytics service. No third-party tracking scripts are included.</p>",
            },
            {
                "type": "paragraph",
                "value": "<h2>Emails sent to us</h2><p>Should you choose to contact us via email, either through this site's contact form or by emailing us from your own client, your message and associated data will be stored. We will use this information to process your request and handle possible follow-up emails. We will not share this information without your explicit consent.</p>",
            },
            {
                "type": "paragraph",
                "value": "<h2>Your privacy rights</h2><p>You have the right to disclosure, correction, deletion, limitation, transfer, revocation and oppositon. If you believe our use of your data is in violation of the General Data Protection Regulation (GDPR), or feel your data is handled incorrectly otherwise, please contact us.</p><p>You can do this directly using our own contact information below, or turn to the responsible data protection authority.</p>",
            },
        ]

        privacy_policy_page_en = PrivacyPolicyPage(
            title="Privacy Policy",
            draft_title="Privacy Policy",
            slug="privacy-policy",
            hero_title="Privacy Policy",
            body=json.dumps(blocks_en),
            show_in_menus=True,
            content_type=privacypolicypage_content_type,
        )
        home_page_en.add_child(instance=privacy_policy_page_en)

        # connect these pages for translation
        privacy_policy_page_de.english_link = privacy_policy_page_en
        privacy_policy_page_de.save()

    def _setup_contact_page(self):
        """Creates the contact page."""
        HomePage = apps.get_model("cms.HomePage")
        ContactPage = apps.get_model("cms.ContactPage")
        ContentType = apps.get_model("contenttypes.ContentType")
        contact_page_content_type = ContentType.objects.get(
            model="contactpage", app_label="cms"
        )
        home_page_de = HomePage.objects.get(language="de")
        contact_page_de = ContactPage(
            title="Kontakt",
            draft_title="Kontakt",
            slug="kontakt",
            hero_title="Los gehts.",
            hero_intro="Wir sind immer auf der Suche nach neuen Ideen und spannenden Projekten. Sagen Sie Hallo.",
            phone_number="+43 1 997 425 61 00",
            email="hello@codista.com",
            show_in_menus=True,
            content_type=contact_page_content_type,
        )
        home_page_de.add_child(instance=contact_page_de)
        home_page_en = HomePage.objects.get(language="en")
        contact_page_en = ContactPage(
            title="Contact",
            draft_title="Contact",
            slug="contact",
            hero_title="Lets go.",
            hero_intro="We are always on the hunt for new projects and interesting ideas! Say Hello.",
            phone_number="+43 1 997 425 61 00",
            email="hello@codista.com",
            show_in_menus=True,
            content_type=contact_page_content_type,
        )
        home_page_en.add_child(instance=contact_page_en)

        # connect these pages for translation
        contact_page_de.english_link = contact_page_en
        contact_page_de.save()

    def _setup_service_overview_page(self):
        """Creates the service overview page."""
        HomePage = apps.get_model("cms.HomePage")
        ServiceOverviewPage = apps.get_model("cms.ServiceOverviewPage")
        ContentType = apps.get_model("contenttypes.ContentType")
        serviceoverview_content_type = ContentType.objects.get(
            model="serviceoverviewpage", app_label="cms"
        )
        home_page_de = HomePage.objects.get(language="de")
        services_column_one = "Wir setzen Ihre Idee und Vision in die Realität um. Wir unterstützen Ihr Team Schritt für Schritt bei der Umsetzung Ihrer Idee."
        services_column_two = "Wir hinterfragen und beraten. Durch unsere Erfahrung können wir Sie dabei unterstützen, die Fehler, die Ihre Konkurrenz machen wird, zu vermeiden."
        services_column_three = "Wir sind hier, um Ihr Team und Ihr digitales Produkt im täglichen Betrieb zu unterstützen. Die Reise hat gerade nach dem Launch Ihres digitalen Produkts erst begonnen."
        clients_column_one = "Wir arbeiten eng mit Beratungs- und Innovationsagenturen zusammen. In langfristigen Partnerschaften unterstützen wir sie bei der Implementierung von Content-Management-Systemen, Online-Plattformen und Websites."
        clients_column_two = "Als Expertenteam das sich frei von Unternehmenszwängen bewegen kann, sind wir in der Lage, Ihre Digitalisierungsprojekte schnell und unkompliziert umzusetzen."
        clients_column_three = "Wir sind sehr erfahren im Verstehen, Analysieren, Hinterfragen und Umsetzen von Visionen. Wir unterstützen Gründer bei der Umsetzung ihrer Vision mit unserer technischen Expertise."

        service_overview_page_de = ServiceOverviewPage(
            title="Leistungen",
            draft_title="Leistungen",
            slug="leistungen",
            services_column_one=services_column_one,
            services_column_two=services_column_two,
            services_column_three=services_column_three,
            clients_column_one=clients_column_one,
            clients_column_two=clients_column_two,
            clients_column_three=clients_column_three,
            show_in_menus=True,
            content_type=serviceoverview_content_type,
        )
        home_page_de.add_child(instance=service_overview_page_de)

        home_page_en = HomePage.objects.get(language="en")
        services_column_one = "We turn your idea and vision into reality. We support your team step by step in the implementation of your idea."
        services_column_two = "We question and advise. Through our experience, we can help you avoid the mistakes that your competition will make."
        services_column_three = "We are here to support your team and your digital product in daily operations. The journey has just begun after the launch of your digital product."
        clients_column_one = "We work closely with consulting and innovation agencies. In long-term partnerships, we support them in the implementation of content management systems, online platforms and websites."
        clients_column_two = "As a team of experts that can move freely from corporate constraints, we are able to implement your digitization projects quickly and easily."
        clients_column_three = "We are very experienced in understanding, analyzing, questioning and implementing visions. We assist founders in implementing their vision with our technical expertise."
        service_overview_page_en = ServiceOverviewPage(
            title="Services",
            draft_title="Services",
            slug="services",
            services_column_one=services_column_one,
            services_column_two=services_column_two,
            services_column_three=services_column_three,
            clients_column_one=clients_column_one,
            clients_column_two=clients_column_two,
            clients_column_three=clients_column_three,
            show_in_menus=True,
            content_type=serviceoverview_content_type,
        )
        home_page_en.add_child(instance=service_overview_page_en)

        # connect these pages for translation
        service_overview_page_de.english_link = service_overview_page_en
        service_overview_page_de.save()

    def _setup_project_index(self):
        """Creates the language specific project index pages."""
        HomePage = apps.get_model("cms.HomePage")
        ProjectIndexPage = apps.get_model("cms.ProjectIndexPage")
        ContentType = apps.get_model("contenttypes.ContentType")
        project_index_page_content_type = ContentType.objects.get(
            model="projectindexpage", app_label="cms"
        )
        home_page_de = HomePage.objects.get(language="de")
        project_index_de = ProjectIndexPage(
            title="Projekte",
            draft_title="Projekte",
            slug="projekte",
            hero_title="Unsere Projekte",
            show_in_menus=True,
            content_type=project_index_page_content_type,
        )
        home_page_de.add_child(instance=project_index_de)
        home_page_en = HomePage.objects.get(language="en")
        project_index_en = ProjectIndexPage(
            title="Projects",
            draft_title="Projects",
            slug="projects",
            hero_title="Our projects",
            show_in_menus=True,
            content_type=project_index_page_content_type,
        )
        home_page_en.add_child(instance=project_index_en)

        # connect these pages for translation
        project_index_de.english_link = project_index_en
        project_index_de.save()

    def _setup_project_pages(self):
        """Creates the language specific project pages."""
        HomePage = apps.get_model("cms.HomePage")
        ProjectPage = apps.get_model("cms.ProjectPage")
        ProjectIndexPage = apps.get_model("cms.ProjectIndexPage")
        ContentType = apps.get_model("contenttypes.ContentType")

        home_page_de = HomePage.objects.get(language="de")
        home_page_en = HomePage.objects.get(language="en")
        project_index_page_de = ProjectIndexPage.objects.descendant_of(
            home_page_de
        ).first()
        project_index_page_en = ProjectIndexPage.objects.descendant_of(
            home_page_en
        ).first()

        project_page_content_type = ContentType.objects.get(
            model="projectpage", app_label="cms"
        )
        folder_path = FIXTURES_DIR.joinpath("img")

        # create story.one project
        story_one_de = ProjectPage(
            title="story.one",
            draft_title="story.one",
            slug="story-one",
            hero_title="story.one",
            project_url="www.story.one",
            hero_intro="Für die Unternehmer Hannes Steiner, Martin Blank und Matthias Strolz entwickelten wir die Online-Plattform story.one. Auf story.one kann man wahre Geschichten schreiben, teilen und lesen.",
            teaser_title="Zeit für Geschichten",
            client="Storylution GmbH",
            services="UI/UX Design, Frontend Development, Backend Development, System-Architektur, Consulting, Betrieb",
            tech="HTML/CSS, Wagtail, React, Postgres, Django",
            content_type=project_page_content_type,
        )
        project_index_page_de.add_child(instance=story_one_de)

        story_one_en = ProjectPage(
            title="story.one",
            draft_title="story.one",
            slug="story-one",
            hero_title="story.one",
            project_url="www.story.one",
            hero_intro="We developed the online-platform story.one for the entrepreneurs Hannes Steiner, Martin Blank an Matthias Strolz. story.one is a place to share real stories online, connect with other users, and publish books.",
            teaser_title="Time for storys",
            client="Storylution GmbH",
            services="UI/UX design, frontend development, backend development, system architectur, consulting, operations",
            tech="HTML/CSS, Wagtail, React, Postgres, Django",
            content_type=project_page_content_type,
        )
        project_index_page_en.add_child(instance=story_one_en)
        story_one_de.english_link = story_one_en
        story_one_de.save()

        # create onboard project
        onboard_de = ProjectPage(
            title="onboardcommunity.com",
            draft_title="onboardcommunity.com",
            slug="austrian-airlines-onboardcommunity",
            hero_title="onboardcommunity.com",
            project_url="onboardcommunity.com",
            hero_intro="Für die Austrian Airlines / Lufthansa Gruppe entwickelten wir eine Online-Community. Responsive Umsetzung, Gamification und Erreichbarkeit über das In-Flight WLAN waren Herausforderungen die zu meistern waren.",
            teaser_title="Community über den Wolken",
            client="Austrian Airlines",
            services="UI/UX Design, Frontend Development, Backend Development, System-Architektur, Consulting, Betrieb",
            tech="HTML/CSS, Wagtail, React, Postgres, Django",
            content_type=project_page_content_type,
        )
        project_index_page_de.add_child(instance=onboard_de)

        onboard_en = ProjectPage(
            title="onboardcommunity.com",
            draft_title="onboardcommunity.com",
            slug="austrian-airlines-onboardcommunity",
            hero_title="onboardcommunity.com",
            project_url="onboardcommunity.com",
            hero_intro="We developed an online-community for Austrian Airlines and the Lufthansa Gruppe. Responsive setup, Gamification and accessability via the in-flight WLAN have been successfully mastered challenges.",
            teaser_title="Community above the skys",
            client="Austrian Airlines",
            services="UI/UX design, frontend development, backend development, system architectur, consulting, operations",
            tech="HTML/CSS, Wagtail, React, Postgres, Django",
            content_type=project_page_content_type,
        )
        project_index_page_en.add_child(instance=onboard_en)
        onboard_de.english_link = onboard_en
        onboard_de.save()

        # create cleanvest project
        cleanvest_de = ProjectPage(
            title="cleanvest.org",
            draft_title="cleanvest.org",
            slug="cleanvest-nachhaltige-investments",
            hero_title="cleanvest.org",
            project_url="cleanvest.org",
            hero_intro="Für die Auftraggeber esgplus entwickelten wir die Website www.cleanvest.org. Auf dieser Website werden Investments nach deren Nachhaltigkeit bewertet.",
            teaser_title="Nachhaltig investieren",
            client="ESG Plus",
            services="UI/UX Design, Frontend Development, Backend Development, System-Architektur, Consulting, Betrieb",
            tech="HTML/CSS, Wagtail, React, Postgres, Django",
            content_type=project_page_content_type,
        )
        project_index_page_de.add_child(instance=cleanvest_de)

        cleanvest_en = ProjectPage(
            title="cleanvest.org",
            draft_title="cleanvest.org",
            slug="cleanvest-nachhaltige-investments",
            hero_title="cleanvest.org",
            project_url="cleanvest.org",
            hero_intro="For our customer esgplus we developed the website www.cleanvest.org. This website allows users to get informed about sustainable investments.",
            teaser_title="invest sustainably",
            client="ESG Plus",
            services="UI/UX design, frontend development, backend development, system architectur, consulting, operations",
            tech="HTML/CSS, Wagtail, React, Postgres, Django",
            content_type=project_page_content_type,
        )
        project_index_page_en.add_child(instance=cleanvest_en)
        cleanvest_de.english_link = cleanvest_en
        cleanvest_de.save()

        # create austrian blog project
        austrian_blog_de = ProjectPage(
            title="austrianblog.at",
            draft_title="austrianblog.at",
            slug="austrian-blog-cms-entwicklung",
            hero_title="austrianblog.at",
            project_url="austrianblog.at",
            hero_intro="Wir sind stolz darauf den offiziellen Austrian Airlines Blog entwickelt zu haben und zu betreiben. Ein CMS mit hoher Usability zu entwickeln um die Content-Editoren in ihrer täglichen Arbeit zu unterstützen war unser Ziel.",
            teaser_title="Servus, Welt!",
            client="Austrian Airlines",
            services="UI/UX Design, Frontend Development, Backend Development, System-Architektur, Consulting, Betrieb",
            tech="HTML/CSS, Wagtail, React, Postgres, Django",
            content_type=project_page_content_type,
        )
        project_index_page_de.add_child(instance=austrian_blog_de)

        austrian_blog_en = ProjectPage(
            title="austrianblog.at",
            draft_title="austrianblog.at",
            slug="austrian-blog-cms-development",
            hero_title="austrianblog.at",
            project_url="austrianblog.at",
            hero_intro="For our customer Austrian Airlines we developed the official company blog. Our goal have been to develop a CMS with high usability to support the content editors in their daily work.",
            teaser_title="Servus, World!",
            client="Austrian Airlines",
            services="UI/UX design, frontend development, backend development, system architectur, consulting, operations",
            tech="HTML/CSS, Wagtail, React, Postgres, Django",
            content_type=project_page_content_type,
        )
        project_index_page_en.add_child(instance=austrian_blog_en)
        austrian_blog_de.english_link = austrian_blog_en
        austrian_blog_de.save()

        # create livv.at study
        livv_de = ProjectPage(
            title="livv.at",
            draft_title="livv.at",
            slug="livv-at-chat-bot-cms-entwicklung",
            hero_title="livv.at",
            project_url="livv.at",
            hero_intro="Für die LV1876, eine der größten Versicherungen Deutschlands, entwickelten wir die Online-Plattform www.livv.at. Auf livv.at kann man in einfacher Art und Weise online eine Versicherung abschließen. Ein innovativer Chat Bot führt durch den Abschlussprozess.",
            teaser_title="Lebensversicherung in digital.",
            client="LV 1871",
            services="UI/UX Design, Frontend Development, Backend Development, System-Architektur, Consulting, Betrieb",
            tech="HTML/CSS, Wagtail, React, Postgres, Django",
            content_type=project_page_content_type,
        )
        project_index_page_de.add_child(instance=livv_de)

        livv_en = ProjectPage(
            title="livv.at",
            draft_title="livv.at",
            slug="livv-at-chat-bot-cms-development",
            hero_title="livv.at",
            project_url="livv.at",
            hero_intro="For LV1876, one of the major german insurance companies we developed the website www.livv.at. Our goal was to develop a very simple and convenient process to buy an insurance online. Check out the livv.at chat bot to get an idea on how this idea evolved.",
            teaser_title="Digital Life Insurance.",
            client="LV 1871",
            services="UI/UX design, frontend development, backend development, system architectur, consulting, operations",
            tech="HTML/CSS, Wagtail, React, Postgres, Django",
            content_type=project_page_content_type,
        )
        project_index_page_en.add_child(instance=livv_en)
        livv_de.english_link = livv_en
        livv_de.save()

        # set home page featured project
        home_page_de.featured_project_one = story_one_de
        home_page_en.featured_project_one = story_one_en
        home_page_de.featured_project_two = onboard_de
        home_page_en.featured_project_two = onboard_en
        home_page_de.featured_project_three = cleanvest_de
        home_page_en.featured_project_three = cleanvest_en
        home_page_de.save()
        home_page_en.save()

    def _setup_team_member_index(self):
        """Creates the language specific team member index pages."""
        HomePage = apps.get_model("cms.HomePage")
        TeamMemberIndexPage = apps.get_model("cms.TeamMemberIndexPage")
        ContentType = apps.get_model("contenttypes.ContentType")
        team_member_index_page_content_type = ContentType.objects.get(
            model="teammemberindexpage", app_label="cms"
        )
        home_page_de = HomePage.objects.get(language="de")

        intro_de = "Wir sind eine Software-Agentur mit Sitz in Wien. Unser Büro ist in Gehweite zum Naschmarkt zu finden. Mit einem starken Fokus auf Innovation unterstützen wir Unternehmen bei der Entwicklung und Verbesserung digitaler Produkte."
        team_member_index_de = TeamMemberIndexPage(
            title="Team",
            draft_title="Team",
            slug="team",
            hero_title="Unser Team",
            hero_intro=intro_de,
            show_in_menus=True,
            content_type=team_member_index_page_content_type,
        )
        home_page_de.add_child(instance=team_member_index_de)
        home_page_en = HomePage.objects.get(language="en")

        intro_en = "We are a software agency based in Vienna. Our office is within walking distance to the Naschmarkt. With a strong focus on innovation, we help companies develop and enhance digital products."
        team_member_index_en = TeamMemberIndexPage(
            title="Team",
            draft_title="Team",
            slug="team",
            hero_title="Our team",
            hero_intro=intro_en,
            show_in_menus=True,
            content_type=team_member_index_page_content_type,
        )
        home_page_en.add_child(instance=team_member_index_en)

        # connect these pages for translation
        team_member_index_de.english_link = team_member_index_en
        team_member_index_de.save()

    def _setup_team_member_pages(self):
        """Creates the language specific team member pages."""
        HomePage = apps.get_model("cms.HomePage")
        TeamMemberPage = apps.get_model("cms.TeamMemberPage")
        TeamMemberIndexPage = apps.get_model("cms.TeamMemberIndexPage")
        ContentType = apps.get_model("contenttypes.ContentType")

        home_page_de = HomePage.objects.get(language="de")
        home_page_en = HomePage.objects.get(language="en")
        team_member_index_page_de = TeamMemberIndexPage.objects.descendant_of(
            home_page_de
        ).first()
        team_member_index_page_en = TeamMemberIndexPage.objects.descendant_of(
            home_page_en
        ).first()

        team_member_page_content_type = ContentType.objects.get(
            model="teammemberpage", app_label="cms"
        )

        about_de = "<p>Thomas ist Geschäftsführer von Codista. Er stellt sicher, dass unsere Kunden-Projekte in höchster Qualität und in der vereinbarten Zeit geliefert werden. Seine Arbeitszeit widmet er zu 70% der Software-Entwicklung und zu 30% dem Projektmanagement.</p>"
        team_member_tom_de = TeamMemberPage(
            title="Thomas Kremmel",
            draft_title="Thomas Kremmel",
            slug="thomas-kremmel",
            name="Mag. Thomas Kremmel",
            organisational_role="Geschäftsführer",
            about=about_de,
            content_type=team_member_page_content_type,
        )
        team_member_index_page_de.add_child(instance=team_member_tom_de)
        folder_path = FIXTURES_DIR.joinpath("img")
        self._set_image(
            obj=team_member_tom_de,
            attr_name="portrait",
            folder_path=folder_path,
            img_path="tom.jpg",
        )

        about_en = "<p>Thomas is CEO of Codista. He understands the technical and the business requirements of our customers and devotes 70% of his time to software development and 30% of this time to project management.</p>"
        team_member_tom_en = TeamMemberPage(
            title="Thomas Kremmel",
            draft_title="Thomas Kremmel",
            slug="thomas-kremmel",
            name="Mag. Thomas Kremmel",
            organisational_role="CEO",
            about=about_en,
            content_type=team_member_page_content_type,
        )
        team_member_index_page_en.add_child(instance=team_member_tom_en)
        team_member_tom_de.english_link = team_member_tom_en
        team_member_tom_de.save()
        self._set_image(
            obj=team_member_tom_en,
            attr_name="portrait",
            folder_path=folder_path,
            img_path="tom.jpg",
        )

        about_de = "<p>Luis ist Tech Lead von Codista. TODO: insert text here..  Seine Arbeitszeit widmet er hauptsächlich der Software Entwicklung, dem Server Setup und der Team Leitung.</p>"
        team_member_luis_de = TeamMemberPage(
            title="Luis Nell",
            draft_title="Luis Nell",
            slug="luis-nell",
            name="Luis Nell, BSc.",
            organisational_role="Tech Lead",
            about=about_de,
            content_type=team_member_page_content_type,
        )
        team_member_index_page_de.add_child(instance=team_member_luis_de)
        folder_path = FIXTURES_DIR.joinpath("img")
        self._set_image(
            obj=team_member_luis_de,
            attr_name="portrait",
            folder_path=folder_path,
            img_path="luis.jpg",
        )

        about_en = "<p>Luis is CTO of Codista. TODO: insert text here.. He is responsible for software engineering, server setup & operations, and he is team lead in some of our customer projects.</p>"
        team_member_luis_en = TeamMemberPage(
            title="Luis Nell",
            draft_title="Luis Nell",
            slug="luis-nell",
            name="Luis Nell, BSc.",
            organisational_role="CTO",
            about=about_en,
            content_type=team_member_page_content_type,
        )
        team_member_index_page_en.add_child(instance=team_member_luis_en)
        team_member_luis_de.english_link = team_member_luis_en
        team_member_luis_de.save()
        self._set_image(
            obj=team_member_luis_en,
            attr_name="portrait",
            folder_path=folder_path,
            img_path="luis.jpg",
        )

        about_de = "<p>TODO: insert text here.. Max bringt über zehn Jahre Erfahrung als Frontend-Entwickler und UX Designer mit. Seine Arbeitszeit widmet er hauptsächlich der Entwicklung von Web Frontends und UX Designs.</p>"
        team_member_max_de = TeamMemberPage(
            title="Max Böck",
            draft_title="Max Böck",
            slug="max-boeck",
            name="Max Böck, BSc.",
            organisational_role="Frontend Entwickler",
            about=about_de,
            content_type=team_member_page_content_type,
        )
        team_member_index_page_de.add_child(instance=team_member_max_de)
        folder_path = FIXTURES_DIR.joinpath("img")
        self._set_image(
            obj=team_member_max_de,
            attr_name="portrait",
            folder_path=folder_path,
            img_path="max.jpg",
        )

        about_en = "<p>TODO: insert text here.. Max has over ten years of experience working as a frontend-developer and UX designer. He is responsible for frontend development and UX design.</p>"
        team_member_max_en = TeamMemberPage(
            title="Max Böck",
            draft_title="Max Böck",
            slug="max-boeck",
            name="Max Böck, BSc.",
            organisational_role="Frontend Developer",
            about=about_en,
            content_type=team_member_page_content_type,
        )
        team_member_index_page_en.add_child(instance=team_member_max_en)
        self._set_image(
            obj=team_member_max_en,
            attr_name="portrait",
            folder_path=folder_path,
            img_path="max.jpg",
        )

        team_member_max_de.english_link = team_member_max_en
        team_member_max_de.save()

        about_de = "<p>Angela studiert Projekt Management und IT an der FH des BFI Wien und unterstützt uns als Projekt Management Trainee und QA Expertin.</p>"
        team_member_angela_de = TeamMemberPage(
            title="Angela Prinz",
            draft_title="Angela Prinz",
            slug="angela-prinz",
            name="Angela Prinz",
            organisational_role="Projektmanagement Trainee und QA Expertin",
            about=about_de,
            content_type=team_member_page_content_type,
        )
        team_member_index_page_de.add_child(instance=team_member_angela_de)
        folder_path = FIXTURES_DIR.joinpath("img")
        self._set_image(
            obj=team_member_angela_de,
            attr_name="portrait",
            folder_path=folder_path,
            img_path="angela.jpg",
        )

        about_en = "<p>Angela studies project management and IT at the FH BFI Vienna. Angela is QA expert and supports us in daily project management tasks.</p>"
        team_member_angela_en = TeamMemberPage(
            title="Angela Prinz",
            draft_title="Angela Prinz",
            slug="angela-prinz",
            name="Angela Prinz",
            organisational_role="Project Management Trainee and QA expert",
            about=about_en,
            content_type=team_member_page_content_type,
        )
        team_member_index_page_en.add_child(instance=team_member_angela_en)
        team_member_angela_de.english_link = team_member_angela_en
        team_member_angela_de.save()
        self._set_image(
            obj=team_member_angela_en,
            attr_name="portrait",
            folder_path=folder_path,
            img_path="angela.jpg",
        )

        about_de = "<p>Bernhard ist unser Sys-Admin. Er kümmert sich um operativen Server Support, DevOps und Setup von Continous Integration / Deployment Prozessen.</p>"
        team_member_bernhard_de = TeamMemberPage(
            title="Bernhard",
            draft_title="Bernhard",
            slug="bernhard",
            name="Bernhard",
            organisational_role="Sys Admin / DevOps",
            about=about_de,
            content_type=team_member_page_content_type,
        )
        team_member_index_page_de.add_child(instance=team_member_bernhard_de)
        folder_path = FIXTURES_DIR.joinpath("img")

        about_en = "<p>Bernhard is our Sys-Admin. He is responsible for server setup and operations, devOps and setup of Continous Integration / Deployment processes.</p>"
        team_member_bernhard_en = TeamMemberPage(
            title="Bernhard",
            draft_title="Bernhard",
            slug="bernhard",
            name="Bernhard",
            organisational_role="Sys Admin / DevOps",
            about=about_en,
            content_type=team_member_page_content_type,
        )
        team_member_index_page_en.add_child(instance=team_member_bernhard_en)
        team_member_bernhard_de.english_link = team_member_bernhard_en
        team_member_bernhard_de.save()

        team_member_index_page_de.team_member_one = team_member_tom_de
        team_member_index_page_de.team_member_two = team_member_luis_de
        team_member_index_page_de.team_member_three = team_member_max_de
        team_member_index_page_de.team_member_four = team_member_angela_de
        team_member_index_page_de.team_member_five = team_member_bernhard_de
        team_member_index_page_de.save()
        team_member_index_page_en.team_member_one = team_member_tom_en
        team_member_index_page_en.team_member_two = team_member_luis_en
        team_member_index_page_en.team_member_three = team_member_max_en
        team_member_index_page_en.team_member_four = team_member_angela_en
        team_member_index_page_en.team_member_five = team_member_bernhard_en
        team_member_index_page_en.save()

        TeamMemberPage.objects.all().update(live=False)

    def _create_main_menu(self):
        from wagtailmenus.conf import settings as wagtailmenu_settings
        from wagtail.core.models import Site

        HomePage = apps.get_model("cms.HomePage")
        ContactPage = apps.get_model("cms.ContactPage")
        ServiceOverviewPage = apps.get_model("cms.ServiceOverviewPage")
        ProjectIndexPage = apps.get_model("cms.ProjectIndexPage")
        TeamMemberIndexPage = apps.get_model("cms.TeamMemberIndexPage")
        site = Site.objects.all()[0]
        menu_model = wagtailmenu_settings.models.FLAT_MENU_MODEL

        # create the german footer
        main_menu_de, created = menu_model.objects.get_or_create(
            site=site, handle="main_menu_de", title="main_menu_de"
        )
        home_page_de = HomePage.objects.get(language="de")
        if not main_menu_de.get_menu_items_manager().exists():
            # create the menu items for each page needed
            item_manager = main_menu_de.get_menu_items_manager()
            item_class = item_manager.model
            item_list = []
            service_overview_page_de = ServiceOverviewPage.objects.descendant_of(
                home_page_de
            ).first()
            item_list.append(
                item_class(
                    menu=main_menu_de,
                    link_text="Leistungen",
                    link_page=service_overview_page_de,
                    sort_order=1,
                    allow_subnav=False,
                )
            )
            project_index_page_de = ProjectIndexPage.objects.descendant_of(
                home_page_de
            ).first()
            item_list.append(
                item_class(
                    menu=main_menu_de,
                    link_text="Projekte",
                    link_page=project_index_page_de,
                    sort_order=2,
                    allow_subnav=False,
                )
            )
            team_member_index_page_de = TeamMemberIndexPage.objects.descendant_of(
                home_page_de
            ).first()
            item_list.append(
                item_class(
                    menu=main_menu_de,
                    link_text="Team",
                    link_page=team_member_index_page_de,
                    sort_order=4,
                    allow_subnav=False,
                )
            )
            contact_page_de = ContactPage.objects.descendant_of(home_page_de).first()
            item_list.append(
                item_class(
                    menu=main_menu_de,
                    link_text="Kontakt",
                    link_page=contact_page_de,
                    sort_order=5,
                    allow_subnav=False,
                )
            )
            item_manager.bulk_create(item_list)

        main_menu_en, created = menu_model.objects.get_or_create(
            site=site, handle="main_menu_en", title="main_menu_en"
        )
        home_page_en = HomePage.objects.get(language="en")
        if not main_menu_en.get_menu_items_manager().exists():
            # create the menu items for each page needed
            item_manager = main_menu_en.get_menu_items_manager()
            item_class = item_manager.model
            item_list = []

            service_overview_page_en = ServiceOverviewPage.objects.descendant_of(
                home_page_en
            ).first()
            item_list.append(
                item_class(
                    menu=main_menu_en,
                    link_text="Services",
                    link_page=service_overview_page_en,
                    sort_order=1,
                    allow_subnav=False,
                )
            )
            project_index_page_en = ProjectIndexPage.objects.descendant_of(
                home_page_en
            ).first()
            item_list.append(
                item_class(
                    menu=main_menu_en,
                    link_text="Projects",
                    link_page=project_index_page_en,
                    sort_order=2,
                    allow_subnav=False,
                )
            )
            team_member_index_page_en = TeamMemberIndexPage.objects.descendant_of(
                home_page_en
            ).first()
            item_list.append(
                item_class(
                    menu=main_menu_en,
                    link_text="Team",
                    link_page=team_member_index_page_en,
                    sort_order=4,
                    allow_subnav=False,
                )
            )
            contact_page_en = ContactPage.objects.descendant_of(home_page_en).first()
            item_list.append(
                item_class(
                    menu=main_menu_en,
                    link_text="Contact",
                    link_page=contact_page_en,
                    sort_order=5,
                    allow_subnav=False,
                )
            )
            item_manager.bulk_create(item_list)

    def _create_flat_menus(self):
        from wagtailmenus.conf import settings as wagtailmenu_settings
        from wagtail.core.models import Site

        HomePage = apps.get_model("cms.HomePage")
        PrivacyPolicyPage = apps.get_model("cms.PrivacyPolicyPage")
        DefaultPage = apps.get_model("cms.DefaultPage")
        site = Site.objects.all()[0]
        menu_model = wagtailmenu_settings.models.FLAT_MENU_MODEL

        # create the german footer
        footer_de, created = menu_model.objects.get_or_create(
            site=site, handle="footer_de", title="footer_de"
        )
        home_page_de = HomePage.objects.get(language="de")
        if not footer_de.get_menu_items_manager().exists():
            # create the menu items for each page needed
            item_manager = footer_de.get_menu_items_manager()
            item_class = item_manager.model
            item_list = []

            data_protection_page_de = PrivacyPolicyPage.objects.descendant_of(
                home_page_de
            ).get(slug="datenschutz")
            item_list.append(
                item_class(
                    menu=footer_de,
                    link_text="Datenschutz",
                    link_page=data_protection_page_de,
                    sort_order=2,
                    allow_subnav=False,
                )
            )
            terms_page_de = DefaultPage.objects.descendant_of(home_page_de).get(
                slug="agb"
            )
            item_list.append(
                item_class(
                    menu=footer_de,
                    link_text="AGB",
                    link_page=terms_page_de,
                    sort_order=3,
                    allow_subnav=False,
                )
            )
            imprint_page_de = DefaultPage.objects.descendant_of(home_page_de).get(
                slug="impressum"
            )
            item_list.append(
                item_class(
                    menu=footer_de,
                    link_text="Impressum",
                    link_page=imprint_page_de,
                    sort_order=4,
                    allow_subnav=False,
                )
            )
            item_manager.bulk_create(item_list)

        footer_en, created = menu_model.objects.get_or_create(
            site=site, handle="footer_en", title="footer_en"
        )
        home_page_en = HomePage.objects.get(language="en")
        if not footer_en.get_menu_items_manager().exists():
            # create the menu items for each page needed
            item_manager = footer_en.get_menu_items_manager()
            item_class = item_manager.model
            item_list = []

            data_protection_page_en = PrivacyPolicyPage.objects.descendant_of(
                home_page_en
            ).get(slug="privacy-policy")
            item_list.append(
                item_class(
                    menu=footer_en,
                    link_text="Privacy",
                    link_page=data_protection_page_en,
                    sort_order=2,
                    allow_subnav=False,
                )
            )
            terms_page_en = DefaultPage.objects.descendant_of(home_page_en).get(
                slug="terms"
            )
            item_list.append(
                item_class(
                    menu=footer_en,
                    link_text="Terms",
                    link_page=terms_page_en,
                    sort_order=3,
                    allow_subnav=False,
                )
            )
            imprint_page_en = DefaultPage.objects.descendant_of(home_page_en).get(
                slug="imprint"
            )
            item_list.append(
                item_class(
                    menu=footer_en,
                    link_text="Imprint",
                    link_page=imprint_page_en,
                    sort_order=4,
                    allow_subnav=False,
                )
            )
            item_manager.bulk_create(item_list)

    def handle(self, raise_error=False, *args, **options):
        # Root Page and a default homepage are created by wagtail migrations
        # so check for > 2 here
        verbosity = options["verbosity"]
        checks = [Page.objects.all().count() > 2]
        if any(checks):
            # YOU SHOULD NEVER RUN THIS COMMAND WITHOUT PRIOR DB DUMP
            raise RuntimeError("Pages exists. Aborting.")

        self._setup()
        if verbosity > 0:
            msg = "Page Tree successfully created."
            self.stdout.write(msg)

