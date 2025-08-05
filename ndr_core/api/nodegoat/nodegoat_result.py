"""Implementation of the Nodegoat class. """
import json

import pymongo
import pymongo.errors
import requests
from bson import json_util
from django.utils.translation import gettext_lazy as _

from ndr_core.api.base_result import BaseResult
from ndr_core.utils import get_nested_value


class NodegoatResult(BaseResult):
    """Implementation of the mongo DB API. """

    def __init__(self, search_configuration, query, request):
        """Initializes the NodegoatResult with the search configuration and query."""
        super().__init__(search_configuration, query, request)
        token = self.search_configuration.api_auth_key
        self.api_request_headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/json"
        }

    def save_raw_result(self, text):
        """ The returned text is already a JSON string. The result objects are in a dict
        but we need to convert it to a list of dictionaries. """

        try:
            text.strip()
            data = json.loads(text)
            hits = data.get("data", {}).get("objects", {})
        except Exception as e:
            hits = {}

        values_list = list(hits.values())
        values_list = self.clean_nodegoat_result(values_list)
        # Create the raw result
        self.raw_result = {
            "total": len(values_list),
            "page": self.page,
            "hits": values_list
        }

    def clean_nodegoat_result(self, results):
        """Cleans the Nodegoat result by simplifying the result object."""
        cleaned_results = []

        # Iterate over the different results
        for result in results:
            result_obj = result.get("object", {})
            # Only copy the necessary fields for each result
            # 1: General object information
            clean_result = {
                "nodegoat_id": result_obj.get("nodegoat_id"),
                "object_id": result_obj.get("object_id"),
                "object_name": result_obj.get("object_name"),
                "object_dating": result_obj.get("object_dating"),
                "object_definitions": {},
                "object_subs": {}
            }

            # 2: Object definitions: Basic values of an object (e.g. title, description, etc.)
            for key, value in result["object_definitions"].items():
                clean_result["object_definitions"][key] = value["object_definition_value"]

            # 3: Object subs: Sub-objects of an object.
            # Group by object_sub_details_id and collect all sub-objects for each type
            result_sub_objects = result.get("object_subs", {})

            # Handle case where object_subs is an empty list instead of dict
            if isinstance(result_sub_objects, list):
                result_sub_objects = {}  # Convert empty list to empty dict

            for sub_id, sub_data in result_sub_objects.items():
                # Get the object_sub metadata
                object_sub = sub_data.get("object_sub", {})
                object_sub_details_id = str(object_sub.get("object_sub_details_id", ""))

                # Create the cleaned sub-object
                clean_object_sub = {
                    "object_sub_id": object_sub.get("object_sub_id"),
                    "start": object_sub.get("object_sub_date_start", ""),
                    "end": object_sub.get("object_sub_date_end", ""),
                    "geometry": object_sub.get("object_sub_location_geometry", ""),
                    "location": object_sub.get("object_sub_location_ref_object_name", ""),
                    "object_sub_definitions": {}
                }

                # Process object_sub_definitions
                object_sub_definitions = sub_data.get("object_sub_definitions", {})
                # Empty results come as list, so we convert them to an empty dict
                if isinstance(object_sub_definitions, list) and len(object_sub_definitions) == 0:
                    object_sub_definitions = {}

                for def_key, def_value in object_sub_definitions.items():
                    clean_object_sub["object_sub_definitions"][def_key] = {
                        "value": def_value["object_sub_definition_value"],
                        "ref_object_id": def_value.get("object_sub_definition_ref_object_id")
                    }

                # Group by object_sub_details_id
                if object_sub_details_id in clean_result["object_subs"]:
                    clean_result["object_subs"][object_sub_details_id].append(clean_object_sub)
                else:
                    clean_result["object_subs"][object_sub_details_id] = [clean_object_sub]

            cleaned_results.append(clean_result)

        return cleaned_results

    def fill_search_result_meta_data(self):
        """Fills the search result metadata. In the download_result method, the raw result is created and the
        total number of documents is retrieved. The page number is also set in the download_result method."""

        if "total" in self.raw_result:
            self.total = self.raw_result["total"]
        else:
            self.total = 0
        if "page" in self.raw_result:
            self.page = self.raw_result["page"]

        self.num_pages = self.total // self.page_size
        if self.total % self.page_size > 0:
            self.num_pages += 1

    def fill_results(self):
        if "hits" in self.raw_result:
            self.results = self.raw_result['hits']

    def get_id_value(self, result):
        """ Overwrite the default get_id_value method to get the id from the result. """
        return get_nested_value(result, self.search_configuration.search_id_field)
