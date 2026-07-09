from __future__ import annotations

import json
from pathlib import Path

from app.models.template_config import TemplateConfig


class TemplateManager:
    def save(self, config: TemplateConfig, path: str | Path) -> None:
        target = Path(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(
            json.dumps(config.to_dict(), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def load(self, path: str | Path) -> TemplateConfig:
        source = Path(path)
        data = json.loads(source.read_text(encoding="utf-8"))
        return TemplateConfig.from_dict(data)
