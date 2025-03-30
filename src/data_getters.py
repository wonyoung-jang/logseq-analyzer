"""
Data getters for Logseq data analysis.
"""

from datetime import datetime
from typing import Any, Dict

ALL_DATA_POINTS = {
    # Metadata
    "id",
    "name",
    "name_secondary",
    "file_path",
    "file_path_parent_name",
    "file_path_name",
    "file_path_suffix",
    "file_path_parts",
    "date_created",
    "date_modified",
    "time_existed",
    "time_unmodified",
    "size",
    "uri",
    "logseq_url",
    "char_count",
    "bullet_count",
    "bullet_count_empty",
    "bullet_density",
    # Content Data
    "aliases",
    "namespace_root",
    "namespace_parent",
    "namespace_stem",
    "namespace_parts",
    "namespace_level",
    "namespace_children",
    "namespace_size",
    "page_references",
    "tagged_backlinks",
    "tags",
    "properties_values",
    "properties_page_builtin",
    "properties_page_user",
    "properties_block_builtin",
    "properties_block_user",
    "assets",
    "draws",
    "external_links_alias",
    "external_links_internet",
    "external_links_other",
    "embedded_links_asset",
    "embedded_links_internet",
    "embedded_links_other",
    "blockquotes",
    "flashcards",
    "multiline_code_block",
    "calc_block",
    "multiline_code_lang",
    "reference",
    "block_reference",
    "embed",
    "page_embed",
    "block_embed",
    "namespace_queries",
    "clozes",
    "simple_queries",
    "query_functions",
    "advanced_commands",
    # Summary Data
    "file_type",
    "node_type",
    "has_content",
    "has_backlinks",
    "has_external_links",
    "has_embedded_links",
    "is_backlinked",
    "is_backlinked_by_ns_only",
}


def init_data() -> Dict[str, Any]:
    return {
        # Metadata
        "id": "",
        "name": "",
        "name_secondary": "",
        "file_path": "",
        "file_path_parent_name": "",
        "file_path_name": "",
        "file_path_suffix": "",
        "file_path_parts": [],
        "date_created": datetime.min,
        "date_modified": datetime.min,
        "time_existed": datetime.min,
        "time_unmodified": datetime.min,
        "size": 0,
        "uri": "",
        "logseq_url": "",
        "char_count": 0,
        "bullet_count": 0,
        "bullet_count_empty": 0,
        "bullet_density": 0,
        # Content Data
        "aliases": [],
        "namespace_root": "",
        "namespace_parent": "",
        "namespace_stem": "",
        "namespace_parts": {},
        "namespace_level": 0,
        "namespace_children": {},
        "namespace_size": 0,
        "page_references": [],
        "tagged_backlinks": [],
        "tags": [],
        "properties_values": [],
        "properties_page_builtin": [],
        "properties_page_user": [],
        "properties_block_builtin": [],
        "properties_block_user": [],
        "assets": [],
        "draws": [],
        "external_links_alias": [],
        "external_links_internet": [],
        "external_links_other": [],
        "embedded_links_asset": [],
        "embedded_links_internet": [],
        "embedded_links_other": [],
        "blockquotes": [],
        "flashcards": [],
        "multiline_code_block": [],
        "calc_block": [],
        "multiline_code_lang": [],
        "reference": [],
        "block_reference": [],
        "embed": [],
        "page_embed": [],
        "block_embed": [],
        "namespace_queries": [],
        "clozes": [],
        "simple_queries": [],
        "query_functions": [],
        "advanced_commands": [],
        # Summary Data
        "file_type": "",
        "node_type": "",
        "has_content": False,
        "has_backlinks": False,
        "has_external_links": False,
        "has_embedded_links": False,
        "is_backlinked": False,
        "is_backlinked_by_ns_only": False,
    }


def get_all_data(values):
    data_points = [
        # Metadata
        "id",
        "name",
        "name_secondary",
        "file_path",
        "file_path_parent_name",
        "file_path_name",
        "file_path_suffix",
        "file_path_parts",
        "date_created",
        "date_modified",
        "time_existed",
        "time_unmodified",
        "size",
        "uri",
        "logseq_url",
        "char_count",
        "bullet_count",
        "bullet_count_empty",
        "bullet_density",
        # Content Data
        "aliases",
        "namespace_root",
        "namespace_parent",
        "namespace_stem",
        "namespace_parts",
        "namespace_level",
        "namespace_children",
        "namespace_size",
        "page_references",
        "tagged_backlinks",
        "tags",
        "properties_values",
        "properties_page_builtin",
        "properties_page_user",
        "properties_block_builtin",
        "properties_block_user",
        "assets",
        "draws",
        "external_links_alias",
        "external_links_internet",
        "external_links_other",
        "embedded_links_asset",
        "embedded_links_internet",
        "embedded_links_other",
        "blockquotes",
        "flashcards",
        "multiline_code_block",
        "calc_block",
        "multiline_code_lang",
        "reference",
        "block_reference",
        "embed",
        "page_embed",
        "block_embed",
        "namespace_queries",
        "clozes",
        "simple_queries",
        "query_functions",
        "advanced_commands",
        # Summary Data
        "file_type",
        "node_type",
        "has_content",
        "has_backlinks",
        "has_external_links",
        "has_embedded_links",
        "is_backlinked",
        "is_backlinked_by_ns_only",
    ]
    all_data = {}
    for key in [k for k in data_points if k in values]:
        all_data.setdefault(key, values.get(key))
    return all_data


