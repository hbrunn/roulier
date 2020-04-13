# -*- coding: utf-8 -*-
"""Transform input to dpd compatible xml."""
from jinja2 import Environment, PackageLoader
from roulier.codec import Encoder
from .common import CARRIER_TYPE


class ChronopostFrEncoder(Encoder):
    _carrier_type = CARRIER_TYPE
    _action = ["get_label"]

    def _get_actions_mapping():
        return {"get_label": "shipping"}

    def transform_input_to_carrier_webservice(self, data, action):
        env = Environment(
            loader=PackageLoader("roulier", "/carriers/chronopost_fr/templates"),
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
            "output_format": data["service"]["labelFormat"],
        }
