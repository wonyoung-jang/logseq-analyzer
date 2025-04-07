from src.regex_patterns import RegexPatterns

PATTERNS = RegexPatterns()
PATTERNS.compile_re_content()


def test_tag_re():
    tag_re = PATTERNS.content["tag"]
    test_tags = {
        "#tag": "tag",
        "#tag nottag": "tag",
        "# tag": "",
        "#tag#": "tag",
        "##tag": "tag",
        "#tag#tag": "tag",
        "#tag tag": "tag",
        "#[tag]": "[tag]",
        "#tag [tag]": "tag",
        "#tag [tag] nottag": "tag",
        "tag #[tag]extra": "[tag]extra",
        "# notatag [tag] #tag": "tag",
        "#[[tag]]": "",
    }
    for test_string, expected in test_tags.items():
        results = tag_re.findall(test_string)
        print(results)
        if expected:
            assert results[0] == expected, f"Expected '{expected}' for '{test_string}', got '{results[0]}'"
        else:
            assert len(results) == 0, f"Expected no match for '{test_string}', got {len(results)}"
