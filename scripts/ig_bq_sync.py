# -*- coding: utf-8 -*-
"""
ig_bq_sync.py — 인스타그램 지표 → BigQuery 일일 적재 (퍼널 에디션)

수집 대상 (테이블 5개, 없으면 자동 생성):
  reel_metrics         릴스/게시물별 지표 (views·reach·likes·comments·saved·shares·시청시간)
  account_insights     계정 추이 (day / days_28, 지원 메트릭 자동탐지)
  account_demographics 오디언스 나이/성별/국가/도시
  follower_counts      팔로워/팔로잉/게시물 수
  comment_keywords     퍼널 KPI — 댓글 내 키워드("로드맵") 발생 수

원칙:
  - 멱등성: 같은 pull_date 행을 DELETE 후 load job으로 INSERT (재실행해도 중복 없음)
  - 토큰은 .secrets/ig_token.txt 에서만 읽음 (코드에 비밀값 없음)
  - BigQuery 인증은 GOOGLE_APPLICATION_CREDENTIALS 환경변수
  - 로컬 CSV 백업: output/backup/<날짜>/<테이블>.csv
  - --dry-run: IG에서 읽고 CSV까지만, BigQuery 미접근

사용:
  python scripts/ig_bq_sync.py            # 전체 수집 + 적재
  python scripts/ig_bq_sync.py --dry-run  # BigQuery 없이 수집 테스트
"""

import argparse
import csv
import datetime as dt
import json
import os
import re
import sys
import time

import requests

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG = json.load(open(os.path.join(ROOT, "config.json"), encoding="utf-8"))

API_VER = CONFIG["api_version"]
BASE = f"https://graph.instagram.com/{API_VER}"
DATASET = CONFIG["dataset"]
LOCATION = CONFIG["location"]
PROJECT_ID = os.environ.get(CONFIG["project_id_env"], CONFIG["project_id_default"])
KEYWORDS = CONFIG["funnel_keywords"]
TOKEN_PATH = os.path.join(ROOT, ".secrets", "ig_token.txt")
BACKUP_DIR = os.path.join(ROOT, "output", "backup")

PULL_DATE = dt.date.today().isoformat()

# ---------------------------------------------------------------- 스키마

SCHEMAS = {
    "reel_metrics": [
        ("pull_date", "DATE"), ("media_id", "STRING"), ("media_type", "STRING"),
        ("media_product_type", "STRING"), ("permalink", "STRING"), ("caption", "STRING"),
        ("posted_at", "TIMESTAMP"), ("views", "INT64"), ("reach", "INT64"),
        ("likes", "INT64"), ("comments", "INT64"), ("saved", "INT64"),
        ("shares", "INT64"), ("total_interactions", "INT64"),
        ("avg_watch_time_sec", "FLOAT64"), ("total_watch_time_sec", "FLOAT64"),
    ],
    "account_insights": [
        ("pull_date", "DATE"), ("metric", "STRING"), ("period", "STRING"),
        ("end_time", "TIMESTAMP"), ("value", "INT64"),
    ],
    "account_demographics": [
        ("pull_date", "DATE"), ("breakdown", "STRING"),
        ("dimension", "STRING"), ("value", "INT64"),
    ],
    "follower_counts": [
        ("pull_date", "DATE"), ("username", "STRING"), ("followers", "INT64"),
        ("follows", "INT64"), ("media_count", "INT64"),
    ],
    "comment_keywords": [
        ("pull_date", "DATE"), ("media_id", "STRING"), ("permalink", "STRING"),
        ("keyword", "STRING"), ("match_count", "INT64"), ("total_comments", "INT64"),
    ],
}

# ---------------------------------------------------------------- IG API

def load_token():
    if not os.path.exists(TOKEN_PATH):
        sys.exit(f"❌ 토큰 파일이 없습니다: {TOKEN_PATH}\n"
                 f"   STEP 1의 60일 토큰을 한 줄로 저장하세요 (공백·따옴표·줄바꿈 없이).")
    token = open(TOKEN_PATH, encoding="utf-8").read().strip().strip('"').strip("'")
    if len(token) < 50:
        sys.exit("❌ 토큰이 너무 짧습니다. ig_token.txt 내용을 확인하세요.")
    return token


TOKEN = None


def api_get(path, params=None, ok_to_fail=False):
    """GET 1회. 실패 시 (None, error_message) 반환 가능."""
    p = dict(params or {})
    p["access_token"] = TOKEN
    url = path if path.startswith("http") else f"{BASE}/{path}"
    try:
        r = requests.get(url, params=p, timeout=30)
        data = r.json()
    except Exception as e:
        if ok_to_fail:
            return None, str(e)
        sys.exit(f"❌ API 요청 실패: {url} — {e}")
    if "error" in data:
        msg = data["error"].get("message", str(data["error"]))
        if ok_to_fail:
            return None, msg
        sys.exit(f"❌ API 오류: {msg}\n   (토큰 만료면 STEP 1 갱신 URL로 재발급)")
    return data, None


