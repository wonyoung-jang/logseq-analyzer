import logging
from src.compile_regex import *
from src.namespace import *
from src.setup import *
from src.core import *


def run_app():
    """
    Main function to run the Logseq analyzer.
    """
    # Setup command line arguments
    args = setup_logseq_analyzer_args()

    # Setup output directory and logging
    output_dir = setup_output_directory()
    setup_logging(output_dir)

    # Get graph folder and extract bak and recycle directories
    logseq_graph_dir = Path(args.graph_folder)
    logseq_dir = get_sub_file_or_folder(logseq_graph_dir, config.DEFAULT_LOGSEQ_DIR)
    recycle_dir = get_sub_file_or_folder(logseq_dir, config.DEFAULT_RECYCLE_DIR)
    bak_dir = get_sub_file_or_folder(logseq_dir, config.DEFAULT_BAK_DIR)

    # Compile regex patterns
    content_patterns = compile_re_content()
    config_patterns = compile_re_config()

    # Get configs
    config_file = get_sub_file_or_folder(logseq_dir, config.DEFAULT_CONFIG_FILE)
    config_edn_content = get_logseq_config_edn_content(config_file)
    config_edn_data = get_logseq_config_edn(config_edn_content, config_patterns)
    config_edn_data = {**config.CONFIG_EDN_DATA, **config_edn_data}
    if args.global_config:
        global_config_edn_file = config.GLOBAL_CONFIG_FILE = Path(args.global_config)
        global_config_edn_content = get_logseq_config_edn_content(global_config_edn_file)
        global_config_edn_data = get_logseq_config_edn(global_config_edn_content, config_patterns)
        config_edn_data = {**config_edn_data, **global_config_edn_data}

    # Get target directories
    target_dirs = get_target_dirs(config_edn_data)

    # Process graph files
    graph_meta_data, meta_graph_content = process_graph_files(logseq_graph_dir, content_patterns, target_dirs)

    # Core data analysis
    (
        meta_alphanum_dictionary,
        meta_dangling_links,
        graph_content_data,
        graph_summary_data,
    ) = core_data_analysis(content_patterns, graph_meta_data, meta_graph_content)

    # Generate summary subsets
    summary_data_subsets = generate_summary_subsets(output_dir, graph_summary_data)

    # Write initial outputs
    write_initial_outputs(
        args,
        output_dir,
        meta_alphanum_dictionary,
        meta_dangling_links,
        meta_graph_content,
        graph_meta_data,
        graph_content_data,
        graph_summary_data,
    )

    # Generate global summary
    generate_global_summary(output_dir, summary_data_subsets)

    # Handle assets
    handle_assets(args, output_dir, graph_meta_data, graph_content_data, graph_summary_data, summary_data_subsets)

    # Handle bak and recycle directories
    handle_bak_recycle(args, bak_dir, recycle_dir)

    # Namespaces analysis
    process_namespace_data(output_dir, graph_content_data, meta_dangling_links)

    logging.info("Logseq Analyzer completed.")
