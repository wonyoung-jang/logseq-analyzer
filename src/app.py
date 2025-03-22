from pathlib import Path

from src import config
from .compile_regex import compile_re_config, compile_re_content
from .core import (
    core_data_analysis,
    generate_global_summary,
    generate_sorted_summary_all,
    generate_summary_subsets,
    process_graph_files,
)
from .logseq_assets import handle_assets
from .logseq_move_files import create_delete_directory, handle_move_files
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


def run_app(**kwargs):
    """Main function to run the Logseq analyzer."""

    # Setup variables
    gui_inst = "gui_instance"
    setup_phase = "setup"
    process_files_phase = "process_files"
    summary_phase = "summary"
    namespaces_phase = "namespaces"
    move_files_phase = "move_files"
    gui_instance = kwargs.get(gui_inst)

    ###################################################################
    # Phase 01: Setup
    ###################################################################
    if gui_instance:
        gui_instance.update_progress(setup_phase, 20)

    # Parse command line arguments or GUI arguments
    args = get_logseq_analyzer_args(**kwargs)
    move_bak = args.move_bak
    move_recycle = args.move_recycle
    move_assets = args.move_unlinked_assets
    move = any([move_bak, move_recycle, move_assets])

    # Setup output directory and logging
    create_output_directory()
    create_log_file()

    # Get graph folder and extract bak and recycle directories
    logseq_graph_dir = Path(args.graph_folder)
    validate_path(logseq_graph_dir)
    logseq_dir = get_sub_file_or_folder(logseq_graph_dir, config.DEFAULT_LOGSEQ_DIR)
    recycle_dir = get_sub_file_or_folder(logseq_dir, config.DEFAULT_RECYCLE_DIR)
    bak_dir = get_sub_file_or_folder(logseq_dir, config.DEFAULT_BAK_DIR)

    # Compile regex patterns
    content_patterns = compile_re_content()
    config_patterns = compile_re_config()

    # Get config data and target directories
    config_edn_data = get_logseq_config_edn(args, logseq_dir, config_patterns)
    set_logseq_config_edn_data(config_edn_data)
    target_dirs = get_logseq_target_dirs()
    config.REPORT_FORMAT = args.report_format

    if gui_instance:
        gui_instance.update_progress(setup_phase, 100)
        gui_instance.update_progress(process_files_phase, 20)

    ################################################################
    # Phase 02: Process files
    ################################################################
    # Process graph files
    graph_data, graph_content_bullets = process_graph_files(logseq_graph_dir, content_patterns, target_dirs)

    # Core data analysis
    (
        alphanum_dict,
        alphanum_dict_ns,
        dangling_links,
        graph_data,
    ) = core_data_analysis(graph_data)

    if gui_instance:
        gui_instance.update_progress(process_files_phase, 100)
        gui_instance.update_progress(summary_phase, 20)

    #################################################################
    # Phase 03: Process summaries
    #################################################################
    # Generate summary
    summary_data_subsets = generate_summary_subsets(graph_data)
    summary_global = generate_global_summary(summary_data_subsets)
    summary_sorted_all = generate_sorted_summary_all(graph_data)

    if gui_instance:
        gui_instance.update_progress(summary_phase, 100)
        gui_instance.update_progress(namespaces_phase, 20)

    ################################################################
    # Phase 04: Process namespaces
    ################################################################
    # Namespaces analysis
    summary_namespaces, summary_global_namespaces = process_namespace_data(graph_data, dangling_links)

    if gui_instance:
        gui_instance.update_progress(namespaces_phase, 100)
        gui_instance.update_progress(move_files_phase, 20)

    #####################################################################
    # Phase 05: Move files to a delete directory (optional)
    #####################################################################
    moved_files = None
    assets_backlinked = None
    assets_not_backlinked = None
    if move:
        # Create delete directory
        to_delete_dir = create_delete_directory()
        # Handle assets
        assets_backlinked, assets_not_backlinked = handle_assets(graph_data, summary_data_subsets)
        # Handle bak and recycle directories
        moved_files = handle_move_files(args, graph_data, assets_not_backlinked, bak_dir, recycle_dir, to_delete_dir)

    if gui_instance:
        gui_instance.update_progress(move_files_phase, 100)

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
        output_data["graph_content"] = graph_content_bullets

    return output_data
