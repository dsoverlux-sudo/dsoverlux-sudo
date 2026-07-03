# -*- coding: utf-8 -*-
"""
L0 리드마그넷 — 「학력 리셋 로드맵」 PDF 생성기 (A4 2쪽)

퍼널 설계서 1주차 산출물. 모든 CTA의 종착지.
팩트 출처: 국가평생교육진흥원 고시 제2025-02호 (제28차 자격 학점인정 기준, 2025.12.15 시행)
컴플라이언스: 표시광고법 리스크 표현("보장", "100%", "무조건") 사용 금지.

실행:  python l0_pdf/make_l0_pdf.py
출력:  l0_pdf/L0_roadmap_v1.pdf
"""

import os

from reportlab.lib.colors import HexColor, white
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "L0_roadmap_v1.pdf")

pdfmetrics.registerFont(TTFont("Malgun", r"C:\Windows\Fonts\malgun.ttf"))
pdfmetrics.registerFont(TTFont("MalgunB", r"C:\Windows\Fonts\malgunbd.ttf"))

W, H = A4  # 595 x 842 pt

NAVY = HexColor("#0f2557")
BLUE = HexColor("#2563eb")
SKY = HexColor("#e8effc")
GRAY = HexColor("#5b6472")
LGRAY = HexColor("#eef0f4")
RED = HexColor("#d93a3a")
GREEN = HexColor("#1e8e5a")
M = 46  # 좌우 여백


def header(c, page_no):
    c.setFillColor(NAVY)
    c.rect(0, H - 110, W, 110, fill=1, stroke=0)
    c.setFillColor(white)
    c.setFont("MalgunB", 26)
    c.drawString(M, H - 62, "학력 리셋 로드맵")
    c.setFont("Malgun", 12.5)
    c.drawString(M, H - 86, "중졸에서 반도체 취업까지 — 전체 경로 한 장 정리")
    c.setFont("Malgun", 9)
    c.drawRightString(W - M, H - 86, f"{page_no} / 2")


def footer(c):
    c.setFillColor(GRAY)
    c.setFont("Malgun", 7.5)
    c.drawString(M, 34, "출처: 국가평생교육진흥원 고시 제2025-02호 (제28차 자격 학점인정 기준, 2025.12.15 시행)")
    c.drawString(M, 23, "본 자료는 제28차 고시 기준이며, 이후 고시 개정 시 내용이 변경될 수 있습니다. 개인의 학습 이력에 따라 적용이 다를 수 있습니다.")


def stage_box(c, y, tag, title, lines, accent=BLUE):
    box_h = 30 + 15 * len(lines)
    # 왼쪽 태그 원
    c.setFillColor(accent)
    c.circle(M + 16, y - box_h / 2, 15, fill=1, stroke=0)
    c.setFillColor(white)
    c.setFont("MalgunB", 9.5)
    c.drawCentredString(M + 16, y - box_h / 2 - 3.5, tag)
    # 본문 박스
    c.setFillColor(SKY)
    c.roundRect(M + 42, y - box_h, W - 2 * M - 42, box_h, 8, fill=1, stroke=0)
    c.setFillColor(NAVY)
    c.setFont("MalgunB", 12.5)
    c.drawString(M + 56, y - 21, title)
    c.setFillColor(GRAY)
    c.setFont("Malgun", 9.5)
    ty = y - 38
    for ln in lines:
        c.drawString(M + 56, ty, ln)
        ty -= 15
    return y - box_h


def arrow(c, y):
    c.setFillColor(BLUE)
    cx = M + 16
    c.line(cx, y, cx, y - 14)
    p = c.beginPath()
    p.moveTo(cx - 4, y - 12)
    p.lineTo(cx + 4, y - 12)
    p.lineTo(cx, y - 20)
    p.close()
    c.setStrokeColor(BLUE)
    c.drawPath(p, fill=1, stroke=0)
    return y - 22


def section_title(c, y, text):
    c.setFillColor(NAVY)
    c.setFont("MalgunB", 14)
    c.drawString(M, y, text)
    c.setStrokeColor(BLUE)
    c.setLineWidth(2)
    c.line(M, y - 7, M + 44, y - 7)
    return y - 28