def get_meta_data(values):
    data_points = [
        "id",
        "name",
        "name_secondary",
        "file_path",
        "file_path_parent_name",
        "file_path_name",
        "file_path_suffix",
        "file_path_parts",
        "date_created",
        "date_modified",
        "time_existed",
        "time_unmodified",
        "size",
        "uri",
        "logseq_url",
        "char_count",
        "bullet_count",
        "bullet_count_empty",
        "bullet_density",
    ]
    meta_data = {}
    for key in [k for k in data_points if k in values]:
        meta_data.setdefault(key, values.get(key))
    return meta_data


def get_content_data(values):
    data_points = [
        "aliases",
        "namespace_root",
        "namespace_parent",
        "namespace_stem",
        "namespace_parts",
        "namespace_level",
        "namespace_children",
        "namespace_size",
        "page_references",
        "tagged_backlinks",
        "tags",
        "properties_values",
        "properties_page_builtin",
        "properties_page_user",
        "properties_block_builtin",
        "properties_block_user",
        "assets",
        "draws",
        "external_links_alias",
        "external_links_internet",
        "external_links_other",
        "embedded_links_asset",
        "embedded_links_internet",
        "embedded_links_other",
        "blockquotes",
        "flashcards",
        "multiline_code_block",
        "calc_block",
        "multiline_code_lang",
        "reference",
        "block_reference",
        "embed",
        "page_embed",
        "block_embed",
        "namespace_queries",
        "clozes",
        "simple_queries",
        "query_functions",
        "advanced_commands",
    ]
    content_data = {}
    for key in [k for k in data_points if k in values]:
        content_data.setdefault(key, values.get(key))
    return content_data


def get_namespace_data(values):
    data_points = [
        "namespace_root",
        "namespace_parent",
        "namespace_stem",
        "namespace_parts",
        "namespace_level",
        "namespace_children",
        "namespace_size",
        "namespace_queries",
    ]
    namespace_data = {}
    for key in [k for k in data_points if k in values]:
        namespace_data.setdefault(key, values.get(key))
    return namespace_data


def get_summary_data(values):
    data_points = [
        "file_type",
        "node_type",
        "has_content",
        "has_backlinks",
        "has_external_links",
        "has_embedded_links",
        "is_backlinked",
        "is_backlinked_by_ns_only",
    ]
    summary_data = {}
    for key in [k for k in data_points if k in values]:
        summary_data.setdefault(key, values.get(key))
    return summary_data


def get_numeric_data(values):
    data_points = [
        "size",
        "char_count",
        "bullet_count",
        "bullet_count_empty",
        "bullet_density",
        "namespace_level",
        "namespace_size",
    ]
    numeric_data = {}
    for key in [k for k in data_points if k in values]:
        numeric_data.setdefault(key, values.get(key))
    return numeric_data


def get_string_data(values):
    data_points = [
        "id",
        "name",
        "name_secondary",
        "file_path",
        "file_path_parent_name",
        "file_path_name",
        "file_path_suffix",
        "uri",
        "namespace_root",
        "namespace_parent",
        "file_type",
        "node_type",
        "logseq_url",
    ]
    string_data = {}
    for key in [k for k in data_points if k in values]:
        string_data.setdefault(key, values.get(key))
    return string_data


def get_boolean_data(values):
    data_points = [
        "has_content",
        "has_backlinks",
        "has_external_links",
        "has_embedded_links",
        "is_backlinked",
        "is_backlinked_by_ns_only",
    ]
    boolean_data = {}
    for key in [k for k in data_points if k in values]:
        boolean_data.setdefault(key, values.get(key))
    return boolean_data


def get_datetime_data(values):
    data_points = [
        "date_created",
        "date_modified",
        "time_existed",
        "time_unmodified",
    ]
    datetime_data = {}
    for key in [k for k in data_points if k in values]:
        datetime_data.setdefault(key, values.get(key))
    return datetime_data


def get_list_data(values):
    data_points = [
        "advanced_commands",
        "aliases",
        "assets",
        "block_embed",
        "block_reference",
        "blockquotes",
        "calc_block",
        "clozes",
        "draws",
        "embed",
        "embedded_links_asset",
        "embedded_links_internet",
        "embedded_links_other",
        "external_links_alias",
        "external_links_internet",
        "external_links_other",
        "file_path_parts",
        "flashcards",
        "multiline_code_block",
        "multiline_code_lang",
        "namespace_queries",
        "page_embed",
        "page_references",
        "properties_block_builtin",
        "properties_block_user",
        "properties_page_builtin",
        "properties_page_user",
        "properties_values",
        "query_functions",
        "reference",
        "simple_queries",
        "tagged_backlinks",
        "tags",
    ]
    list_data = {}
    for key in [k for k in data_points if k in values]:
        list_data.setdefault(key, values.get(key))
    return list_data
