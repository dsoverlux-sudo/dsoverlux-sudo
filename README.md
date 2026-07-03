# IG 퍼널 대시보드 (iginsights)

인스타 지표가 매일 BigQuery에 쌓이고, 퍼널 KPI(댓글 "로드맵")까지 그래프로 보는 대시보드.
공장 설계서의 성과 지표("조회수가 아니라 퍼널 기여 → L2 월 3건")를 측정하는 인프라.

## 구조

```
C:\dev\SNS
├── scripts\ig_bq_sync.py   # 매일 IG → BigQuery 수집 (테이블 5개 자동 생성)
├── config.json             # 키워드("로드맵")·데이터셋·API 버전 설정
├── run_ig_sync.bat         # 작업 스케줄러용 실행 파일
├── .secrets\ig_token.txt   # IG 60일 토큰 (직접 붙여넣기 — git 제외됨)
└── dashboard\              # Next.js 대시보드 (Vercel 배포용)
```

수집 테이블: reel_metrics · account_insights · account_demographics ·
follower_counts · **comment_keywords(퍼널 KPI — "로드맵" 댓글 카운트)**

## 사람이 해야 하는 것 (순서대로)

### 1. IG 토큰 (매뉴얼 STEP 1)
- 인스타 프로페셔널 전환 → developers.facebook.com 앱 생성 → Instagram 제품 추가
- **권한 3개** 체크: `instagram_business_basic`, `instagram_business_manage_insights`,
  `instagram_business_manage_comments` ← 댓글 "로드맵" 카운트에 필요 (매뉴얼엔 없던 추가 1개)
- 60일 토큰 발급 → `.secrets\ig_token.txt`에 한 줄로 저장 (공백·따옴표 없이)
- **50일마다 갱신 알림 필수** — 만료되면 수집이 조용히 멈춤

### 2. Google Cloud (매뉴얼 STEP 2)
- 프로젝트 생성(ID 메모) → BigQuery API 켜기 → 데이터셋은 스크립트가 자동 생성(US)
- 서비스계정 `iginsights-sa` + 역할: BigQuery 데이터 편집자 + 작업 사용자
- JSON 키 다운로드 → `C:\keys\iginsights-key.json`으로 이동
- 환경변수: `setx GOOGLE_APPLICATION_CREDENTIALS "C:\keys\iginsights-key.json"`
  그리고 `setx GCP_PROJECT_ID "본인프로젝트ID"` → **새 터미널부터 적용**

### 3. 첫 실행 + 자동화
```powershell
cd C:\dev\SNS
$env:PYTHONUTF8=1
python scripts\ig_bq_sync.py --dry-run   # 토큰만으로 수집 테스트 (BigQuery 불필요)
python scripts\ig_bq_sync.py             # 실제 적재
```
- 작업 스케줄러: 작업 만들기 → 트리거 매일 10:30 → 동작 = `C:\dev\SNS\run_ig_sync.bat`
- 로그: `output\ig_sync.log`

### 4. 대시보드
```powershell
cd C:\dev\SNS\dashboard
npm run dev    # http://localhost:3000
```
- 로컬 인증: 위 환경변수 2개가 이미 있으면 그대로 동작
- Vercel 배포 시 환경변수: `GCP_SA_KEY`(JSON 통짜 문자열) + `GCP_PROJECT_ID`

## 운영 루틴 (2개)
1. **토큰 50일 갱신** (달력 반복 알림) — 대시보드 생사를 가름
2. GCP 예산 알림($1) 메일 확인 — 거의 안 옴

## 공장 연동 (Phase 3 이후)
- publish_state.json(videoId·pillar·persona)을 BigQuery에 적재하면
  "어떤 필러·페르소나가 로드맵 댓글을 만드는가" 조인 분석 가능 → 백로그 우선순위 결정