def api_paginate(path, params, max_items):
    """paging.next 따라가며 data 항목 수집 (상한 max_items로 무한루프 차단)."""
    items, url, p = [], path, dict(params)
    for _ in range(50):  # 페이지 수 안전 상한
        data, err = api_get(url, p, ok_to_fail=True)
        if err or not data:
            break
        items.extend(data.get("data", []))
        if len(items) >= max_items:
            return items[:max_items]
        nxt = data.get("paging", {}).get("next")
        if not nxt:
            break
        url, p = nxt, {}  # next URL에 토큰 포함돼 있음
    return items


def get_me():
    data, _ = api_get("me", {"fields": "id,username,followers_count,follows_count,media_count"})
    return data


def get_media():
    fields = "id,caption,media_type,media_product_type,permalink,timestamp,like_count,comments_count"
    return api_paginate("me/media", {"fields": fields, "limit": 50},
                        CONFIG["media_page_limit"])


MEDIA_METRICS = {
    "REELS": ["views", "reach", "likes", "comments", "saved", "shares",
              "total_interactions", "ig_reels_avg_watch_time",
              "ig_reels_video_view_total_time"],
    "DEFAULT": ["views", "reach", "likes", "comments", "saved", "shares",
                "total_interactions"],
}


def drop_bad_metric(metrics, err_msg):
    """오류 메시지에 언급된 미지원 메트릭 제거. 못 찾으면 마지막 것 제거(진행 보장)."""
    for m in list(metrics):
        if re.search(rf"\b{re.escape(m)}\b", err_msg):
            metrics.remove(m)
            return metrics
    metrics.pop()
    return metrics


def get_media_insights(media):
    kind = "REELS" if media.get("media_product_type") == "REELS" else "DEFAULT"
    metrics = list(MEDIA_METRICS[kind])
    values = {}
    for _ in range(len(metrics)):  # 유한 반복 — 매 실패마다 메트릭 1개 제거
        if not metrics:
            break
        data, err = api_get(f"{media['id']}/insights",
                            {"metric": ",".join(metrics)}, ok_to_fail=True)
        if not err:
            for item in (data or {}).get("data", []):
                vals = item.get("values", [])
                if vals:
                    values[item["name"]] = vals[0].get("value")
            break
        metrics = drop_bad_metric(metrics, err)
    return values


def build_reel_rows(media_list):
    rows = []
    for m in media_list:
        ins = get_media_insights(m)
        avg_ms = ins.get("ig_reels_avg_watch_time")
        tot_ms = ins.get("ig_reels_video_view_total_time")
        rows.append({
            "pull_date": PULL_DATE,
            "media_id": m["id"],
            "media_type": m.get("media_type"),
            "media_product_type": m.get("media_product_type"),
            "permalink": m.get("permalink"),
            "caption": (m.get("caption") or "")[:300],
            "posted_at": m.get("timestamp"),
            "views": ins.get("views"),
            "reach": ins.get("reach"),
            "likes": ins.get("likes", m.get("like_count")),
            "comments": ins.get("comments", m.get("comments_count")),
            "saved": ins.get("saved"),
            "shares": ins.get("shares"),
            "total_interactions": ins.get("total_interactions"),
            "avg_watch_time_sec": round(avg_ms / 1000.0, 2) if avg_ms else None,
            "total_watch_time_sec": round(tot_ms / 1000.0, 2) if tot_ms else None,
        })
        time.sleep(0.2)  # 레이트리밋 완충
    return rows


ACCOUNT_METRIC_CANDIDATES = ["reach", "views", "accounts_engaged",
                             "total_interactions", "likes", "comments",
                             "saves", "shares", "replies", "follows_and_unfollows"]


def get_account_insights():
    """period=day/days_28 × 지원 메트릭 자동탐지 (실패 메트릭은 제거하며 유한 재시도)."""
    rows = []
    for period in ("day", "days_28"):
        metrics = list(ACCOUNT_METRIC_CANDIDATES)
        for _ in range(len(metrics)):
            if not metrics:
                break
            data, err = api_get("me/insights", {
                "metric": ",".join(metrics), "period": period,
                "metric_type": "total_value",
            }, ok_to_fail=True)
            if not err:
                for item in (data or {}).get("data", []):
                    tv = item.get("total_value", {})
                    rows.append({
                        "pull_date": PULL_DATE, "metric": item["name"],
                        "period": period, "end_time": None,
                        "value": tv.get("value"),
                    })
                break
            metrics = drop_bad_metric(metrics, err)
    return rows


