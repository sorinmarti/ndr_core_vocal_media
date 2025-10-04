"""Implementation of the mongo DB API. """
from ndr_core.models import NdrCoreSearchField
from ndr_core.api.base_query import BaseQuery


class NodegoatQuery(BaseQuery):
    """Implementation of the nodegoat API. """

    def __init__(self, search_config, page=1):
        super().__init__(search_config, page)
        self.search_config = search_config

        # The connection URL is expected to have thr following form:
        # https://api.nodegoat.dasch.swiss/data/type/<type_id>/
        # (Remove the trailing slash if it exists)
        if self.search_config.api_connection_url.endswith('/'):
            self.search_config.api_connection_url = self.search_config.api_connection_url[:-1]

        self.data_type_id = self.search_config.api_connection_url.split('/')[-1]

    def get_simple_query(self, search_term, add_page_and_size=True, and_or='and'):
        """  """
        query = self.search_config.api_connection_url

        query += '/object?search=' + search_term
        if add_page_and_size:
            query += f'&limit={self.search_config.page_size}&offset=' + str((self.page - 1) * self.search_config.page_size)
        else:
            query += '&limit=100&offset=0'

        return query

    def get_advanced_query(self, *kwargs):
        query = self.search_config.api_connection_url
        query += '/object?filter='
        obj_filter = {"form": {"filter_1": {"type_id": self.data_type_id, "object_definitions": {}}}}

        for field in self.get_field_configurations():
            object_definition = {}
            if field.field_type == 'string':
                object_definition["equality"] = "*"
                object_definition["value"] = field.value
            elif field.field_type == 'list':
                object_definition["equality"] = "*"
                object_definition["value"] = field.value

            obj_filter["form"]["filter_1"]["object_definitions"][field.parameter] = [object_definition]

        query += str(obj_filter).replace("'", '"')

        print("NG-QUERY:", query)
        return query

    def get_list_query(self, list_name, add_page_and_size=True, search_term=None, tags=None):
        """ Not Implemented """
        return None

    def get_record_query(self, record_id):
        """ Not Implemented """
        record_query = None
        return record_query

    def get_all_items_query(self, add_page_and_size=True):
        """Returns a query to retrieve all items without filters."""
        query = self.search_config.api_connection_url
        query += '/object?'

        if add_page_and_size:
            query += f'limit={self.search_config.page_size}&offset=' + str((self.page - 1) * self.search_config.page_size)
        else:
            query += 'limit=100&offset=0'

        return query

    def get_explain_query(self, search_type):
        """ Not Implemented """
        return None

    def set_value(self, field_name, value):
        """Sets a value=key setting to compose a query from"""
        self.values[field_name] = value

    @staticmethod
    def get_value_conf(item_value):
        """Gets the value of a key setting"""
        if "__" in item_value:
            split = item_value.split('__')
            return split[0], True if split[1] == 'true' else False

        return item_value, True
