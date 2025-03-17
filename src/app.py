from pathlib import Path

from src import config
from src.compile_regex import compile_re_content, compile_re_config
from src.namespace import process_namespace_data
from src.reporting import write_many_outputs
from src.setup import (
    get_logseq_analyzer_args,
    create_output_directory,
    create_log_file,
    get_logseq_config_edn,
    get_logseq_target_dirs,
    set_logseq_config_edn_data,
    validate_path,
    get_sub_file_or_folder,
)
from src.core import (
    create_delete_directory,
    generate_sorted_summary_all,
    handle_assets,
    handle_move_files,
    process_graph_files,
    core_data_analysis,
    generate_summary_subsets,
    generate_global_summary,
    generate_graph_visualization,
)


def run_app(**kwargs):
    """Main function to run the Logseq analyzer."""

    # Setup variables
    gui_inst = "gui_instance"
    setup_phase = "setup"
    process_files_phase = "process_files"
    reporting_phase = "reporting"
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

    if args.visualize_graph:  # Check for visualize_graph argument
        generate_graph_visualization(graph_data, config.DEFAULT_OUTPUT_DIR)  # Call graph viz function

    if gui_instance:
        gui_instance.update_progress(process_files_phase, 100)
        gui_instance.update_progress(reporting_phase, 20)
    #################################################################
    # Phase 03: Reporting/writing outputs
    #################################################################
    # Write initial outputs
    initial_outputs = {
        "alphanum_dict": alphanum_dict,
        "alphanum_dict_ns": alphanum_dict_ns,
        "dangling_links": dangling_links,
        "target_dirs": target_dirs,
        "graph_data": graph_data,
    }

    if args.write_graph:
        initial_outputs["graph_content"] = graph_content_bullets

    write_many_outputs(args, config.OUTPUT_DIR_META, **initial_outputs)

    # Generate summary
    summary_data_subsets = generate_summary_subsets(graph_data)
    generate_global_summary(summary_data_subsets, config.OUTPUT_DIR_SUMMARY)

    generate_sorted_summary_all(graph_data, config.OUTPUT_DIR_TEST)

    if gui_instance:
        gui_instance.update_progress(reporting_phase, 100)
        gui_instance.update_progress(namespaces_phase, 20)
    ################################################################
    # Phase 04: Process namespaces
    ################################################################
    # Namespaces analysis
    process_namespace_data(graph_data, dangling_links)

    if gui_instance:
        gui_instance.update_progress(namespaces_phase, 100)
        gui_instance.update_progress(move_files_phase, 20)
    #####################################################################
    # Phase 05: Move files to a delete directory (optional)
    #####################################################################
    if move:
        # Create delete directory
        to_delete_dir = create_delete_directory()

        # Handle assets
        summary_is_asset_not_backlinked = handle_assets(graph_data, summary_data_subsets, to_delete_dir)

        # Handle bak and recycle directories
        handle_move_files(args, graph_data, summary_is_asset_not_backlinked, bak_dir, recycle_dir, to_delete_dir)

    if gui_instance:
        gui_instance.update_progress(move_files_phase, 100)
