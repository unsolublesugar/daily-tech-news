"""AI要約。記事本文を取得し、Gemini で「主題＋3行要約＋キーワード」を生成する。

tsuyu-mi (https://github.com/unsolublesugar/tsuyu-mi) の要約パイプラインを
本リポジトリ向けに簡略化して移植したもの。

- 本文取得: requests + trafilatura。失敗時はタイトル＋RSS抜粋からの簡易要約に切り替える
- LLM: google-genai SDK（JSONモード）。`LLM_API_KEY` 未設定なら何もしない
- 永続化: `data/summaries.json` にURLキーで保存し、再登場した記事は再要約しない

環境変数:
    LLM_API_KEY              Gemini APIキー（未設定なら要約機能は無効）
    LLM_MODEL                モデル名（既定: gemini-3.5-flash-lite）
    MAX_SUMMARIZE_PER_RUN    1回の実行で新規に要約する上限件数（既定: 60）
    REQUEST_TIMEOUT_SECONDS  本文取得のタイムアウト秒（既定: 15）
"""

import html as html_module
import json
import os
import re
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

import requests

DEFAULT_MODEL = "gemini-3.5-flash-lite"
PROJECT_ROOT = Path(__file__).resolve().parent.parent
PROMPTS_DIR = PROJECT_ROOT / "prompts"
CACHE_PATH = PROJECT_ROOT / "data" / "summaries.json"

# キャッシュの保持日数。はてブ人気/新着のように日をまたいで再登場する記事を再要約しないための期間
CACHE_RETENTION_DAYS = 30

# 本文の最大文字数（トークン量の上限。長文記事は冒頭で打ち切る）
MAX_BODY_CHARS = 12000
# これ未満しか抽出できない場合は本文取得失敗とみなし簡易要約に切り替える
MIN_BODY_CHARS = 100

USER_AGENT = "daily-tech-news/1.0 (+https://github.com/unsolublesugar/daily-tech-news)"

# LLM呼び出しの再試行（レート制限・一時的エラー向け）。待機秒は試行ごとに使う
LLM_RETRY_WAITS = (5, 15, 30)


def _log(message: str) -> None:
    print(f"[ai_summary] {message}")


# ---------------------------------------------------------------
# 設定
# ---------------------------------------------------------------


class SummaryConfig:
    """環境変数から要約機能の設定を読み込む"""

    def __init__(self) -> None:
        self.api_key = os.environ.get("LLM_API_KEY", "").strip()
        self.model = os.environ.get("LLM_MODEL", "").strip() or DEFAULT_MODEL
        self.max_per_run = _env_int("MAX_SUMMARIZE_PER_RUN", 60)
        self.request_timeout = _env_int("REQUEST_TIMEOUT_SECONDS", 15)

    @property
    def enabled(self) -> bool:
        return bool(self.api_key)


def _env_int(name: str, default: int) -> int:
    try:
        return int(os.environ.get(name, "") or default)
    except ValueError:
        return default


# ---------------------------------------------------------------
# キャッシュ（data/summaries.json）
# ---------------------------------------------------------------


class SummaryCache:
    """URLをキーにした要約キャッシュ。リポジトリにコミットして永続化する"""

    def __init__(self, path: Path = CACHE_PATH) -> None:
        self.path = path
        self.items: Dict[str, Dict[str, Any]] = {}
        self.dirty = False
        self._load()

    def _load(self) -> None:
        if not self.path.exists():
            return
        try:
            with open(self.path, "r", encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, dict):
                self.items = data
        except (OSError, json.JSONDecodeError) as e:
            _log(f"キャッシュの読み込みに失敗したため空から開始します: {e}")
            self.items = {}

    def get(self, url: str) -> Optional[Dict[str, Any]]:
        return self.items.get(url)

    def set(self, url: str, summary: Dict[str, Any]) -> None:
        self.items[url] = summary
        self.dirty = True

    def prune(self, now: datetime, retention_days: int = CACHE_RETENTION_DAYS) -> int:
        """保持期間を過ぎたエントリーを削除し、削除件数を返す"""
        threshold = now - timedelta(days=retention_days)
        removed = 0
        for url in list(self.items.keys()):
            generated_at = _parse_datetime(self.items[url].get("generated_at"))
            if generated_at is None or generated_at < threshold:
                del self.items[url]
                removed += 1
        if removed:
            self.dirty = True
        return removed

    def save(self) -> None:
        if not self.dirty:
            return
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump(self.items, f, ensure_ascii=False, indent=2, sort_keys=True)
            f.write("\n")
        self.dirty = False
        _log(f"キャッシュを保存しました: {self.path} ({len(self.items)}件)")


