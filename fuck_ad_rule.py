#!/usr/bin/env python3
# 功能說明: 從網絡自動爬取兩個廣告規則文件, 去除註釋並合併去重排序後輸出到本地 FuckAD 規則文件

import sys
import urllib.request
import urllib.error
from datetime import datetime, timezone
from typing import List, Set


# 功能說明: 規則來源配置
RULE_URLS = [
    "https://adrules.top/adrules-surge.conf",
    "https://whatshub.top/rule/AntiAD.list",
]

# 功能說明: 合併後輸出的文件名稱
OUTPUT_FILE = "FuckAD.conf"

# 功能說明: HTTP 請求超時秒數
HTTP_TIMEOUT_SECONDS = 60


# 功能說明: 從指定 URL 下載文本內容並按行返回
def fetch_lines_from_url(url: str) -> List[str]:
    if not isinstance(url, str) or not url:
        raise ValueError("URL must be a non-empty string")
    request = urllib.request.Request(
        url=url,
        headers={
            "User-Agent": "Mozilla/5.0 (compatible; FuckAD/1.0; +https://github.com/)"
        },
        method="GET",
    )
    try:
        with urllib.request.urlopen(request, timeout=HTTP_TIMEOUT_SECONDS) as response:
            status = getattr(response, "status", None)
            if status is not None and status != 200:
                raise RuntimeError(f"Unexpected HTTP status {status} for URL: {url}")
            raw_data = response.read()
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"HTTP error when fetching {url}: {e}") from e
    except urllib.error.URLError as e:
        raise RuntimeError(f"Network error when fetching {url}: {e}") from e
    except Exception as e:
        raise RuntimeError(f"Unknown error when fetching {url}: {e}") from e

    if raw_data is None:
        raise RuntimeError(f"Empty response when fetching {url}")

    text = ""
    for encoding in ("utf-8", "utf-8-sig", "latin-1"):
        try:
            text = raw_data.decode(encoding)
            if text:
                break
        except UnicodeDecodeError:
            text = ""
            continue
    if not text:
        raise RuntimeError(f"Failed to decode response from {url} with common encodings")

    lines = text.splitlines()
    return lines


# 功能說明: 判斷一行是否為註釋行或空行
def is_comment_or_empty(line: str) -> bool:
    if line is None:
        return True
    stripped = line.strip()
    if not stripped:
        return True
    if stripped.startswith("#") or stripped.startswith(";") or stripped.startswith("!"):
        return True
    lower = stripped.lower()
    if lower.startswith("[adblock") or lower.startswith("[version") or lower.startswith("[filter"):
        return True
    return False


# 功能說明: 規範化單行規則內容
def normalize_rule_line(line: str) -> str:
    if line is None:
        return ""
    rule = line.strip()
    return rule


# 功能說明: 合併多個規則列表並去除註釋與重複, 然後排序
def merge_and_deduplicate_rules(multi_source_lines: List[List[str]]) -> List[str]:
    if not isinstance(multi_source_lines, list) or not multi_source_lines:
        raise ValueError("Input rule list must be a non-empty list of line lists")

    unique_rules: Set[str] = set()
    rules: List[str] = []

    for source_lines in multi_source_lines:
        if not isinstance(source_lines, list):
            continue
        for raw_line in source_lines:
            if not isinstance(raw_line, str):
                continue
            if is_comment_or_empty(raw_line):
                continue
            rule = normalize_rule_line(raw_line)
            if not rule:
                continue
            if rule in unique_rules:
                continue
            unique_rules.add(rule)
            rules.append(rule)

    rules.sort()
    return rules


# 功能說明: 將規則按格式寫入輸出文件並添加頭部信息
def write_rules_to_file(rules: List[str], output_path: str) -> None:
    if not isinstance(output_path, str) or not output_path:
        raise ValueError("Output path must be a non-empty string")
    if rules is None:
        raise ValueError("Rules list must not be None")

    updated_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    total_rules = len(rules)

    header_lines = [
        f"# Updated time: {updated_at}",
        f"# Total rules: {total_rules}",
        "# Thanks: adrules.top and whatshub.top",
        "",
    ]

    try:
        with open(output_path, "w", encoding="utf-8") as f:
            for line in header_lines:
                f.write(line + "\n")
            for rule in rules:
                f.write(rule + "\n")
    except OSError as e:
        raise RuntimeError(f"Failed to write output file '{output_path}': {e}") from e


# 功能說明: 主函數, 自動爬取並生成 FuckAD 規則文件
def main() -> None:
    all_source_lines: List[List[str]] = []

    for url in RULE_URLS:
        try:
            lines = fetch_lines_from_url(url)
        except Exception as e:
            print(f"Error: failed to fetch rules from {url}: {e}", file=sys.stderr)
            sys.exit(1)
        if not isinstance(lines, list):
            print(f"Error: invalid content fetched from {url}", file=sys.stderr)
            sys.exit(1)
        all_source_lines.append(lines)

    try:
        merged_rules = merge_and_deduplicate_rules(all_source_lines)
    except Exception as e:
        print(f"Error: failed to merge rules: {e}", file=sys.stderr)
        sys.exit(1)

    try:
        write_rules_to_file(merged_rules, OUTPUT_FILE)
    except Exception as e:
        print(f"Error: failed to write output file '{OUTPUT_FILE}': {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
