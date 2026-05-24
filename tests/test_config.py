import pytest
from src.config import Config, load_config

def test_load_config_parses_yaml():
    yaml_content = """
mode: auto
llm:
  provider: claude
  model: claude-sonnet-4-6
  api_key_env: ANTHROPIC_API_KEY
academic_db:
  cnki_proxy: null
  fallback: semantic_scholar
output_dir: ./output
template_path: ./data/template.docx
spec_path: ./data/format-spec.pdf
"""
    import tempfile, os
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        f.write(yaml_content)
        tmp_path = f.name
    try:
        config = load_config(tmp_path)
        assert config.mode == "auto"
        assert config.llm.provider == "claude"
        assert config.llm.model == "claude-sonnet-4-6"
        assert config.llm.api_key_env == "ANTHROPIC_API_KEY"
        assert config.academic_db.cnki_proxy is None
        assert config.academic_db.fallback == "semantic_scholar"
        assert config.output_dir == "./output"
    finally:
        os.unlink(tmp_path)

def test_load_config_missing_file_raises():
    with pytest.raises(FileNotFoundError):
        load_config("./nonexistent.yaml")

def test_get_api_key_returns_env_value(monkeypatch):
    from src.config import LLMConfig
    monkeypatch.setenv("TEST_KEY", "sk-test-123")
    cfg = LLMConfig(api_key_env="TEST_KEY")
    assert cfg.get_api_key() == "sk-test-123"

def test_get_api_key_raises_when_not_set():
    from src.config import LLMConfig
    cfg = LLMConfig(api_key_env="NONEXISTENT_KEY_PLEASE")
    with pytest.raises(ValueError, match="Environment variable"):
        cfg.get_api_key()

def test_load_config_applies_defaults_for_missing_keys():
    yaml_content = "mode: auto\n"
    import tempfile, os
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        f.write(yaml_content)
        tmp_path = f.name
    try:
        config = load_config(tmp_path)
        assert config.mode == "auto"
        # These should get defaults
        assert config.llm.provider == "claude"
        assert config.output_dir == "./output"
    finally:
        os.unlink(tmp_path)
