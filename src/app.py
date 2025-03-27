"""
This module contains the main application logic for the Logseq analyzer.
"""

# import sys
import logging
from pathlib import Path
import shelve

from src.helpers import iter_files

from .config_loader import get_config
from .process_properties import process_properties
from .process_dangling_links import process_dangling_links
from .compile_regex import compile_re_config, compile_re_content
from .core import (
    core_data_analysis,
    generate_global_summary,
    generate_sorted_summary_all,
    generate_summary_subsets,
    process_graph_files,
)
from .logseq_assets import handle_assets
from .logseq_move_files import create_delete_directory, handle_move_files, handle_move_directory
from .logseq_journals import extract_journals_from_dangling_links, process_journals_timelines
from .process_namespaces import process_namespace_data
from .setup import (
    create_log_file,
    create_output_directory,
    get_logseq_analyzer_args,
    get_logseq_config_edn,
    get_logseq_target_dirs,
    get_sub_file_or_folder,
    set_logseq_config_edn_data,
    validate_path,
)

CONFIG = get_config()
DEF_LS_DIR = CONFIG.get("LOGSEQ_STRUCTURE", "LOGSEQ_DIR")
DEF_REC_DIR = CONFIG.get("LOGSEQ_STRUCTURE", "RECYCLE_DIR")
DEF_BAK_DIR = CONFIG.get("LOGSEQ_STRUCTURE", "BAK_DIR")


def check_for_modified_files(logseq_graph_dir: Path, target_dirs: list):
    modded_files = []

    with shelve.open("mydata") as db:
        mod_tracker = db.get("mod_tracker", {})

        for path in iter_files(logseq_graph_dir, target_dirs):
            curr_date_mod = path.stat().st_mtime
            last_date_mod = mod_tracker.get(str(path))

            if last_date_mod is None or last_date_mod != curr_date_mod:
                mod_tracker[str(path)] = curr_date_mod
                logging.debug("File modified: %s", path)
                modded_files.append(path)

        db["mod_tracker"] = mod_tracker

    return modded_files


def check_for_deleted_files(graph_data_db: dict):
    deleted_files = []
    
    for key, data in graph_data_db.items():
        path = data.get("file_path", None)
        if Path(path).exists():
            continue
        deleted_files.append(key)
        logging.debug("File deleted: %s", path)
        
    return deleted_files


