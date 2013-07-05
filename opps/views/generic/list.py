#!/usr/bin/env python
# -*- coding: utf-8 -*-
from django.core.exceptions import ImproperlyConfigured
from django.views.generic.list import ListView as DjangoListView
from django.contrib.sites.models import get_current_site
from django.utils import timezone
from django.conf import settings

from opps.views.generic.base import View

from opps.containers.models import ContainerBox


class ListView(View, DjangoListView):

    def get_template_names(self):
        names = []
        domain_folder = self.get_template_folder()

        # look for a different template only if defined in settings
        # default should be OPPS_PAGINATE_SUFFIX = "_paginated"
        # if set OPPS_PAGINATE_NOT_APP = ['TagList'] not set paginate_suffix
        if self.request and self.request.GET.get('page') and\
           self.__class__.__name__ not in settings.OPPS_PAGINATE_NOT_APP:
            self.paginate_suffix = settings.OPPS_PAGINATE_SUFFIX
            self.template_name_suffix = "_list{}".format(self.paginate_suffix)
        else:
            self.paginate_suffix = ''

        if self.channel:
            if self.channel.group and self.channel.parent:

                _template = '{}/_{}{}.html'.format(
                    domain_folder,
                    self.channel.parent.long_slug,
                    self.paginate_suffix
                )
                names.append(_template)

                _template = u'{}/_post_list{}.html'.format(
                    domain_folder,
                    # self.channel.parent.long_slug,
                    self.paginate_suffix
                )
                names.append(_template)

        names.append(
            u'{}/{}{}.html'.format(
                domain_folder,
                self.long_slug,
                self.paginate_suffix
            )
        )

        try:
            names = names + super(ListView, self).get_template_names()
        except ImproperlyConfigured:
            pass

        if self.paginate_suffix:
            # use the default _paginated.html if no template found
            names.append(
                u"{}/{}.html".format(domain_folder, self.paginate_suffix)
            )

        return names

    @property
    def queryset(self):
        self.site = get_current_site(self.request).domain
        self.long_slug = self.get_long_slug()

        if not self.long_slug:
            return None

        self.set_channel_rules()

        self.articleboxes = ContainerBox.objects.filter(
            channel__long_slug=self.long_slug)

        self.excluded_ids = []
        for box in self.articleboxes:
            self.excluded_ids += [a.pk for a in box.ordered_articles()]

        self.article = self.model.objects.filter(
            site_domain=self.site,
            channel_long_slug__in=self.channel_long_slug,
            date_available__lte=timezone.now(),
            published=True
        ).exclude(pk__in=self.excluded_ids)

        if self.limit:
            self.article = self.article[:self.limit]

        return self.article._clone()