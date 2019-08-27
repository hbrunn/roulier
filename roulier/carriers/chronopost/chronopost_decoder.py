# -*- coding: utf-8 -*-
"""Dpd XML -> Python."""
from lxml import objectify
from roulier.codec import Decoder


class ChronopostDecoder(Decoder):
    """Chronopost XML -> Python."""

    def decode(self, body, output_format):
        """Chronopost XML -> Python."""

        def create_shipment_with_labels(msg, output_format):
            """Understand a CreateShipmentWithLabelsResponse."""
            result = msg.getchildren()[0]
            tracking_ref = result.skybillNumber.text
            data = result.skybill.text.encode()
            x = {
                "parcels": [{
                    "id": 1,  # no multi parcel management for now.
                    "reference": "",
                    "tracking": {
                        'number' : tracking_ref,
                        "url": "",
                    },
                    "label": {
                        "data": data,
                        "name": "label_%s" % tracking_ref,
                        "type": output_format,
                    },
                }],
                "annexes": [],
            }
            return x
        xml = objectify.fromstring(body)
        return create_shipment_with_labels(xml, output_format)