def page1(c):
    header(c, 1)
    y = H - 140

    c.setFillColor(GRAY)
    c.setFont("Malgun", 10.5)
    c.drawString(M, y, "지금 학력이 어디에 있든, 경로는 네 단계입니다. 각 단계의 함정을 알면 시간과 비용이 줄어듭니다.")
    y -= 32

    y = stage_box(c, y, "S0", "Stage 0 — 검정고시 (고졸 학력 취득)",
                  ["고졸 학력이 모든 것의 출발점입니다. 시험 과목을 이후 직무 학습과 연결되게 준비하면",
                   "같은 공부가 두 번 쓰입니다. (과목별 연결 전략은 채널 영상에서 단계별 해설)"])
    y = arrow(c, y)

    y = stage_box(c, y, "S1", "Stage 1 — 학점은행제 설계 (전문학사·학사)",
                  ["핵심은 순서입니다. 자격증부터 따고 나면 학점이 생각보다 덜 잡히는 구조라서,",
                   "전공·자격증·온라인 학점(K-MOOC·GSEEK 등 무료 강좌 활용)을 먼저 설계하고 시작합니다.",
                   "→ 자격증 학점의 현행 기준과 3가지 규칙은 2쪽에 정리"])
    y = arrow(c, y)

    y = stage_box(c, y, "S2", "Stage 2 — 반도체 현장직 진입",
                  ["FAB(생산라인) 현장 직무로 먼저 진입해 경력을 만듭니다.",
                   "채용 공고가 요구하는 안전·직무 교육 이수증을 미리 갖추면 지원 폭이 넓어집니다."])
    y = arrow(c, y)

    y = stage_box(c, y, "S3", "Stage 3 — 사무·관리직 전환 (Path A / B)",
                  ["Path A: 현장 전문성 심화(설비·PLC 제어 등) → 기술직 성장",
                   "Path B: 학위 + 데이터 역량(설비 로그 분석 등) → 사무·관리직 전환",
                   "둘 중 무엇이 맞는지는 성향과 현장 경험에 따라 갈립니다."], accent=GREEN)

    # 하단 안내
    y -= 26
    c.setFillColor(LGRAY)
    c.roundRect(M, y - 46, W - 2 * M, 46, 8, fill=1, stroke=0)
    c.setFillColor(NAVY)
    c.setFont("MalgunB", 10.5)
    c.drawString(M + 14, y - 19, "이 로드맵을 쓰는 법")
    c.setFillColor(GRAY)
    c.setFont("Malgun", 9.5)
    c.drawString(M + 14, y - 35, "① 내 현재 위치(Stage)를 찾는다 → ② 다음 Stage의 함정(2쪽)을 먼저 확인한다 → ③ 학점 설계 후 자격증을 딴다")

    footer(c)


