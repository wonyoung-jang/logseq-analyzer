import logging
from src.compile_regex import compile_re_content
from src.namespace import process_namespace_data
from src.setup import *
from src.core import *


def run_app():
    """
    Main function to run the Logseq analyzer.
    """
    # Setup command line arguments
    args = setup_logseq_analyzer_args()

    # Get graph folder
    logseq_graph_dir = Path(args.graph_folder)

    # Setup output directory
    output_dir = setup_output_directory()

    # Setup logging
    setup_logging(output_dir)

    # Extract Logseq configuration and directories
    target_dirs, config_edn_data = get_logseq_config_edn(logseq_graph_dir, args)

    # Extract bak and recycle directories
    logseq_dir = get_sub_folder(logseq_graph_dir, config.DEFAULT_LOGSEQ_DIR)
    recycle_dir = get_sub_folder(logseq_dir, config.DEFAULT_RECYCLE_DIR)
    bak_dir = get_sub_folder(logseq_dir, config.DEFAULT_BAK_DIR)

    # Compile regex patterns
    content_patterns = compile_re_content()

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
