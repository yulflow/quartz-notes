#!/usr/bin/env python3

import json
import os
import re
import sys
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

API_BASE_URL = "https://hub.yulflow.dev"
ENV_FILE_PATH = Path("/Volumes/Seoyul2T/Coding/workflow-hub/.env.local")
VAULT_PATH = Path(
    "~/Library/CloudStorage/GoogleDrive-chaedamflow@gmail.com/내 드라이브/Obsidian"
).expanduser()

INVALID_FILENAME_CHARS = re.compile(r'[\\/:*?"<>|]')


def sanitize_filename(name: str) -> str:
    sanitized = INVALID_FILENAME_CHARS.sub("-", (name or "").strip())
    sanitized = re.sub(r"\s+", " ", sanitized).strip(" .")
    return sanitized or "untitled"


def normalize_tags(tags_value):
    if tags_value is None:
        return []

    if isinstance(tags_value, list):
        return [str(tag).strip() for tag in tags_value if str(tag).strip()]

    if isinstance(tags_value, str):
        value = tags_value.strip()
        if not value:
            return []
        if value.startswith("[") and value.endswith("]"):
            try:
                parsed = json.loads(value)
                if isinstance(parsed, list):
                    return [str(tag).strip() for tag in parsed if str(tag).strip()]
            except json.JSONDecodeError:
                pass
        return [tag.strip() for tag in value.split(",") if tag.strip()]

    return [str(tags_value).strip()] if str(tags_value).strip() else []


def yaml_tags_inline(tags_value) -> str:
    tags = normalize_tags(tags_value)
    return "[" + ", ".join(json.dumps(tag, ensure_ascii=False) for tag in tags) + "]"


def yaml_value(value) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    if value is None:
        return '""'
    if isinstance(value, (int, float)):
        return str(value)
    return json.dumps(str(value), ensure_ascii=False)


def build_frontmatter(field_order, data: dict) -> str:
    lines = ["---"]
    for key in field_order:
        if key == "tags":
            lines.append(f"{key}: {yaml_tags_inline(data.get(key))}")
            continue
        lines.append(f"{key}: {yaml_value(data.get(key))}")
    lines.append("---")
    return "\n".join(lines)


def read_api_key() -> str:
    key_from_env = os.getenv("WH_API_KEY", "").strip()
    if key_from_env:
        return key_from_env

    try:
        with ENV_FILE_PATH.open("r", encoding="utf-8") as f:
            for raw_line in f:
                line = raw_line.strip().replace("\r", "")
                if not line or line.startswith("#"):
                    continue
                if not line.startswith("API_KEY="):
                    continue
                value = line.split("=", 1)[1].strip().replace("\r", "")
                if len(value) >= 2 and value[0] == value[-1] and value[0] in ("'", '"'):
                    value = value[1:-1]
                value = value.strip()
                if value:
                    return value
    except FileNotFoundError:
        pass
    except OSError as exc:
        print(f"[오류] .env.local 읽기 실패: {exc}")

    return ""


def fetch_api_data(path: str, api_key: str, params=None):
    query = f"?{urlencode(params)}" if params else ""
    url = f"{API_BASE_URL}{path}{query}"
    request = Request(
        url,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Accept": "application/json",
        },
        method="GET",
    )
    try:
        with urlopen(request, timeout=30) as response:
            payload = response.read().decode("utf-8")
        decoded = json.loads(payload)
        if isinstance(decoded, dict) and "data" in decoded:
            return decoded.get("data")
        return decoded
    except HTTPError as exc:
        error_body = ""
        try:
            error_body = exc.read().decode("utf-8", errors="ignore")
        except Exception:
            error_body = ""
        print(f"[오류] {path} 요청 실패 (HTTP {exc.code}): {error_body[:200]}")
    except URLError as exc:
        print(f"[오류] {path} 요청 실패 (네트워크): {exc.reason}")
    except json.JSONDecodeError as exc:
        print(f"[오류] {path} 응답 JSON 파싱 실패: {exc}")
    except Exception as exc:
        print(f"[오류] {path} 처리 실패: {exc}")
    return None


def ensure_dir(path: Path):
    path.mkdir(parents=True, exist_ok=True)


def write_markdown(file_path: Path, frontmatter: str, body: str):
    ensure_dir(file_path.parent)
    text = f"{frontmatter}\n\n{body.strip()}\n"
    file_path.write_text(text, encoding="utf-8")


def sync_references(api_key: str) -> int:
    data = fetch_api_data("/api/v1/references", api_key, params={"details": "true"})
    if not isinstance(data, list):
        print("[오류] references 응답 형식이 올바르지 않습니다.")
        return 0

    synced = 0
    out_dir = VAULT_PATH / "Research"
    ensure_dir(out_dir)

    for item in data:
        if not isinstance(item, dict):
            continue

        content = str(item.get("content") or "").strip()
        if not content:
            continue

        title = str(item.get("title") or item.get("id") or "untitled").strip()
        filename = sanitize_filename(title) + ".md"
        file_path = out_dir / filename

        frontmatter = build_frontmatter(
            [
                "title",
                "category",
                "tags",
                "url",
                "source",
                "source_id",
                "updated_at",
                "publish",
            ],
            {
                "title": title,
                "category": item.get("category"),
                "tags": item.get("tags"),
                "url": item.get("url"),
                "source": "workflow-hub",
                "source_id": item.get("id"),
                "updated_at": item.get("updated_at"),
                "publish": False,
            },
        )

        write_markdown(file_path, frontmatter, content)
        synced += 1

    return synced


