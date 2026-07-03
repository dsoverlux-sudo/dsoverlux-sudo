import {
  getFollowerTrend,
  getTopMedia,
  getAccountSummary,
  getDemographics,
  getKeywordTrend,
  getKeywordByMedia,
} from "../lib/bq";
import { FollowerChart, MediaBarChart, DemoChart, KeywordChart } from "./Charts";

export const dynamic = "force-dynamic";

function num(v) {
  return v == null ? "–" : Number(v).toLocaleString("ko-KR");
}

export default async function Page() {
  let data, error;
  try {
    const [followers, media, summary, demos, kwTrend, kwMedia] =
      await Promise.all([
        getFollowerTrend(),
        getTopMedia(),
        getAccountSummary(),
        getDemographics(),
        getKeywordTrend(),
        getKeywordByMedia(),
      ]);
    data = { followers, media, summary, demos, kwTrend, kwMedia };
  } catch (e) {
    error = e.message || String(e);
  }

  if (error) {
    return (
      <main>
        <h1>IG 퍼널 대시보드</h1>
        <div className="error">
          BigQuery 연결 오류:{"\n"}{error}{"\n\n"}
          체크: ① GCP_SA_KEY(배포) 또는 GOOGLE_APPLICATION_CREDENTIALS(로컬)
          ② GCP_PROJECT_ID ③ 데이터셋 ig_insights(US)에 수집 데이터 존재 여부
        </div>
      </main>
    );
  }

  const { followers, media, summary, demos, kwTrend, kwMedia } = data;

  const latestFollowers = followers.at(-1);
  const day = Object.fromEntries(
    summary.filter((r) => r.period === "day").map((r) => [r.metric, r.value]));
  const d28 = Object.fromEntries(
    summary.filter((r) => r.period === "days_28").map((r) => [r.metric, r.value]));
  const kwToday = kwTrend.at(-1)?.matches ?? 0;
  const kwTotal = kwTrend.reduce((s, r) => s + Number(r.matches || 0), 0);

  return (
    <main>
      <h1>IG 퍼널 대시보드</h1>
      <p className="sub">
        북극성: L2 월 3건 · 선행 지표 = 댓글 &quot;로드맵&quot; · 매일 자동 수집
      </p>

      <div className="cards">
        <div className="card accent">
          <div className="label">💬 &quot;로드맵&quot; 댓글 (오늘 기준)</div>
          <div className="value">{num(kwToday)}</div>
        </div>
        <div className="card accent">
          <div className="label">💬 &quot;로드맵&quot; 누적</div>
          <div className="value">{num(kwTotal)}</div>
        </div>
        <div className="card">
          <div className="label">팔로워</div>
          <div className="value">{num(latestFollowers?.followers)}</div>
        </div>
        <div className="card">
          <div className="label">도달 (28일)</div>
          <div className="value">{num(d28.reach ?? day.reach)}</div>
        </div>
        <div className="card">
          <div className="label">조회 (28일)</div>
          <div className="value">{num(d28.views ?? day.views)}</div>
        </div>
        <div className="card">
          <div className="label">저장 (28일)</div>
          <div className="value">{num(d28.saves ?? day.saves)}</div>
        </div>
      </div>

      <h2>퍼널 기여 — 게시물별 &quot;로드맵&quot; 댓글</h2>
      <div className="panel">
        {kwMedia.length === 0 ? (
          <p className="sub">아직 키워드 댓글이 없습니다. CTA가 깔리면 여기부터 움직입니다.</p>
        ) : (
          <table className="list">
            <thead>
              <tr><th>게시물</th><th>키워드</th><th>매치</th><th>전체 댓글</th></tr>
            </thead>
            <tbody>
              {kwMedia.map((r, i) => (
                <tr key={i}>
                  <td><a href={r.permalink} target="_blank">{r.permalink?.replace("https://www.instagram.com", "")}</a></td>
                  <td>{r.keyword}</td>
                  <td>{num(r.match_count)}</td>
                  <td>{num(r.total_comments)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      <h2>&quot;로드맵&quot; 댓글 추이</h2>
      <div className="panel"><KeywordChart data={kwTrend} /></div>

      <h2>팔로워 추이</h2>
      <div className="panel"><FollowerChart data={followers} /></div>

      <h2>게시물별 조회·도달 TOP 10</h2>
      <div className="panel"><MediaBarChart data={media} /></div>

      <h2>오디언스 (나이 / 성별 / 지역)</h2>
      <div className="panel"><DemoChart data={demos} /></div>
    </main>
  );
}
