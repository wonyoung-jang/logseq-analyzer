from ..default_logseq_config_edn import DEFAULT_LOGSEQ_CONFIG_EDN


def test_default_logseq_config():
    assert DEFAULT_LOGSEQ_CONFIG_EDN is not None
    assert isinstance(DEFAULT_LOGSEQ_CONFIG_EDN, dict)
    assert ":meta/version" in DEFAULT_LOGSEQ_CONFIG_EDN