def sync_watchlist(api_key: str) -> int:
    data = fetch_api_data("/api/v1/watchlist", api_key)
    if not isinstance(data, list):
        print("[오류] watchlist 응답 형식이 올바르지 않습니다.")
        return 0

    synced = 0
    out_dir = VAULT_PATH / "Research" / "watchlist"
    ensure_dir(out_dir)

    for item in data:
        if not isinstance(item, dict):
            continue

        content = str(item.get("content") or "").strip()
        if not content:
            continue

        notes = str(item.get("notes") or "").strip()
        body_parts = [part for part in [notes, content] if part]
        body = "\n\n".join(body_parts)

        title = str(item.get("title") or item.get("id") or "untitled").strip()
        filename = sanitize_filename(title) + ".md"
        file_path = out_dir / filename

        frontmatter = build_frontmatter(
            [
                "title",
                "category",
                "status",
                "tags",
                "url",
                "source",
                "source_id",
                "updated_at",
                "publish",
            ],
            {
                "title": title,
                "category": item.get("category"),
                "status": item.get("status"),
                "tags": item.get("tags"),
                "url": item.get("url"),
                "source": "workflow-hub",
                "source_id": item.get("id"),
                "updated_at": item.get("updated_at"),
                "publish": False,
            },
        )

        write_markdown(file_path, frontmatter, body)
        synced += 1

    return synced


def get_plan_items(api_key: str, plan: dict):
    inline_items = plan.get("items")
    if isinstance(inline_items, list):
        return inline_items

    alt_items = plan.get("plan_items")
    if isinstance(alt_items, list):
        return alt_items

    plan_id = plan.get("id")
    if not plan_id:
        return []

    detail = fetch_api_data(f"/api/v1/plans/{plan_id}", api_key)
    if isinstance(detail, dict):
        if isinstance(detail.get("items"), list):
            return detail.get("items")
        if isinstance(detail.get("plan_items"), list):
            return detail.get("plan_items")

    return []


def sync_plans(api_key: str) -> int:
    data = fetch_api_data("/api/v1/plans", api_key)
    if not isinstance(data, list):
        print("[오류] plans 응답 형식이 올바르지 않습니다.")
        return 0

    synced = 0
    out_dir = VAULT_PATH / "Projects"
    ensure_dir(out_dir)

    for plan in data:
        if not isinstance(plan, dict):
            continue

        title = str(plan.get("title") or plan.get("id") or "untitled").strip()
        filename = sanitize_filename(title) + ".md"
        file_path = out_dir / filename

        description = str(plan.get("description") or "").strip()
        items = get_plan_items(api_key, plan)

        checklist_lines = []
        sorted_items = sorted(
            [item for item in items if isinstance(item, dict)],
            key=lambda x: int(x.get("sort_order") or 0),
        )

        for item in sorted_items:
            status = str(item.get("status") or "").strip()
            checked = "x" if status == "done" else " "
            item_title = str(item.get("title") or "").strip()
            if not item_title:
                continue
            checklist_lines.append(f"- [{checked}] {item_title}")
            item_description = str(item.get("description") or "").strip()
            if item_description:
                checklist_lines.append(f"  - {item_description}")

        body_parts = []
        if description:
            body_parts.append(description)
        if checklist_lines:
            body_parts.append("\n".join(checklist_lines))
        body = "\n\n".join(body_parts).strip()

        frontmatter = build_frontmatter(
            [
                "title",
                "status",
                "project",
                "source",
                "source_id",
                "created_at",
                "completed_at",
                "publish",
            ],
            {
                "title": title,
                "status": plan.get("status"),
                "project": plan.get("project"),
                "source": "workflow-hub",
                "source_id": plan.get("id"),
                "created_at": plan.get("created_at"),
                "completed_at": plan.get("completed_at"),
                "publish": False,
            },
        )

        write_markdown(file_path, frontmatter, body)
        synced += 1

    return synced


def main():
    api_key = read_api_key()
    if not api_key:
        print("[오류] API 키를 찾을 수 없습니다. WH_API_KEY 또는 .env.local의 API_KEY를 확인하세요.")
        sys.exit(1)

    references_count = sync_references(api_key)
    watchlist_count = sync_watchlist(api_key)
    plans_count = sync_plans(api_key)

    print(
        f"References: {references_count}개, Watchlist: {watchlist_count}개, Plans: {plans_count}개 동기화 완료"
    )


if __name__ == "__main__":
    main()
