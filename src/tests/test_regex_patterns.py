import re
import pytest
from ..regex_patterns import RegexPatterns


@pytest.fixture
def rp():
    return RegexPatterns()


# Test compilation of code patterns
def test_compile_re_code_populates_code_dict(rp):
    rp.compile_re_code()
    assert isinstance(rp.code, dict)
    assert "multiline_code_block" in rp.code
    assert isinstance(rp.code["multiline_code_block"], re.Pattern)


@pytest.mark.parametrize(
    "text,key,should_match",
    [
        ("```print('hello')\n```", "multiline_code_block", True),
        ("```calc 1+1\n```", "calc_block", True),
        ("```python\nx=1\n```", "multiline_code_lang", True),
        ("`x=1`", "inline_code_block", True),
        ("no backticks here", "multiline_code_block", False),
    ],
)
def test_code_patterns(rp, text, key, should_match):
    rp.compile_re_code()
    pattern = rp.code[key]
    assert bool(pattern.search(text)) is should_match


# Test compilation of content patterns
def test_compile_re_content_populates_content_dict(rp):
    rp.compile_re_content()
    assert "bullet" in rp.content
    assert isinstance(rp.content["bullet"], re.Pattern)


@pytest.mark.parametrize(
    "text,key,should_match",
    [
        ("- item", "bullet", True),
        ("[[Page Name]]", "page_reference", True),
        ("#[[Backlink]]", "tagged_backlink", True),
        ("#tag", "tag", True),
        ("key:: value", "property", True),
        ("key::value", "property_value", True),
        ("assets/image.png)", "asset", True),
        ("[[draws/sketch.excalidraw]]", "draw", True),
        ("- > quote", "blockquote", True),
        ("- Q? #card", "flashcard", True),
        ("((ref))", "reference", True),
        ("((123e4567-e89b-12d3-a456-426614174000))", "block_reference", True),
        ("<% var %>", "dynamic_variable", True),
        ("no match here", "page_reference", False),
    ],
)
def test_content_patterns(rp, text, key, should_match):
    rp.compile_re_content()
    pattern = rp.content[key]
    assert bool(pattern.search(text)) is should_match


# Test compilation of embedded links patterns
def test_compile_re_emb_links_populates_emb_links_dict(rp):
    rp.compile_re_emb_links()
    assert "embedded_link" in rp.emb_links
    assert isinstance(rp.emb_links["embedded_link"], re.Pattern)


@pytest.mark.parametrize(
    "text,key,should_match",
    [
        ("![alt](url)", "embedded_link", True),
        ("![alt](http://example.com)", "embedded_link_internet", True),
        ("![alt](assets/img.png)", "embedded_link_asset", True),
        ("[not embedded](url)", "embedded_link", False),
    ],
)
def test_emb_links_patterns(rp, text, key, should_match):
    rp.compile_re_emb_links()
    pattern = rp.emb_links[key]
    assert bool(pattern.search(text)) is should_match


# Test compilation of external links patterns
def test_compile_re_ext_links_populates_ext_links_dict(rp):
    rp.compile_re_ext_links()
    assert "external_link" in rp.ext_links
    assert isinstance(rp.ext_links["external_link"], re.Pattern)


@pytest.mark.parametrize(
    "text,key,should_match",
    [
        ("[Link](url)", "external_link", True),
        ("[Link](http://example.com)", "external_link_internet", True),
        ("[Alias]([[Page]])", "external_link_alias", True),
        ("![Embedded](url)", "external_link", False),
    ],
)
def test_ext_links_patterns(rp, text, key, should_match):
    rp.compile_re_ext_links()
    pattern = rp.ext_links[key]
    assert bool(pattern.search(text)) is should_match


# Test compilation of config patterns
def test_compile_re_config_populates_config_dict(rp):
    rp.compile_re_config()
    assert "journal_page_title_format_pattern" in rp.config
    assert isinstance(rp.config["journal_page_title_format_pattern"], re.Pattern)


