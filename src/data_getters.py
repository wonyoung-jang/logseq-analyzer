from datetime import datetime


def get_meta_data(item):
    meta_data = {}
    meta_data["id"] = item.get("id", None)
    meta_data["name"] = item.get("name", None)
    meta_data["name_secondary"] = item.get("name_secondary", None)
    meta_data["file_path"] = item.get("file_path", None)
    meta_data["file_path_parent_name"] = item.get("file_path_parent_name", None)
    meta_data["file_path_name"] = item.get("file_path_name", None)
    meta_data["file_path_suffix"] = item.get("file_path_suffix", None)
    meta_data["date_created"] = item.get("date_created", None)
    meta_data["date_modified"] = item.get("date_modified", None)
    meta_data["time_existed"] = item.get("time_existed", None)
    meta_data["time_unmodified"] = item.get("time_unmodified", None)
    meta_data["size"] = item.get("size", 0)
    meta_data["uri"] = item.get("uri", None)
    meta_data["char_count"] = item.get("char_count", 0)
    meta_data["bullet_count"] = item.get("bullet_count", 0)
    meta_data["bullet_density"] = item.get("bullet_density", 0)
    return meta_data


def get_content_data(item):
    content_data = {}
    content_data["aliases"] = item.get("aliases", [])
    content_data["namespace_root"] = item.get("namespace_root", "")
    content_data["namespace_parent"] = item.get("namespace_parent", "")
    content_data["namespace_parts"] = item.get("namespace_parts", {})
    content_data["namespace_level"] = item.get("namespace_level", -1)
    content_data["page_references"] = item.get("page_references", [])
    content_data["tagged_backlinks"] = item.get("tagged_backlinks", [])
    content_data["tags"] = item.get("tags", [])
    content_data["properties_values"] = item.get("properties_values", [])
    content_data["properties_page_builtin"] = item.get("properties_page_builtin", [])
    content_data["properties_page_user"] = item.get("properties_page_user", [])
    content_data["properties_block_builtin"] = item.get("properties_block_builtin", [])
    content_data["properties_block_user"] = item.get("properties_block_user", [])
    content_data["assets"] = item.get("assets", [])
    content_data["draws"] = item.get("draws", [])
    content_data["external_links_internet"] = item.get("external_links_internet", [])
    content_data["external_links_alias"] = item.get("external_links_alias", [])
    content_data["external_links_other"] = item.get("external_links_other", [])
    content_data["embedded_links_internet"] = item.get("embedded_links_internet", [])
    content_data["embedded_links_asset"] = item.get("embedded_links_asset", [])
    content_data["embedded_links_other"] = item.get("embedded_links_other", [])
    content_data["blockquotes"] = item.get("blockquotes", [])
    content_data["flashcards"] = item.get("flashcards", [])
    content_data["multiline_code_block"] = item.get("multiline_code_block", [])
    content_data["calc_block"] = item.get("calc_block", [])
    content_data["multiline_code_lang"] = item.get("multiline_code_lang", [])
    content_data["reference"] = item.get("reference", [])
    content_data["block_reference"] = item.get("block_reference", [])
    content_data["embed"] = item.get("embed", [])
    content_data["page_embed"] = item.get("page_embed", [])
    content_data["block_embed"] = item.get("block_embed", [])
    content_data["namespace_queries"] = item.get("namespace_queries", [])
    content_data["clozes"] = item.get("clozes", [])
    content_data["simple_queries"] = item.get("simple_queries", [])
    content_data["query_functions"] = item.get("query_functions", [])
    content_data["advanced_commands"] = item.get("advanced_commands", [])
    return content_data


def get_summary_data(item):
    summary_data = {}
    summary_data["file_type"] = item.get("file_type", "")
    summary_data["file_extension"] = item.get("file_extension", "")
    summary_data["node_type"] = item.get("node_type", "")
    summary_data["has_content"] = item.get("has_content", False)
    summary_data["has_backlinks"] = item.get("has_backlinks", False)
    summary_data["has_external_links"] = item.get("has_external_links", False)
    summary_data["has_embedded_links"] = item.get("has_embedded_links", False)
    summary_data["is_backlinked"] = item.get("is_backlinked", False)
    summary_data["is_backlinked_by_ns_only"] = item.get("is_backlinked_by_ns_only", False)
    return summary_data