def get_demographics():
    rows = []
    for breakdown in ("age", "gender", "country", "city"):
        data, err = api_get("me/insights", {
            "metric": "follower_demographics", "period": "lifetime",
            "timeframe": "this_month", "metric_type": "total_value",
            "breakdown": breakdown,
        }, ok_to_fail=True)
        if err:
            print(f"  ⚠ demographics/{breakdown} 스킵: {err}")
            continue
        for item in (data or {}).get("data", []):
            for bd in item.get("total_value", {}).get("breakdowns", []):
                for res in bd.get("results", []):
                    dim = "/".join(res.get("dimension_values", []))
                    rows.append({"pull_date": PULL_DATE, "breakdown": breakdown,
                                 "dimension": dim, "value": res.get("value")})
    return rows


def get_comment_keywords(media_list):
    """최근 N개 게시물의 댓글에서 퍼널 키워드 발생 수 집계.
    권한(instagram_business_manage_comments) 없으면 경고 후 빈 목록."""
    rows = []
    recent = media_list[:CONFIG["comments_recent_media"]]
    warned = False
    for m in recent:
        comments = api_paginate(f"{m['id']}/comments",
                                {"fields": "text", "limit": 50}, 300)
        if not comments and not warned:
            pass  # 댓글 0개일 수도 있으므로 개별 경고는 생략
        texts = [(c.get("text") or "") for c in comments]
        for kw in KEYWORDS:
            rows.append({
                "pull_date": PULL_DATE, "media_id": m["id"],
                "permalink": m.get("permalink"), "keyword": kw,
                "match_count": sum(1 for t in texts if kw in t),
                "total_comments": len(texts),
            })
        time.sleep(0.2)
    return rows


# ---------------------------------------------------------------- 적재

def backup_csv(table, rows):
    d = os.path.join(BACKUP_DIR, PULL_DATE)
    os.makedirs(d, exist_ok=True)
    path = os.path.join(d, f"{table}.csv")
    cols = [c for c, _ in SCHEMAS[table]]
    with open(path, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        w.writerows(rows)
    return path


def load_to_bq(client, table, rows):
    from google.cloud import bigquery

    dataset_ref = f"{PROJECT_ID}.{DATASET}"
    try:
        client.get_dataset(dataset_ref)
    except Exception:
        ds = bigquery.Dataset(dataset_ref)
        ds.location = LOCATION
        client.create_dataset(ds)
        print(f"  📦 데이터셋 생성: {dataset_ref} ({LOCATION})")

    table_id = f"{dataset_ref}.{table}"
    schema = [bigquery.SchemaField(n, t) for n, t in SCHEMAS[table]]
    try:
        client.get_table(table_id)
    except Exception:
        client.create_table(bigquery.Table(table_id, schema=schema))
        print(f"  📋 테이블 생성: {table}")

    # 멱등성: 오늘 날짜 행 삭제 후 load job으로 삽입
    client.query(
        f"DELETE FROM `{table_id}` WHERE pull_date = @d",
        job_config=bigquery.QueryJobConfig(query_parameters=[
            bigquery.ScalarQueryParameter("d", "DATE", PULL_DATE)]),
        location=LOCATION,
    ).result()

    if rows:
        job = client.load_table_from_json(
            rows, table_id,
            job_config=bigquery.LoadJobConfig(schema=schema),
            location=LOCATION)
        job.result()
    print(f"  ✅ {table}: {len(rows)}행")


def main():
    global TOKEN
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true",
                    help="BigQuery 없이 IG 수집 + CSV 백업만")
    args = ap.parse_args()

    TOKEN = load_token()

    print(f"── IG → BigQuery 수집 시작 ({PULL_DATE}) ──")
    me = get_me()
    print(f"  계정: @{me.get('username')} · 팔로워 {me.get('followers_count')}")

    media = get_media()
    print(f"  게시물 {len(media)}개 발견 — 지표 수집 중…")

    tables = {
        "follower_counts": [{
            "pull_date": PULL_DATE, "username": me.get("username"),
            "followers": me.get("followers_count"),
            "follows": me.get("follows_count"),
            "media_count": me.get("media_count"),
        }],
        "reel_metrics": build_reel_rows(media),
        "account_insights": get_account_insights(),
        "account_demographics": get_demographics(),
        "comment_keywords": get_comment_keywords(media),
    }

    for t, rows in tables.items():
        p = backup_csv(t, rows)
        print(f"  💾 CSV 백업: {p} ({len(rows)}행)")

    if args.dry_run:
        print("── dry-run 완료 (BigQuery 미접근) ──")
        return

    if not os.environ.get("GOOGLE_APPLICATION_CREDENTIALS"):
        sys.exit("❌ GOOGLE_APPLICATION_CREDENTIALS 환경변수가 없습니다.\n"
                 "   setx 등록 후 '새' 터미널에서 다시 실행하세요 (STEP 2-5).")

    from google.cloud import bigquery
    client = bigquery.Client(project=PROJECT_ID)
    for t, rows in tables.items():
        load_to_bq(client, t, rows)

    kw_total = sum(r["match_count"] for r in tables["comment_keywords"])
    print(f"── 완료. 오늘 '로드맵' 댓글 매치: {kw_total}건 ──")


if __name__ == "__main__":
    main()