def _parse_datetime(value: Any) -> Optional[datetime]:
    if not isinstance(value, str) or not value:
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed


# ---------------------------------------------------------------
# 本文取得
# ---------------------------------------------------------------


def fetch_article_text(url: str, timeout: int = 15, session: Optional[requests.Session] = None) -> str:
    """URLから記事本文のテキストを取得する。取得・抽出できなければ空文字"""
    try:
        import trafilatura
    except ImportError:
        _log("trafilatura がインストールされていないため本文取得をスキップします")
        return ""

    http = session or requests
    try:
        response = http.get(url, timeout=timeout, headers={"User-Agent": USER_AGENT}, allow_redirects=True)
        response.raise_for_status()
    except requests.RequestException as e:
        _log(f"本文取得失敗 {url}: {e}")
        return ""

    content_type = response.headers.get("content-type", "")
    if "html" not in content_type.lower():
        return ""

    try:
        text = trafilatura.extract(response.text, include_comments=False, include_tables=True) or ""
    except Exception as e:  # trafilatura は内部で多様な例外を投げうる
        _log(f"本文抽出失敗 {url}: {e}")
        return ""

    text = re.sub(r"[ \t　]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text).strip()
    if len(text) < MIN_BODY_CHARS:
        return ""
    return text[:MAX_BODY_CHARS]


def fetch_article_texts(urls: List[str], timeout: int = 15, max_workers: int = 5) -> Dict[str, str]:
    """複数URLの本文を並列取得する"""
    results: Dict[str, str] = {}
    if not urls:
        return results

    session = requests.Session()
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        for url, text in zip(urls, executor.map(lambda u: fetch_article_text(u, timeout, session), urls)):
            results[url] = text
    return results


# ---------------------------------------------------------------
# LLM プロバイダー
# ---------------------------------------------------------------


class GeminiProvider:
    """Google Gemini API（google-genai SDK）でJSON応答を生成する"""

    def __init__(self, api_key: str, model: str) -> None:
        from google import genai

        self.client = genai.Client(api_key=api_key)
        self.model = model

    def generate(self, prompt: str) -> str:
        response = self.client.models.generate_content(
            model=self.model,
            contents=prompt,
            # JSONモードを明示し、コードブロックや前置きが混ざるのを防ぐ
            config={"response_mime_type": "application/json"},
        )
        return response.text or ""


# ---------------------------------------------------------------
# プロンプトと応答パース
# ---------------------------------------------------------------


def _load_prompt(name: str) -> str:
    return (PROMPTS_DIR / name).read_text(encoding="utf-8")


def build_fulltext_prompt(title: str, url: str, feed_name: str, text: str) -> str:
    return _load_prompt("summarize_full.txt").format(title=title, url=url, feed=feed_name, text=text)


def build_fallback_prompt(title: str, url: str, feed_name: str, excerpt: str) -> str:
    metadata = {"title": title, "url": url, "feed": feed_name, "rss_excerpt": excerpt}
    metadata_str = json.dumps(metadata, ensure_ascii=False, indent=2)
    return _load_prompt("summarize_fallback.txt").format(metadata=metadata_str)


def parse_summary_response(raw: str) -> Dict[str, Any]:
    """LLM応答のJSONを検証し、正規化した辞書を返す。不正なら ValueError"""
    text = raw.strip()
    if "```" in text:
        match = re.search(r"```(?:json)?\s*(.*?)```", text, re.DOTALL)
        if match:
            text = match.group(1).strip()

    data = json.loads(text)
    if not isinstance(data, dict):
        raise ValueError("JSONオブジェクトではありません")

    topic = str(data.get("topic", "")).strip()
    lines = [str(line).strip() for line in data.get("summary_3lines", []) if str(line).strip()]
    keywords = [str(k).strip() for k in data.get("keywords", []) if str(k).strip()]

    if not topic or not lines:
        raise ValueError("topic / summary_3lines が空です")

    return {"topic": topic, "summary_lines": lines[:3], "keywords": keywords[:5]}


def _call_llm(provider: Any, prompt: str) -> Optional[Dict[str, Any]]:
    """LLMを呼び出してパースする。失敗時は待機付きで再試行し、それでも駄目なら None"""
    last_error: Optional[Exception] = None
    for attempt, wait in enumerate(LLM_RETRY_WAITS + (None,)):
        try:
            return parse_summary_response(provider.generate(prompt))
        except Exception as e:
            last_error = e
            if wait is None:
                break
            _log(f"LLM呼び出し/パース失敗（{attempt + 1}回目）、{wait}秒後に再試行します: {e}")
            time.sleep(wait)
    _log(f"LLM呼び出しを断念しました: {last_error}")
    return None


# ---------------------------------------------------------------
# エントリーへの付与
# ---------------------------------------------------------------


def _entry_excerpt(entry: Any) -> str:
    """RSS本文の抜粋（タグ除去済み）。簡易要約プロンプトの材料"""
    raw = ""
    for attr in ("summary", "description"):
        value = getattr(entry, attr, None)
        if value:
            raw = value
            break
    if not raw:
        content = getattr(entry, "content", None)
        if isinstance(content, list) and content:
            raw = content[0].get("value", "")
    text = re.sub(r"<[^>]+>", " ", str(raw))
    text = html_module.unescape(text)
    return re.sub(r"\s+", " ", text).strip()[:1000]


def attach_ai_summaries(
    all_entries: Dict[str, List[Any]],
    is_article_feed: Callable[[str], bool],
    config: Optional[SummaryConfig] = None,
    provider: Any = None,
    cache: Optional[SummaryCache] = None,
    now: Optional[datetime] = None,
) -> Dict[str, int]:
    """記事フィードの各エントリーに `ai_summary` 属性を付与する

    戻り値は統計（cached / generated / failed / skipped）。
    要約機能が無効（APIキー未設定）なら何もせず空の統計を返す。
    `provider` を差し替えるとテストでLLM呼び出しをモックできる。
    """
    config = config or SummaryConfig()
    stats = {"cached": 0, "generated": 0, "failed": 0, "skipped": 0}

    if provider is None:
        if not config.enabled:
            _log("LLM_API_KEY が未設定のためAI要約をスキップします")
            return stats
        try:
            provider = GeminiProvider(config.api_key, config.model)
        except Exception as e:
            _log(f"LLMクライアントの初期化に失敗したためAI要約をスキップします: {e}")
            return stats

    now = now or datetime.now(timezone.utc)
    cache = cache or SummaryCache()
    cache.prune(now)

    # 1. キャッシュ済みは即付与、未要約のものを集める
    pending: List[tuple] = []  # (entry, feed_name)
    seen_urls = set()
    for feed_name, entries in all_entries.items():
        if not is_article_feed(feed_name):
            continue
        for entry in entries:
            url = getattr(entry, "link", "") or ""
            if not url or url in seen_urls:
                continue
            seen_urls.add(url)
            cached = cache.get(url)
            if cached:
                entry.ai_summary = cached
                stats["cached"] += 1
            else:
                pending.append((entry, feed_name))

    if len(pending) > config.max_per_run:
        stats["skipped"] = len(pending) - config.max_per_run
        _log(f"要約上限 {config.max_per_run} 件を超えたため {stats['skipped']} 件は今回スキップします")
        pending = pending[: config.max_per_run]

    if not pending:
        _log(f"新規に要約する記事はありません（キャッシュ利用: {stats['cached']}件）")
        cache.save()
        return stats

    # 2. 本文を並列取得
    _log(f"{len(pending)} 件の本文を取得します...")
    texts = fetch_article_texts([entry.link for entry, _ in pending], timeout=config.request_timeout)

    # 3. LLMで要約（レート制限を考慮して直列）
    for entry, feed_name in pending:
        title = html_module.unescape(re.sub(r"<[^>]+>", "", getattr(entry, "title", "") or "")).strip()
        body = texts.get(entry.link, "")
        if body:
            prompt = build_fulltext_prompt(title, entry.link, feed_name, body)
            input_type = "fulltext"
        else:
            prompt = build_fallback_prompt(title, entry.link, feed_name, _entry_excerpt(entry))
            input_type = "metadata"

        result = _call_llm(provider, prompt)
        if result is None:
            stats["failed"] += 1
            continue

        result.update({
            "input_type": input_type,
            "model": config.model,
            "generated_at": now.isoformat().replace("+00:00", "Z"),
        })
        entry.ai_summary = result
        cache.set(entry.link, result)
        stats["generated"] += 1

    cache.save()
    _log(
        f"AI要約 完了: 生成 {stats['generated']} / キャッシュ {stats['cached']} / "
        f"失敗 {stats['failed']} / スキップ {stats['skipped']}"
    )
    return stats