def run_app(**kwargs):
    """Main function to run the Logseq analyzer."""

    # Setup variables
    gui_instance = kwargs.get("gui_instance")

    ###################################################################
    # Phase 01: Setup
    ###################################################################
    if gui_instance:
        gui_instance.update_progress("setup", 20)

    # Parse command line arguments or GUI arguments
    args = get_logseq_analyzer_args(**kwargs)

    # Setup output directory and logging
    create_output_directory()
    create_log_file()

    # Get graph folder and extract bak and recycle directories
    logseq_graph_dir = Path(args.graph_folder)
    validate_path(logseq_graph_dir)
    CONFIG.set("CONSTANTS", "GRAPH_DIR", str(logseq_graph_dir))
    logseq_dir = get_sub_file_or_folder(logseq_graph_dir, DEF_LS_DIR)
    recycle_dir = get_sub_file_or_folder(logseq_dir, DEF_REC_DIR)
    bak_dir = get_sub_file_or_folder(logseq_dir, DEF_BAK_DIR)

    # Compile regex patterns
    content_patterns = compile_re_content()
    config_patterns = compile_re_config()

    # Get config data and target directories
    config_edn_data = get_logseq_config_edn(args, logseq_dir, config_patterns)
    set_logseq_config_edn_data(config_edn_data)
    target_dirs = get_logseq_target_dirs()
    CONFIG.set("REPORTING", "REPORT_FORMAT", args.report_format)

    if gui_instance:
        gui_instance.update_progress("setup", 100)
        gui_instance.update_progress("process_files", 20)

    ################################################################
    # Phase 02: Process files
    ################################################################
    # Check for modified files
    modded_files = check_for_modified_files(logseq_graph_dir, target_dirs)
        
    # Process for only modified/new graph files
    graph_data, graph_content_bullets = process_graph_files(modded_files, content_patterns)
    
    # Check for existing data
    with shelve.open("mydata") as db:
        graph_data_db = db.get("graph_data", {})
        graph_content_db = db.get("graph_content", {})
        
    # Check for deleted files and remove them from the database
    deleted_files = check_for_deleted_files(graph_data_db)
    for file in deleted_files:
        graph_data_db.pop(file, None)
        graph_content_db.pop(file, None)
    
    # Update existing data with new data
    graph_data_db.update(graph_data)
    graph_content_db.update(graph_content_bullets)

    # Core data analysis
    (
        alphanum_dict,
        alphanum_dict_ns,
        dangling_links,
        graph_data,
        all_refs,
    ) = core_data_analysis(graph_data_db)

    # Namespaces analysis
    summary_namespaces, summary_global_namespaces = process_namespace_data(graph_data, dangling_links)

    # Basic dangling links analysis
    dangling_dict = process_dangling_links(all_refs, dangling_links)

    # Basic properties analysis
    set_all_prop_values_builtin, set_all_prop_values_user, sorted_all_props_builtin, sorted_all_props_user = (
        process_properties(graph_data)
    )

    if gui_instance:
        gui_instance.update_progress("process_files", 100)
        gui_instance.update_progress("summary", 20)

    #################################################################
    # Phase 03: Process summaries
    #################################################################
    # Generate summary
    summary_data_subsets = generate_summary_subsets(graph_data)
    summary_global = generate_global_summary(summary_data_subsets)
    summary_sorted_all = generate_sorted_summary_all(graph_data)

    if gui_instance:
        gui_instance.update_progress("summary", 100)
        gui_instance.update_progress("move_files", 20)

    #####################################################################
    # Phase 04: Move files to a delete directory (optional)
    #####################################################################
    to_delete_dir = create_delete_directory()
    assets_backlinked, assets_not_backlinked = handle_assets(graph_data, summary_data_subsets)

    moved_files = {}
    moved_files["moved_assets"] = handle_move_files(
        args.move_unlinked_assets, graph_data, assets_not_backlinked, to_delete_dir
    )
    moved_files["moved_bak"] = handle_move_directory(args.move_bak, bak_dir, to_delete_dir, DEF_BAK_DIR)
    moved_files["moved_recycle"] = handle_move_directory(args.move_recycle, recycle_dir, to_delete_dir, DEF_REC_DIR)

    if gui_instance:
        gui_instance.update_progress("move_files", 100)

    output_data = {
        # Main meta outputs
        "alphanum_dict": alphanum_dict,
        "alphanum_dict_ns": alphanum_dict_ns,
        "dangling_links": dangling_links,
        "config_edn_data": config_edn_data,
        "target_dirs": target_dirs,
        "graph_data": graph_data,
        "content_patterns": content_patterns,
        "config_patterns": config_patterns,
        "all_refs": all_refs,
        "dangling_dict": dangling_dict,
        # Properties
        "set_all_prop_values_builtin": set_all_prop_values_builtin,
        "set_all_prop_values_user": set_all_prop_values_user,
        "sorted_all_props_builtin": sorted_all_props_builtin,
        "sorted_all_props_user": sorted_all_props_user,
        # General summary
        "___summary_global": summary_global,
        "summary_data_subsets": summary_data_subsets,
        "summary_sorted_all": summary_sorted_all,
        # Namespaces summary
        "___summary_global_namespaces": summary_global_namespaces,
        "summary_namespaces": summary_namespaces,
        # Move files and assets
        "moved_files": moved_files,
        "assets_backlinked": assets_backlinked,
        "assets_not_backlinked": assets_not_backlinked,
    }

    if args.write_graph:
        output_data["graph_content"] = graph_content_db

    # TODO Process journal keys to create a timeline
    journals_dangling = extract_journals_from_dangling_links(dangling_links)
    process_journals_timelines(summary_data_subsets["_is_journal"], journals_dangling)

    # TODO test shelf
    shelve_output_data = {
        # Main meta outputs
        "alphanum_dict": alphanum_dict,
        "alphanum_dict_ns": alphanum_dict_ns,
        "dangling_links": dangling_links,
        "config_edn_data": config_edn_data,
        "target_dirs": target_dirs,
        "graph_content": graph_content_db,
        "graph_data": graph_data,
        "content_patterns": content_patterns,
        "config_patterns": config_patterns,
        "all_refs": all_refs,
        "dangling_dict": dangling_dict,
        # Properties
        "set_all_prop_values_builtin": set_all_prop_values_builtin,
        "set_all_prop_values_user": set_all_prop_values_user,
        "sorted_all_props_builtin": sorted_all_props_builtin,
        "sorted_all_props_user": sorted_all_props_user,
        # General summary
        "___summary_global": summary_global,
        **summary_data_subsets,
        **summary_sorted_all,
        # Namespaces summary
        "___summary_global_namespaces": summary_global_namespaces,
        **summary_namespaces,
        # Move files and assets
        "moved_files": moved_files,
        "assets_backlinked": assets_backlinked,
        "assets_not_backlinked": assets_not_backlinked,
    }

    with shelve.open("mydata") as db:
        for key, values in shelve_output_data.items():
            db[key] = values

    # TODO write config to file
    with open("user_config.ini", "w") as config_file:
        CONFIG.write(config_file)

    return output_data
