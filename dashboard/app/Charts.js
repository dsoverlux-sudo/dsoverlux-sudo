"use client";

import {
  ResponsiveContainer, LineChart, Line, BarChart, Bar,
  XAxis, YAxis, Tooltip, Legend, CartesianGrid,
} from "recharts";

const GRID = "#2a2e37";
const TICK = { fill: "#9aa0a6", fontSize: 12 };
const TIP = {
  contentStyle: { background: "#1a1d24", border: "1px solid #2a2e37", borderRadius: 8 },
  labelStyle: { color: "#e8eaed" },
};

function Empty() {
  return <p style={{ color: "#9aa0a6", fontSize: 13 }}>데이터가 아직 없습니다 — 수집이 쌓이면 표시됩니다.</p>;
}

export function FollowerChart({ data }) {
  if (!data?.length) return <Empty />;
  return (
    <ResponsiveContainer width="100%" height={260}>
      <LineChart data={data}>
        <CartesianGrid stroke={GRID} strokeDasharray="3 3" />
        <XAxis dataKey="date" tick={TICK} />
        <YAxis tick={TICK} domain={["auto", "auto"]} />
        <Tooltip {...TIP} />
        <Legend />
        <Line type="monotone" dataKey="followers" name="팔로워" stroke="#4f8cff" strokeWidth={2} dot={false} />
        <Line type="monotone" dataKey="follows" name="팔로잉" stroke="#9aa0a6" strokeWidth={1} dot={false} />
      </LineChart>
    </ResponsiveContainer>
  );
}

export function KeywordChart({ data }) {
  if (!data?.length) return <Empty />;
  return (
    <ResponsiveContainer width="100%" height={220}>
      <BarChart data={data}>
        <CartesianGrid stroke={GRID} strokeDasharray="3 3" />
        <XAxis dataKey="date" tick={TICK} />
        <YAxis tick={TICK} allowDecimals={false} />
        <Tooltip {...TIP} />
        <Bar dataKey="matches" name={'"로드맵" 댓글'} fill="#4f8cff" radius={[4, 4, 0, 0]} />
      </BarChart>
    </ResponsiveContainer>
  );
}

export function MediaBarChart({ data }) {
  if (!data?.length) return <Empty />;
  const rows = data.map((d) => ({
    name: (d.caption || d.media_id || "").slice(0, 14) || d.media_id,
    조회: d.views ?? 0,
    도달: d.reach ?? 0,
    저장: d.saved ?? 0,
  }));
  return (
    <ResponsiveContainer width="100%" height={300}>
      <BarChart data={rows}>
        <CartesianGrid stroke={GRID} strokeDasharray="3 3" />
        <XAxis dataKey="name" tick={TICK} interval={0} angle={-20} textAnchor="end" height={60} />
        <YAxis tick={TICK} />
        <Tooltip {...TIP} />
        <Legend />
        <Bar dataKey="조회" fill="#4f8cff" radius={[4, 4, 0, 0]} />
        <Bar dataKey="도달" fill="#7bd88f" radius={[4, 4, 0, 0]} />
        <Bar dataKey="저장" fill="#f2c14e" radius={[4, 4, 0, 0]} />
      </BarChart>
    </ResponsiveContainer>
  );
}

export function DemoChart({ data }) {
  if (!data?.length) return <Empty />;
  const groups = ["age", "gender", "country", "city"];
  return (
    <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(260px, 1fr))", gap: 16 }}>
      {groups.map((g) => {
        const rows = data.filter((d) => d.breakdown === g).slice(0, 8);
        if (!rows.length) return null;
        return (
          <div key={g}>
            <p style={{ color: "#9aa0a6", fontSize: 12, marginBottom: 6 }}>{g}</p>
            <ResponsiveContainer width="100%" height={200}>
              <BarChart data={rows} layout="vertical">
                <XAxis type="number" tick={TICK} hide />
                <YAxis type="category" dataKey="dimension" tick={TICK} width={90} />
                <Tooltip {...TIP} />
                <Bar dataKey="value" name="팔로워" fill="#4f8cff" radius={[0, 4, 4, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        );
      })}
    </div>
  );
}
