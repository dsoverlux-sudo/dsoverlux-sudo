import "./globals.css";

export const metadata = {
  title: "IG 퍼널 대시보드",
  description: "인스타그램 지표 · 퍼널 기여(로드맵 댓글) 대시보드",
};

export default function RootLayout({ children }) {
  return (
    <html lang="ko">
      <body>{children}</body>
    </html>
  );
}
