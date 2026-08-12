"""Editor data model."""

from __future__ import annotations

from dataclasses import asdict, dataclass


@dataclass
class EditorInfo:
    id: str  # stable catalog id, e.g. "vscode", or "manual:<uuid>"
    display_name: str
    executable_path: str
    kind: str  # "detected" | "manual"
    launch_strategy: str  # "cli" | "mac_open"
    launch_template: list[str]  # argv template; "{path}" replaced with project path
    # For mac_open strategy: the .app bundle name to pass to `open -a`.
    app_bundle: str | None = None

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> EditorInfo:
        return cls(
            id=data["id"],
            display_name=data.get("display_name", data["id"]),
            executable_path=data.get("executable_path", ""),
            kind=data.get("kind", "detected"),
            launch_strategy=data.get("launch_strategy", "cli"),
            launch_template=list(data.get("launch_template", [])),
            app_bundle=data.get("app_bundle"),
        )
