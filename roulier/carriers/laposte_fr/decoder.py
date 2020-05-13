# -*- coding: utf-8 -*-
"""Laposte XML -> Python."""
from lxml import objectify

from ...roulier import Decoder
from .common import CARRIER_TYPE
import base64


class LaposteFrDecoder(Decoder):
    _carrier_type = CARRIER_TYPE
    _action = ["get_label"]

    """Laposte XML -> Python."""

    def decode(self, responses, input_payloads):
        """Laposte XML -> Python."""

        def get_cid(tag, tree):
            element = tree.find(tag)
            if element is None:
                return None
            href = element.getchildren()[0].attrib["href"]
            # href contains cid:236212...-38932@cfx.apache.org
            return href[len("cid:") :]  # remove prefix


        result = {
            "parcels": [],
            "annexes": [],
        }
        for response, input_payload in zip(responses, input_payloads):
            body = response["body"]
            parts = response["parts"]
            output_format = input_payload["output_format"]

            xml = objectify.fromstring(body)
            msg = xml.xpath("//return")[0]

            rep = msg.labelResponse
            cn23_cid = get_cid("cn23", rep)
            label_cid = get_cid("label", rep)

            annexes = []

            if cn23_cid:
                annexes.append(
                    {"name": "cn23", "data": parts.get(cn23_cid), "type": "pdf"}
                )

            if rep.find("pdfUrl"):
                annexes.append(
                    {"name": "label", "data": rep.find("pdfUrl"), "type": "url"}
                )
            label = {
                        "id": 1,
                        "reference": rep.parcelNumber,
                        "tracking": {
                            "number": rep.parcelNumber,
                            "url": "",
                            "partner": rep.find("parcelNumberPartner"),
                        },
                        "label": {
                            "data": base64.b64encode(parts.get(label_cid).encode()),
                            "name": "label_1",
                            "type": output_format,
                        },
                    }
            result['parcels'].append(label)
        return result
