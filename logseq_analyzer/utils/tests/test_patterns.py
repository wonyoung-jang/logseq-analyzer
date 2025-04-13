import re
import pytest
from ..patterns import CodePatterns, DoubleParenthesesPatterns, EmbeddedLinksPatterns, ExternalLinksPatterns, RegexPatterns


@pytest.fixture
def rp():
    return RegexPatterns()


@pytest.fixture
def emlp():
    return EmbeddedLinksPatterns()


@pytest.fixture
def exlp():
    return ExternalLinksPatterns()


@pytest.fixture
def dpp():
    return DoubleParenthesesPatterns()


@pytest.fixture
def cdep():
    return CodePatterns()


# CODE PATTERNS
def test_compile_re_code_populates_code_dict(cdep):
    assert hasattr(cdep, "all")
    assert isinstance(cdep.all, re.Pattern)


@pytest.mark.parametrize(
    "text,key,should_match",
    [
        ("```\nprint('hello')\n```", "all", True),
        ("```print('hello')\n```", "all", True),
        ("```calc 1+1\n```", "calc_block", True),
        ("```\ncalc 1+1\n```", "calc_block", False),
        ("```python\nx=1\n```", "multiline_code_lang", True),
        ("```\npython\nx=1\n```", "multiline_code_lang", False),
        ("`x=1`", "inline_code_block", True),
        ("`x\n=1`", "inline_code_block", False),
        ("no backticks here", "all", False),
        ("one `backtick here", "all", False),
        ("one `backtick here", "inline_code_block", False),
    ],
)
def test_code_patterns(cdep, text, key, should_match):
    pattern = getattr(cdep, key)
    assert bool(pattern.search(text)) is should_match


# TODO CONTENT PATTERNS
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
        ("<% var %>", "dynamic_variable", True),
        ("no match here", "page_reference", False),
    ],
)
def test_content_patterns(rp, text, key, should_match):
    rp.compile_re_content()
    pattern = rp.content[key]
    assert bool(pattern.search(text)) is should_match


# DOUBLE-PARENTHESES PATTERNS
def test_compile_re_dblparen_populates_dblparen_dict(dpp):
    assert hasattr(dpp, "all")
    assert isinstance(dpp.all, re.Pattern)


@pytest.mark.parametrize(
    "text,key,should_match",
    [
        ("((123e4567-e89b-12d3-a456 stf))", "all", True),
        ("((123e4567-e89b-12d3-a456-426614174000))", "block_reference", True),
    ],
)
def test_dblparen_patterns(dpp, text, key, should_match):
    pattern = getattr(dpp, key)
    assert bool(pattern.search(text)) is should_match


# EMBEDDED LINKS PATTERNS
def test_compile_re_emb_links_populates_emb_links_dict(emlp):
    assert hasattr(emlp, "all")
    assert isinstance(emlp.all, re.Pattern)


@pytest.mark.parametrize(
    "text,key,should_match",
    [
        ("![alt](url)", "all", True),
        ("![alt](http://example.com)", "internet", True),
        ("![alt](assets/img.png)", "asset", True),
        ("[not embedded](url)", "all", False),
    ],
)
def test_emb_links_patterns(emlp, text, key, should_match):
    pattern = getattr(emlp, key)
    assert bool(pattern.search(text)) is should_match


# EXTERNAL LINKS PATTERNS
def test_compile_re_ext_links_populates_ext_links_dict(exlp):
    assert hasattr(exlp, "all")
    assert isinstance(exlp.all, re.Pattern)


@pytest.mark.parametrize(
    "text,key,should_match",
    [
        ("[Link](url)", "all", True),
        ("[Link](http://example.com)", "internet", True),
        ("[Alias]([[Page]])", "alias", True),
        ("![Embedded](url)", "all", False),
    ],
)
def test_ext_links_patterns(exlp, text, key, should_match):
    pattern = getattr(exlp, key)
    assert bool(pattern.search(text)) is should_match


# TODO DOUBLE-CURLY PATTERNS
def test_compile_re_content_double_curly_brackets_populates_dblcurly_dict(rp):
    rp.compile_re_content_double_curly_brackets()
    assert "_all" in rp.dblcurly
    assert isinstance(rp.dblcurly["_all"], re.Pattern)


@pytest.mark.parametrize(
    "text,key,should_match",
    [
        ("{{macro}}", "_all", True),
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
        ("no curly here", "_all", False),
    ],
)
def test_dblcurly_patterns(rp, text, key, should_match):
    rp.compile_re_content_double_curly_brackets()
    pattern = rp.dblcurly[key]
    assert bool(pattern.search(text)) is should_match


# TODO ADVANCED COMMANDS PATTERNS
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


# Test Capture Groups
# @pytest.mark.parametrize(
#     "compile_method, dict_name, key, text, group_index, expected",
#     [
#         # content patterns with capture groups
#         ("compile_re_content", "content", "page_reference", "[[Page Name]]", 1, "Page Name"),
#         ("compile_re_content", "content", "property", "key:: value", 1, "key"),
#         ("compile_re_content", "content", "property_value", "key::value", 1, "key"),
#         ("compile_re_content", "content", "property_value", "key::value", 2, "value"),
#         ("compile_re_content", "content", "asset", "assets/image.png)", 1, "image.png)"),
#         ("compile_re_content", "content", "draw", "[[draws/sketch.excalidraw]]", 1, "sketch"),
#         # patterns without capture groups → test full match
#         # (
#         #     "compile_re_content",
#         #     "dblparen",
#         #     "block_reference",
#         #     "((123e4567-e89b-12d3-a456-426614174000))",
#         #     0,
#         #     "((123e4567-e89b-12d3-a456-426614174000))",
#         # ),
#         ("compile_re_content", "content", "dynamic_variable", "<% var %>", 0, "<% var %>"),
#         # external & embedded links
#         # (
#         #     "compile_re_ext_links",
#         #     "ext_links",
#         #     "external_link_internet",
#         #     "[Link](http://example.com)",
#         #     0,
#         #     "[Link](http://example.com)",
#         # ),
#         # (
#         #     "compile_re_emb_links",
#         #     "emb_links",
#         #     "embedded_link_asset",
#         #     "![alt](assets/img.png)",
#         #     0,
#         #     "![alt](assets/img.png)",
#         # ),
#         # double-curly patterns
#         ("compile_re_content_double_curly_brackets", "dblcurly", "_all", "{{macro}}", 0, "{{macro}}"),
#         (
#             "compile_re_content_double_curly_brackets",
#             "dblcurly",
#             "page_embed",
#             "{{embed [[Page]]}}",
#             0,
#             "{{embed [[Page]]}}",
#         ),
#         (
#             "compile_re_content_double_curly_brackets",
#             "dblcurly",
#             "block_embed",
#             "{{embed ((123e4567-e89b-12d3-a456-426614174000))}}",
#             0,
#             "{{embed ((123e4567-e89b-12d3-a456-426614174000))}}",
#         ),
#     ],
# )
# def test_pattern_capture_groups(rp, compile_method, dict_name, key, text, group_index, expected):
#     # compile the appropriate set of patterns
#     getattr(rp, compile_method)()
#     patterns = getattr(rp, dict_name)
#     pattern = patterns[key]
#     m = pattern.search(text)
#     assert m is not None, f"Pattern '{key}' did not match '{text}'"
#     assert m.group(group_index) == expected