def page2(c):
    header(c, 2)
    y = H - 145

    # ── 표: 현행 자격증 인정 학점
    y = section_title(c, y, "자격증 학점, 현행 기준 (제28차 고시)")

    rows = [
        ("자격증", "현행 인정 학점", "인터넷에 도는 옛 숫자"),
        ("컴퓨터활용능력 1급", "14학점", "18학점 (X)"),
        ("정보처리기사", "20학점", "30학점 (X)"),
    ]
    col_x = [M, M + 190, M + 330]
    row_h = 24
    for i, (a, b, cc) in enumerate(rows):
        ry = y - i * row_h
        if i == 0:
            c.setFillColor(NAVY)
            c.rect(M - 4, ry - 7, W - 2 * M + 8, row_h - 4, fill=1, stroke=0)
            c.setFillColor(white)
            c.setFont("MalgunB", 10)
        else:
            if i % 2 == 0:
                c.setFillColor(LGRAY)
                c.rect(M - 4, ry - 7, W - 2 * M + 8, row_h - 4, fill=1, stroke=0)
            c.setFillColor(NAVY)
            c.setFont("Malgun", 10)
        c.drawString(col_x[0] + 4, ry, a)
        if i > 0:
            c.setFont("MalgunB", 10)
            c.setFillColor(BLUE)
        c.drawString(col_x[1] + 4, ry, b)
        if i > 0:
            c.setFillColor(RED)
            c.setFont("Malgun", 10)
        c.drawString(col_x[2] + 4, ry, cc)
    y -= len(rows) * row_h + 4

    c.setFillColor(RED)
    c.setFont("MalgunB", 9.5)
    c.drawString(M, y, "※ 18·30학점은 2009년 3월 이전 취득자에게만 적용되는 17년 전 기준입니다.")
    c.setFillColor(GRAY)
    c.setFont("Malgun", 9.5)
    c.drawString(M, y - 14, "고시 표의 괄호 숫자가 최신 기준처럼 퍼진 것 — 옛 숫자로 학위를 설계하면 계획이 통째로 어긋납니다.")
    y -= 44

    # ── 실전 규칙 3가지
    y = section_title(c, y, "학점은행제 자격증 학점 — 실전 규칙 3가지")
    rules = [
        ("1", "개수 한도", "자격증 인정 개수는 학사 최대 3개, 전문학사 최대 2개까지입니다."),
        ("2", "전공 따라 구분 변동", "같은 자격이라도 전공에 따라 전공필수↔일반선택이 바뀝니다. (예: 컴활 1급 — 컴퓨터공학"),
        ("", "", "전공은 전공필수 14학점, 메카트로닉스 전공은 일반선택 14학점)"),
        ("3", "미연계 자격은 1개", "전공과 연계되지 않은 자격은 전체 학위과정에서 1개만 인정됩니다."),
    ]
    for no, head, body in rules:
        if no:
            c.setFillColor(BLUE)
            c.circle(M + 8, y + 3, 8, fill=1, stroke=0)
            c.setFillColor(white)
            c.setFont("MalgunB", 9)
            c.drawCentredString(M + 8, y, no)
            c.setFillColor(NAVY)
            c.setFont("MalgunB", 10)
            c.drawString(M + 24, y, head)
            c.setFillColor(GRAY)
            c.setFont("Malgun", 9.5)
            c.drawString(M + 24 + c.stringWidth(head, "MalgunB", 10) + 8, y, body)
        else:
            c.setFillColor(GRAY)
            c.setFont("Malgun", 9.5)
            c.drawString(M + 24, y, body)
        y -= 19
    y -= 14

    # ── 함정 체크리스트
    y = section_title(c, y, "설계 전 체크 — 흔한 함정 3개")
    traps = [
        "17년 전 숫자(18·30학점)로 학위 계획을 세우고 있지 않은가?",
        "학점 설계 없이 자격증부터 따고 있지 않은가? (한도·구분 규칙에 걸리면 학점이 덜 잡힙니다)",
        "전공 미연계 자격을 여러 개 준비하고 있지 않은가? (1개만 인정)",
    ]
    for t in traps:
        c.setFillColor(RED)
        c.setFont("MalgunB", 10)
        c.drawString(M, y, "□")
        c.setFillColor(GRAY)
        c.setFont("Malgun", 9.5)
        c.drawString(M + 18, y, t)
        y -= 18
    y -= 16

    # ── CTA
    c.setFillColor(NAVY)
    c.roundRect(M, y - 74, W - 2 * M, 74, 10, fill=1, stroke=0)
    c.setFillColor(white)
    c.setFont("MalgunB", 12.5)
    c.drawString(M + 18, y - 26, "다음 단계 — 이 로드맵을 한 칸씩 뜯어봅니다")
    c.setFont("Malgun", 9.5)
    c.drawString(M + 18, y - 44, "각 Stage의 상세 전략(검정고시 과목 연결, 0원 학점 채우기, 자격증 순서, Path A/B 선택 기준)을")
    c.drawString(M + 18, y - 58, "채널 영상으로 순서대로 다룹니다. 궁금한 단계는 영상 댓글에 \"로드맵\"이라고 남겨주세요.")

    footer(c)


def main():
    c = canvas.Canvas(OUT, pagesize=A4)
    c.setTitle("학력 리셋 로드맵 — 중졸에서 반도체 취업까지")
    c.setAuthor("학력 리셋 로드맵")
    page1(c)
    c.showPage()
    page2(c)
    c.save()
    print(f"✅ 생성 완료: {OUT}")


if __name__ == "__main__":
    main()