@pytest.mark.parametrize(
    "text,key,should_match",
    [
        (
            ':journal/page-title-format "%Y-%m-%d"',
            "journal_page_title_format_pattern",
            True,
        ),
        (
            ':journal/file-name-format "%Y-%m-%d"',
            "journal_file_name_format_pattern",
            True,
        ),
        (":feature/enable-journals? true", "feature_enable_journals_pattern", True),
        (
            ":feature/enable-whiteboards? false",
            "feature_enable_whiteboards_pattern",
            True,
        ),
        (':pages-directory "pages"', "pages_directory_pattern", True),
        (':journals-directory "journals"', "journals_directory_pattern", True),
        (':whiteboards-directory "whiteboards"', "whiteboards_directory_pattern", True),
        (":file/name-format %Y%m%d", "file_name_format_pattern", True),
        ("invalid config line", "pages_directory_pattern", False),
    ],
)
def test_config_patterns(rp, text, key, should_match):
    rp.compile_re_config()
    pattern = rp.config[key]
    assert bool(pattern.search(text)) is should_match


# Test compilation of double-curly content patterns
def test_compile_re_content_double_curly_brackets_populates_dblcurly_dict(rp):
    rp.compile_re_content_double_curly_brackets()
    assert "macro" in rp.dblcurly
    assert isinstance(rp.dblcurly["macro"], re.Pattern)


@pytest.mark.parametrize(
    "text,key,should_match",
    [
        ("{{macro}}", "macro", True),
        ("{{embed [[Page]]}}", "embed", True),
        ("{{embed [[Page]]}}", "page_embed", True),
        ("{{embed ((123e4567-e89b-12d3-a456-426614174000))}}", "block_embed", True),
        ("{{namespace foo}}", "namespace_query", True),
        ("{{cards foo}}", "card", True),
        ("{{cloze foo}}", "cloze", True),
        ("{{query foo}}", "simple_query", True),
        ("{{function foo}}", "query_function", True),
        ("{{video foo}}", "embed_video_url", True),
        ("{{tweet foo}}", "embed_twitter_tweet", True),
        ("{{youtube-timestamp foo}}", "embed_youtube_timestamp", True),
        ("{{renderer foo}}", "renderer", True),
        ("no curly here", "macro", False),
    ],
)
def test_dblcurly_patterns(rp, text, key, should_match):
    rp.compile_re_content_double_curly_brackets()
    pattern = rp.dblcurly[key]
    assert bool(pattern.search(text)) is should_match


# Test compilation of advanced command patterns
def test_compile_re_content_advanced_command_populates_advcommand_dict(rp):
    rp.compile_re_content_advanced_command()
    assert "_all" in rp.advcommand
    assert isinstance(rp.advcommand["_all"], re.Pattern)


@pytest.mark.parametrize(
    "text,key,should_match",
    [
        ("#+BEGIN_EXPORT\ncontent\n#+END_EXPORT\n", "export", True),
        ("#+BEGIN_EXPORT ascii\ntext\n#+END_EXPORT\n", "export_ascii", True),
        ("#+BEGIN_EXPORT latex\ntext\n#+END_EXPORT\n", "export_latex", True),
        ("#+BEGIN_CAUTION\nc\n#+END_CAUTION\n", "caution", True),
        ("#+BEGIN_CENTER\nc\n#+END_CENTER\n", "center", True),
        ("#+BEGIN_COMMENT\nc\n#+END_COMMENT\n", "comment", True),
        ("#+BEGIN_EXAMPLE\nc\n#+END_EXAMPLE\n", "example", True),
        ("#+BEGIN_IMPORTANT\nc\n#+END_IMPORTANT\n", "important", True),
        ("#+BEGIN_NOTE\nc\n#+END_NOTE\n", "note", True),
        ("#+BEGIN_PINNED\nc\n#+END_PINNED\n", "pinned", True),
        ("#+BEGIN_QUERY\nc\n#+END_QUERY\n", "query", True),
        ("#+BEGIN_QUOTE\nc\n#+END_QUOTE\n", "quote", True),
        ("#+BEGIN_TIP\nc\n#+END_TIP\n", "tip", True),
        ("#+BEGIN_VERSE\nc\n#+END_VERSE\n", "verse", True),
        ("#+BEGIN_WARNING\nc\n#+END_WARNING\n", "warning", True),
        ("#+BEGIN_WARNIN\nfalse\n#+END_WARNIN\n", "warning", False),
        ("random text", "export", False),
    ],
)
def test_advcommand_patterns(rp, text, key, should_match):
    rp.compile_re_content_advanced_command()
    pattern = rp.advcommand[key]
    assert bool(pattern.search(text)) is should_match
