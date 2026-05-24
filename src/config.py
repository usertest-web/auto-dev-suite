# src/config.py
from dataclasses import dataclass, field
from typing import Optional
import yaml
import os


@dataclass
class LLMConfig:
    provider: str = "claude"
    model: str = "claude-sonnet-4-6"
    api_key_env: str = "ANTHROPIC_API_KEY"

    def get_api_key(self) -> str:
        key = os.environ.get(self.api_key_env)
        if not key:
            raise ValueError(f"Environment variable {self.api_key_env} not set")
        return key


@dataclass
class AcademicDBConfig:
    cnki_proxy: Optional[str] = None
    fallback: str = "semantic_scholar"


@dataclass
class Config:
    mode: str = "interactive"
    llm: LLMConfig = field(default_factory=LLMConfig)
    academic_db: AcademicDBConfig = field(default_factory=AcademicDBConfig)
    output_dir: str = "./output"
    template_path: str = "./data/template.docx"
    spec_path: str = "./data/format-spec.pdf"


def load_config(path: str = "config.yaml") -> Config:
    if not os.path.exists(path):
        raise FileNotFoundError(f"Config file not found: {path}")
    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    llm_data = data.get("llm", {})
    llm = LLMConfig(
        provider=llm_data.get("provider", "claude"),
        model=llm_data.get("model", "claude-sonnet-4-6"),
        api_key_env=llm_data.get("api_key_env", "ANTHROPIC_API_KEY"),
    )
    db_data = data.get("academic_db", {})
    academic_db = AcademicDBConfig(
        cnki_proxy=db_data.get("cnki_proxy"),
        fallback=db_data.get("fallback", "semantic_scholar"),
    )
    return Config(
        mode=data.get("mode", "interactive"),
        llm=llm,
        academic_db=academic_db,
        output_dir=data.get("output_dir", "./output"),
        template_path=data.get("template_path", "./data/template.docx"),
        spec_path=data.get("spec_path", "./data/format-spec.pdf"),
    )
