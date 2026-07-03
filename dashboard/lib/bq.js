import { BigQuery } from "@google-cloud/bigquery";

const PROJECT_ID = process.env.GCP_PROJECT_ID || "iginsights";
const DATASET = "ig_insights";
const LOCATION = "US";

let client;

function getClient() {
  if (client) return client;
  // 배포(Vercel): GCP_SA_KEY = 서비스계정 JSON 통짜 문자열
  // 로컬: GOOGLE_APPLICATION_CREDENTIALS = 키 파일 경로 (라이브러리가 자동 인식)
  if (process.env.GCP_SA_KEY) {
    const creds = JSON.parse(process.env.GCP_SA_KEY);
    client = new BigQuery({ projectId: PROJECT_ID, credentials: creds });
  } else {
    client = new BigQuery({ projectId: PROJECT_ID });
  }
  return client;
}

async function run(sql) {
  const [rows] = await getClient().query({ query: sql, location: LOCATION });
  return rows;
}

const T = (name) => `\`${PROJECT_ID}.${DATASET}.${name}\``;

export async function getFollowerTrend() {
  return run(`
    SELECT CAST(pull_date AS STRING) AS date,
           MAX(followers) AS followers, MAX(follows) AS follows
    FROM ${T("follower_counts")}
    GROUP BY pull_date ORDER BY pull_date`);
}

export async function getTopMedia(limit = 10) {
  return run(`
    SELECT * EXCEPT(rn) FROM (
      SELECT media_id, permalink, caption, media_product_type,
             views, reach, likes, comments, saved, shares,
             ROW_NUMBER() OVER (PARTITION BY media_id ORDER BY pull_date DESC) AS rn
      FROM ${T("reel_metrics")})
    WHERE rn = 1
    ORDER BY COALESCE(views, reach, 0) DESC
    LIMIT ${Number(limit)}`);
}

export async function getAccountSummary() {
  return run(`
    SELECT metric, period, value
    FROM ${T("account_insights")}
    WHERE pull_date = (SELECT MAX(pull_date) FROM ${T("account_insights")})`);
}

export async function getDemographics() {
  return run(`
    SELECT breakdown, dimension, value
    FROM ${T("account_demographics")}
    WHERE pull_date = (SELECT MAX(pull_date) FROM ${T("account_demographics")})
    ORDER BY breakdown, value DESC`);
}

export async function getKeywordTrend() {
  return run(`
    SELECT CAST(pull_date AS STRING) AS date, keyword,
           SUM(match_count) AS matches
    FROM ${T("comment_keywords")}
    GROUP BY pull_date, keyword ORDER BY pull_date`);
}

export async function getKeywordByMedia(limit = 8) {
  return run(`
    SELECT permalink, keyword, match_count, total_comments
    FROM ${T("comment_keywords")}
    WHERE pull_date = (SELECT MAX(pull_date) FROM ${T("comment_keywords")})
      AND match_count > 0
    ORDER BY match_count DESC
    LIMIT ${Number(limit)}`);
}
