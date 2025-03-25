"""
Process properties of the dataset.
"""

from typing import Dict, Any, Tuple

from .config_loader import get_config
from .process_content_data import split_builtin_user_properties

CONFIG = get_config()
BUILT_IN_PROPERTIES = CONFIG.get_built_in_properties()


def process_properties(
    graph_data: Dict[str, Any],
) -> Tuple[Dict[str, Any], Dict[str, Any], Dict[str, Any], Dict[str, Any]]:
    """
    Process the properties of the dataset.

    Args:
        graph_data (Dict[str, Any]): The graph data containing properties values.

    Returns:
        Tuple[Dict[str, Any], Dict[str, Any], Dict[str, Any], Dict[str, Any]]:
            - Set of all built-in property values.
            - Set of all user-defined property values.
            - Sorted dictionary of all built-in property values.
            - Sorted dictionary of all user-defined property values.
    """
    all_prop_values = get_all_prop_values(graph_data)
    return all_prop_values


def get_all_prop_values(
    graph_data: Dict[str, Any],
) -> Tuple[Dict[str, Any], Dict[str, Any], Dict[str, Any], Dict[str, Any]]:
    """
    Get all property values from the graph data.

    Args:
        graph_data (Dict[str, Any]): The graph data containing properties values.

    Returns:
        Tuple[Dict[str, Any], Dict[str, Any], Dict[str, Any], Dict[str, Any]]:
            - Set of all built-in property values.
            - Set of all user-defined property values.
            - Sorted dictionary of all built-in property values.
            - Sorted dictionary of all user-defined property values.
    """
    all_prop_values = {}
    for name, data in graph_data.items():
        if data.get("properties_values"):
            for prop, value in data["properties_values"].items():
                found_in_value = (name, value)
                all_prop_values[prop] = all_prop_values.get(prop, []) + [found_in_value]

    props_found = sorted(all_prop_values.keys())
    built_in_props, user_props = split_builtin_user_properties(props_found, BUILT_IN_PROPERTIES)
    sorted_all_props_builtin = {k: sorted(v) for k, v in all_prop_values.items() if k in built_in_props}
    sorted_all_props_user = {k: sorted(v) for k, v in all_prop_values.items() if k in user_props}
    set_all_prop_values_builtin = {k: set(v) for k, v in sorted_all_props_builtin.items()}
    set_all_prop_values_user = {k: set(v) for k, v in sorted_all_props_user.items()}

    return set_all_prop_values_builtin, set_all_prop_values_user, sorted_all_props_builtin, sorted_all_props_user
