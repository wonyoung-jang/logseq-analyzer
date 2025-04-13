import re
import pytest
from ..patterns import (
    AdvancedCommandPatterns,
    CodePatterns,
    ContentPatterns,
    DoubleCurlyBracketsPatterns,
    DoubleParenthesesPatterns,
    EmbeddedLinksPatterns,
    ExternalLinksPatterns,
)


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


@pytest.fixture
def conp():
    return ContentPatterns()


@pytest.fixture
def dcbp():
    return DoubleCurlyBracketsPatterns()


@pytest.fixture
def acp():
    return AdvancedCommandPatterns()


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


# CONTENT PATTERNS
def test_compile_re_content_populates_content_dict(conp):
    assert hasattr(conp, "bullet")
    assert isinstance(conp.bullet, re.Pattern)


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
        ("http://example.com", "any_link", True),
    ],
)
def test_content_patterns(conp, text, key, should_match):
    pattern = getattr(conp, key)
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


# DOUBLE-CURLY PATTERNS
def test_compile_re_content_double_curly_brackets_populates_dblcurly_dict(dcbp):
    assert hasattr(dcbp, "all")
    assert isinstance(dcbp.all, re.Pattern)


@pytest.mark.parametrize(
    "text,key,should_match",
    [
        ("{{macro}}", "all", True),
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
        ("no curly here", "all", False),
    ],
)
def test_dblcurly_patterns(dcbp, text, key, should_match):
    pattern = getattr(dcbp, key)
    assert bool(pattern.search(text)) is should_match


# ADVANCED COMMANDS PATTERNS
def test_compile_re_content_advanced_command_populates_advcommand_dict(acp):
    assert hasattr(acp, "all")
    assert isinstance(acp.all, re.Pattern)


@pytest.mark.parametrize(
    "text,key,should_match",
    [
        ("#+BEGIN_something\ncontent\n#+END_something\n", "all", True),
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
def test_advcommand_patterns(acp, text, key, should_match):
    pattern = getattr(acp, key)
    assert bool(pattern.search(text)) is should_match