def get_numeric_data(item):
    numeric_data = {}
    numeric_data["size"] = item.get("size", 0)
    numeric_data["char_count"] = item.get("char_count", 0)
    numeric_data["bullet_count"] = item.get("bullet_count", 0)
    numeric_data["bullet_density"] = item.get("bullet_density", 0)
    numeric_data["namespace_level"] = item.get("namespace_level", -1)
    return numeric_data


def get_string_data(item):
    string_data = {}
    string_data["id"] = item.get("id", "")
    string_data["name"] = item.get("name", "")
    string_data["name_secondary"] = item.get("name_secondary", "")
    string_data["file_path"] = item.get("file_path", "")
    string_data["file_path_parent_name"] = item.get("file_path_parent_name", "")
    string_data["file_path_name"] = item.get("file_path_name", "")
    string_data["file_path_suffix"] = item.get("file_path_suffix", "")
    string_data["uri"] = item.get("uri", "")
    string_data["namespace_root"] = item.get("namespace_root", "")
    string_data["namespace_parent"] = item.get("namespace_parent", "")
    string_data["file_type"] = item.get("file_type", "")
    string_data["file_extension"] = item.get("file_extension", "")
    string_data["node_type"] = item.get("node_type", "")
    return string_data


def get_boolean_data(item):
    boolean_data = {}
    boolean_data["has_content"] = item.get("has_content", False)
    boolean_data["has_backlinks"] = item.get("has_backlinks", False)
    boolean_data["has_external_links"] = item.get("has_external_links", False)
    boolean_data["has_embedded_links"] = item.get("has_embedded_links", False)
    boolean_data["is_backlinked"] = item.get("is_backlinked", False)
    boolean_data["is_backlinked_by_ns_only"] = item.get("is_backlinked_by_ns_only", False)
    return boolean_data


def get_datetime_data(item):
    datetime_data = {}
    datetime_data["date_created"] = item.get("date_created", datetime.min)
    datetime_data["date_modified"] = item.get("date_modified", datetime.min)
    datetime_data["time_existed"] = item.get("time_existed", datetime.min)
    datetime_data["time_unmodified"] = item.get("time_unmodified", datetime.min)
    return datetime_data


def get_list_data(item):
    list_data = {}
    list_data["file_path_parts"] = item.get("file_path_parts", [])
    list_data["aliases"] = item.get("aliases", [])
    list_data["page_references"] = item.get("page_references", [])
    list_data["tagged_backlinks"] = item.get("tagged_backlinks", [])
    list_data["tags"] = item.get("tags", [])
    list_data["properties_values"] = item.get("properties_values", [])
    list_data["properties_page_builtin"] = item.get("properties_page_builtin", [])
    list_data["properties_page_user"] = item.get("properties_page_user", [])
    list_data["properties_block_builtin"] = item.get("properties_block_builtin", [])
    list_data["properties_block_user"] = item.get("properties_block_user", [])
    list_data["assets"] = item.get("assets", [])
    list_data["draws"] = item.get("draws", [])
    list_data["external_links"] = item.get("external_links", [])
    list_data["external_links_internet"] = item.get("external_links_internet", [])
    list_data["external_links_alias"] = item.get("external_links_alias", [])
    list_data["embedded_links"] = item.get("embedded_links", [])
    list_data["embedded_links_internet"] = item.get("embedded_links_internet", [])
    list_data["embedded_links_asset"] = item.get("embedded_links_asset", [])
    list_data["blockquotes"] = item.get("blockquotes", [])
    list_data["flashcards"] = item.get("flashcards", [])
    list_data["multiline_code_block"] = item.get("multiline_code_block", [])
    list_data["calc_block"] = item.get("calc_block", [])
    list_data["multiline_code_lang"] = item.get("multiline_code_lang", [])
    list_data["reference"] = item.get("reference", [])
    list_data["block_reference"] = item.get("block_reference", [])
    list_data["embed"] = item.get("embed", [])
    list_data["page_embed"] = item.get("page_embed", [])
    list_data["block_embed"] = item.get("block_embed", [])
    list_data["namespace_queries"] = item.get("namespace_queries", [])
    list_data["clozes"] = item.get("clozes", [])
    list_data["simple_queries"] = item.get("simple_queries", [])
    list_data["query_functions"] = item.get("query_functions", [])
    list_data["advanced_commands"] = item.get("advanced_commands", [])
    return list_data
