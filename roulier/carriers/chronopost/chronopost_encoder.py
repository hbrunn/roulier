# -*- coding: utf-8 -*-
"""Transform input to dpd compatible xml."""
from jinja2 import Environment, PackageLoader
from roulier.codec import Encoder
from datetime import datetime
from .chronopost_api import ChronopostApi
from roulier.exception import InvalidApiInput
import logging

CHRONOPOST_ACTIONS = "shipping"
log = logging.getLogger(__name__)


class ChronopostEncoder(Encoder):
    """Transform input to dpd compatible xml."""

    def encode(self, api_input, action):
        """Transform input to chronopost compatible xml."""
        api = ChronopostApi()
        if not (action in CHRONOPOST_ACTIONS):
            raise InvalidApiInput(
                "action %s not in %s" % (action, ", ".join(CHRONOPOST_ACTIONS))
            )
        data = api.normalize(api_input)

        env = Environment(
            loader=PackageLoader("roulier", "/carriers/chronopost/templates"),
            extensions=["jinja2.ext.with_", "jinja2.ext.autoescape"],
            autoescape=True,
        )

        template = env.get_template("chronopost_%s.xml" % action)
        return {
            "body": template.render(
                service=data["service"],
                parcel=data["parcels"][0],
                from_address=data["from_address"],
                # TODO manage customer address different from expeditor
                customer_address=data["from_address"],
                to_address=data["to_address"],
                auth=data["auth"],
            ),
            "output_format": data['service']['labelFormat'],
        }

    def api(self):
        """Return API we are expecting."""
        return ChronopostApi().api_values()
