#!/usr/bin/env python3
"""로드맵 status.md 자동 섹션 렌더러.

입력:
- docs/generated/commercial-status.md  — 47 모듈 x 23 기준 판정 결과
- docs/generated/wave-status.md        — Wave 진입/완료 현황

출력:
- docs/product/roadmap/status.md 의 <!-- status-auto:* --> 블록을 멱등 치환
- 추가로 README.md / overview.md / milestones.md / matrix.md / engineering/README.md
  / phase-timeline.md / waves/wave-*.md / gates/README.md 에 존재하는
  <!-- status-auto-embed:KEY --> 블록도 동일 규칙으로 치환

설계:
- 수동 섹션(<!-- status-manual:* -->)은 절대 건드리지 않는다
- 섹션 주석 사이의 내용만 교체하고, 주석 자체는 보존한다
- frontmatter 의 generated_at 을 ISO8601 UTC 로 갱신한다 (status.md 한정)
- 닫는 주석이 누락된 파일은 repair 로직으로 자동 복구 (다음 블록 또는 ## 헤더 앞에서 닫음)
- --check 플래그: diff 만 보고 파일은 기록하지 않음. generated_at 갱신도 스킵.

사용:
    python3 scripts/roadmap/status_render.py
    python3 scripts/roadmap/status_render.py --check
"""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
ROADMAP_DIR = REPO / "docs" / "product" / "roadmap"
COMMERCIAL_STATUS = REPO / "docs" / "generated" / "commercial-status.md"
WAVE_STATUS = REPO / "docs" / "generated" / "wave-status.md"

TOTAL_MODULES = 47
TOTAL_GATES = 23
TOTAL_JUDGMENTS = TOTAL_MODULES * TOTAL_GATES  # 1,081


@dataclass
class ModuleRow:
    module: str
    label: str
    passed: int
    failed: int
    implemented: int


@dataclass
class WaveRow:
    wave: int
    total: int
    pre_commercial_plus: int
    commercial_ready: int
    entered: bool
    completed: bool


@dataclass
class RenderContext:
    modules: list[ModuleRow]
    waves: list[WaveRow]
    active_wave: int | None
    active_phase: str = "1 — 이벤트 체인 안정화"
    label_distribution: dict[str, int] = field(default_factory=dict)
    # Phase → Wave → (passed, expected). commercial-status.md 의 새 섹션에서 파싱.
    phase_wave_matrix: dict[int, dict[int, tuple[int, int]]] = field(default_factory=dict)

    def total_passed(self) -> int:
        return sum(m.passed for m in self.modules)

    def overall_progress(self) -> tuple[int, int]:
        return self.total_passed(), TOTAL_JUDGMENTS

    def modules_in_wave(self, wave: int, wave_modules: dict[int, list[str]]) -> list[ModuleRow]:
        names = set(wave_modules.get(wave, []))
        return [m for m in self.modules if m.module in names]


# ---------------------------------------------------------------------------
# 입력 파싱
# ---------------------------------------------------------------------------


def parse_commercial_status(
    path: Path,
) -> tuple[list[ModuleRow], dict[str, int], dict[int, dict[int, tuple[int, int]]]]:
    """commercial-status.md 3 섹션 동시 파싱: 라벨 분포 + 모듈 행 + Phase x Wave 매트릭스."""
    if not path.exists():
        return [], {}, {}
    text = path.read_text(encoding="utf-8")

    label_dist: dict[str, int] = {}
    for m in re.finditer(
        r"\|\s*(alpha|beta|pre-commercial|commercial-ready)\s*\|\s*(\d+)\s*\|", text
    ):
        label_dist[m.group(1)] = int(m.group(2))

    row_re = re.compile(
        r"\|\s*([\w-]+)\s*\|\s*\*\*(alpha|beta|pre-commercial|commercial-ready)\*\*\s*"
        r"\|\s*(\d+)\s*\|\s*(\d+)\s*\|\s*(\d+)\s*\|\s*/23\s*\|",
    )
    rows: list[ModuleRow] = [
        ModuleRow(
            module=m.group(1),
            label=m.group(2),
            passed=int(m.group(3)),
            failed=int(m.group(4)),
            implemented=int(m.group(5)),
        )
        for m in row_re.finditer(text)
    ]

    # Phase x Wave 매트릭스: | P{n} | {gates} | {p1}/{e1} | ... | {p4}/{e4} | {sum} |
    pw_matrix: dict[int, dict[int, tuple[int, int]]] = {}
    pw_row_re = re.compile(
        r"\|\s*P(\d+)\s*\|\s*\d+\s*"
        r"\|\s*(\d+)/(\d+)\s*"
        r"\|\s*(\d+)/(\d+)\s*"
        r"\|\s*(\d+)/(\d+)\s*"
        r"\|\s*(\d+)/(\d+)\s*\|",
    )
    for m in pw_row_re.finditer(text):
        phase = int(m.group(1))
        pw_matrix[phase] = {
            1: (int(m.group(2)), int(m.group(3))),
            2: (int(m.group(4)), int(m.group(5))),
            3: (int(m.group(6)), int(m.group(7))),
            4: (int(m.group(8)), int(m.group(9))),
        }
    return rows, label_dist, pw_matrix


def parse_wave_status(path: Path) -> tuple[list[WaveRow], int | None]:
    if not path.exists():
        return [], None
    text = path.read_text(encoding="utf-8")

    active_match = re.search(r"\*\*활성\s*웨이브\s*:\s*Wave\s*(\d+)\*\*", text)
    active_wave = int(active_match.group(1)) if active_match else None

    row_re = re.compile(
        r"\|\s*Wave\s*(\d+)\s*\|\s*(\d+)\s*\|\s*(\d+)/\d+\s*\|\s*(\d+)/\d+\s*"
        r"\|\s*([✅⏳❌])\s*\|\s*([✅⏳❌])\s*\|",
    )
    rows: list[WaveRow] = [
        WaveRow(
            wave=int(m.group(1)),
            total=int(m.group(2)),
            pre_commercial_plus=int(m.group(3)),
            commercial_ready=int(m.group(4)),
            entered=m.group(5) == "✅",
            completed=m.group(6) == "✅",
        )
        for m in row_re.finditer(text)
    ]
    return rows, active_wave


# ---------------------------------------------------------------------------
# Wave 모듈 매핑 (scripts/audit/wave_entry_check.py WAVES 와 동일)
# ---------------------------------------------------------------------------

WAVE_MODULES: dict[int, list[str]] = {
    1: [
        "gateway",
        "directory",
        "accounting",
        "hr",
        "payroll",
        "selling",
        "buying",
        "stock",
        "expenses",
        "projects",
        "crm",
        "portal",
    ],
    2: [
        "manufacturing",
        "quality",
        "assets",
        "maintenance",
        "ecommerce",
        "pos",
        "subscriptions",
        "integration-hub",
        "documents",
        "compliance",
        "ehs",
        "plm",
        "survey",
    ],
    3: [
        "calendar",
        "board",
        "mail",
        "messenger",
        "wiki",
        "knowledge",
        "analytics",
        "rental",
        "fleet",
        "tms",
        "marketing",
        "marketing-automation",
        "gtm",
        "clm",
    ],
    4: [
        "advanced-planning",
        "consolidation",
        "esg",
        "iot",
        "rpa",
        "lms",
        "workreport",
        "reservation",
    ],
}


# ---------------------------------------------------------------------------
# 렌더 섹션
# ---------------------------------------------------------------------------


def render_section(key: str, ctx: RenderContext) -> str:
    if key == "active":
        phase = ctx.active_phase
        wave = f"Wave {ctx.active_wave}" if ctx.active_wave else "(미지정)"
        return f"- 활성 작업 흐름: **{phase}**\n- 활성 모듈 집단: **{wave}**"
    if key == "gate-distribution":
        if not ctx.label_distribution:
            return "_입력 파일 없음._"
        lines = ["| 라벨 | 모듈 수 |", "|------|---------|"]
        lines.extend(
            f"| {label} | {ctx.label_distribution.get(label, 0)} |"
            for label in ("alpha", "beta", "pre-commercial", "commercial-ready")
        )
        return "\n".join(lines)
    if key == "wave-entry":
        if not ctx.waves:
            return "_입력 파일 없음._"
        lines = [
            "| 집단 | 총 | pre-commercial+ | commercial-ready | 진입 | 완료 |",
            "|------|-----|-----------------|-------------------|------|------|",
        ]
        for w in ctx.waves:
            enter = "✅" if w.entered else "⏳"
            done = "✅" if w.completed else "❌"
            lines.append(
                f"| Wave {w.wave} | {w.total} | {w.pre_commercial_plus}/{w.total} | {w.commercial_ready}/{w.total} | {enter} | {done} |",
            )
        return "\n".join(lines)
    if key == "matrix":
        return _render_matrix(ctx)
    if key == "progress":
        passed, total = ctx.overall_progress()
        pct = 100.0 * passed / total if total else 0.0
        return f"**{passed} / {total}** = **{pct:.1f}%**  (Σ g(m) / {total})"
    if key == "next-gate":
        return _render_next_gate(ctx)
    if key == "executive-one-line":
        return _render_executive_one_line(ctx)
    if key == "release-rehearsal":
        return _render_release_rehearsal()
    if key == "blockers":
        return _render_blockers()
    if key.startswith("wave-") and key.endswith("-progress"):
        try:
            n = int(key.split("-")[1])
        except ValueError:
            return "_알 수 없는 섹션 키._"
        return _render_wave_progress(ctx, n)
    if key.startswith("wave-") and key.endswith("-risks"):
        return "_위험 등록부 태그 `wave:N` 필터 결과. (데이터 소스 연결 대기)_"
    if key == "risks-top3":
        return "_상위 3건 (월 1회 수동 갱신 예정)._"
    if key == "active-milestone":
        if ctx.active_wave:
            return f"- 현재 외부 태그: **M1** · 내부: `G1.W{ctx.active_wave}.*`"
        return "_활성 마일스톤 미지정._"
    return f"_알 수 없는 섹션 키: {key}_"


def _render_matrix(ctx: RenderContext) -> str:
    """Phase x Wave 매트릭스 — commercial_readiness.py 산출물 기반 실 교차 데이터."""
    lines = [
        "| 작업 흐름 \\ 집단 | W1 (12) | W2 (13) | W3 (14) | W4 (8) |",
        "|---|---|---|---|---|",
    ]
    for phase_idx in range(1, 8):
        cells = [f"P{phase_idx}"]
        phase_data = ctx.phase_wave_matrix.get(phase_idx, {})
        for wave_num in (1, 2, 3, 4):
            if wave_num in phase_data:
                passed, expected = phase_data[wave_num]
                cells.append(f"{passed}/{expected}")
            else:
                cells.append("—")
        lines.append("| " + " | ".join(cells) + " |")
    lines.append("")
    lines.append(
        "_셀 = 해당 Phase 게이트 x 해당 Wave 모듈의 통과/대상. 출처: scripts/audit/commercial_readiness.py GATE_PHASE x WAVES_BY_MODULE._",
    )
    return "\n".join(lines)


def _render_next_gate(ctx: RenderContext) -> str:
    if not ctx.active_wave:
        return "_활성 집단 미지정._"
    return (
        f"- 내부 태그: `G1.W{ctx.active_wave}.K03`\n"
        "- 조건: 활성 집단 전 모듈의 이벤트 체인 일관성 확보\n"
        "- 증거: `scripts/audit/commercial_readiness.py --module <mod>` 통과"
    )


def _render_executive_one_line(ctx: RenderContext) -> str:
    passed, total = ctx.overall_progress()
    pct = 100.0 * passed / total if total else 0.0
    wave_label = f"Wave {ctx.active_wave}" if ctx.active_wave else "(미지정)"
    return f"**활성 {wave_label} · {ctx.active_phase} · 전체 진행률 {pct:.1f}% ({passed}/{total})**"


def _render_release_rehearsal() -> str:
    evidence_dir = REPO / "artifacts" / "rehearsal" / "latest"
    if evidence_dir.exists():
        evidence_files = [p for p in evidence_dir.rglob("*") if p.is_file()]
        if evidence_files:
            return (
                f"- 최근 출시급 실측: 증거 수집됨 ({len(evidence_files)}개)\n"
                f"- 근거: `{evidence_dir.relative_to(REPO)}/`"
            )
        return (
            "- 최근 출시급 실측: 판정 대기\n"
            f"- 근거: `{evidence_dir.relative_to(REPO)}/` (비어 있음)"
        )
    return "- 최근 출시급 실측: 미실행\n- 근거: `artifacts/rehearsal/latest/` (미생성)"


def _render_blockers() -> str:
    handoff = REPO / "HANDOFF.md"
    if handoff.exists():
        text = handoff.read_text(encoding="utf-8")
        status_match = re.search(r"^상태:\s*(.+)$", text, flags=re.MULTILINE)
        status_line = status_match.group(1) if status_match else ""
        if any(token in status_line for token in ("자동 정지", "에스컬레이션", "정지")):
            blocker_state = "블로커 1건"
        elif any(token in status_line for token in ("가동 대기", "완료", "완결", "정상", "대기")):
            blocker_state = "블로커 0건"
        else:
            blocker_state = "판정 보류"
        updated_at = datetime.fromtimestamp(handoff.stat().st_mtime, tz=UTC).strftime(
            "%Y-%m-%dT%H:%M:%SZ"
        )
        return (
            f"- 상태 원문: {status_line or '(없음)'}\n"
            f"- 판정: {blocker_state}\n"
            f"- 마지막 갱신: {updated_at}\n"
            "- 근거: `HANDOFF.md`"
        )
    return (
        "- 상태 원문: (없음)\n"
        "- 판정: 판정 보류\n"
        "- 마지막 갱신: _알 수 없음_\n"
        "- 근거: `HANDOFF.md` (없음)"
    )


def _render_wave_progress(ctx: RenderContext, wave: int) -> str:
    mods = ctx.modules_in_wave(wave, WAVE_MODULES)
    if not mods:
        return f"_집단 {wave} 모듈 데이터 없음._"
    total_passed = sum(m.passed for m in mods)
    total_judg = len(mods) * TOTAL_GATES
    pct = 100.0 * total_passed / total_judg if total_judg else 0.0
    best = max(mods, key=lambda m: m.passed)
    return (
        f"- 집단 {wave}: {total_passed} / {total_judg} 기준 통과 ({pct:.1f}%)\n"
        f"- 모듈 수: {len(mods)}\n"
        f"- 최고 통과 모듈: {best.module} ({best.passed}/23)"
    )


# ---------------------------------------------------------------------------
# 블록 인식 정규식 — named groups 로 index 혼동 방지
# ---------------------------------------------------------------------------

AUTO_BLOCK_RE = re.compile(
    r"(?P<open><!--\s*status-auto:(?P<key>[\w-]+)\s*-->)"
    r"(?P<body>.*?)"
    r"(?P<close><!--\s*/status-auto:(?P=key)\s*-->)",
    re.DOTALL,
)
EMBED_BLOCK_RE = re.compile(
    r"(?P<open><!--\s*status-auto-embed:(?P<key>[\w-]+)\s*-->)"
    r"(?P<body>.*?)"
    r"(?P<close><!--\s*/status-auto-embed:(?P=key)\s*-->)",
    re.DOTALL,
)
WAVE_MODULE_BLOCK_RE = re.compile(
    r"(?P<open><!--\s*wave-module-table:(?P<wave>\d+)\s*-->)"
    r"(?P<body>.*?)"
    r"(?P<close><!--\s*/wave-module-table:(?P=wave)\s*-->)",
    re.DOTALL,
)


def _render_wave_module_table(wave: int, ctx: RenderContext) -> str:
    """Wave N 의 모듈 표 — 모듈명 · 현재 라벨 · 23 기준 통과 수."""
    modules = WAVE_MODULES.get(wave, [])
    lines = [
        f"_Wave {wave} 의 {len(modules)} 모듈. 정본: ADR-0012 §6. 자동 렌더._",
        "",
        "| 모듈 | 현재 라벨 | 통과 | 실패 | 구현 | /23 |",
        "|---|---|---|---|---|---|",
    ]
    by_name = {m.module: m for m in ctx.modules}
    for name in modules:
        mod = by_name.get(name)
        if mod:
            lines.append(
                f"| `{name}` | **{mod.label}** | {mod.passed} | {mod.failed} | {mod.implemented} | /23 |",
            )
        else:
            lines.append(f"| `{name}` | _데이터 없음_ | - | - | - | /23 |")
    return "\n".join(lines)


OPEN_ANY_RE = re.compile(r"<!--\s*status-auto(?P<type>-embed)?:(?P<key>[\w-]+)\s*-->")
CLOSE_ANY_RE = re.compile(r"<!--\s*/status-auto(?P<type>-embed)?:(?P<key>[\w-]+)\s*-->")


def repair_unclosed_blocks(text: str) -> str:
    """여는 주석만 있고 닫는 주석이 없는 블록을 복구한다.

    다음 여는 주석 또는 '## ' 헤더 또는 '---' 구분선 직전에서 블록을 닫는다.
    이미 올바르게 닫힌 블록은 그대로 둔다.
    """
    lines = text.splitlines(keepends=True)
    out: list[str] = []
    open_key: str | None = None
    open_type: str = ""  # "-embed" 또는 ""

    def close_now() -> str:
        return f"<!-- /status-auto{open_type}:{open_key} -->\n\n"

    for line in lines:
        stripped = line.strip()
        m_close = CLOSE_ANY_RE.match(stripped)
        m_open = OPEN_ANY_RE.match(stripped)

        if m_close:
            # 닫는 주석 그대로 유지하고 open 상태 해제
            out.append(line)
            open_key = None
            open_type = ""
            continue

        if m_open:
            # 이전 open 이 살아있으면 먼저 닫고 새 open 시작
            if open_key is not None:
                out.append(close_now())
            open_key = m_open.group("key")
            open_type = m_open.group("type") or ""
            out.append(line)
            continue

        # open 상태에서 강제 종료 시그널 감지 (## 헤더, --- 수평선)
        if open_key is not None and (line.startswith(("## ", "---"))):
            out.append(close_now())
            open_key = None
            open_type = ""
            out.append(line)
            continue

        out.append(line)

    if open_key is not None:
        out.append(close_now())
    return "".join(out)


def render_file(path: Path, ctx: RenderContext, *, skip_generated_at: bool = False) -> str:
    text = path.read_text(encoding="utf-8")
    text = repair_unclosed_blocks(text)

    def _sub_auto(m: re.Match[str]) -> str:
        body = "\n" + render_section(m.group("key"), ctx).strip() + "\n"
        return m.group("open") + body + m.group("close")

    def _sub_embed(m: re.Match[str]) -> str:
        body = "\n" + render_section(m.group("key"), ctx).strip() + "\n"
        return m.group("open") + body + m.group("close")

    def _sub_wave_table(m: re.Match[str]) -> str:
        wave = int(m.group("wave"))
        body = "\n" + _render_wave_module_table(wave, ctx).strip() + "\n"
        return m.group("open") + body + m.group("close")

    text = AUTO_BLOCK_RE.sub(_sub_auto, text)
    text = EMBED_BLOCK_RE.sub(_sub_embed, text)
    text = WAVE_MODULE_BLOCK_RE.sub(_sub_wave_table, text)

    if path.name == "status.md" and not skip_generated_at:
        now_iso = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
        text = re.sub(
            r"(^generated_at:\s*).*",
            lambda mm: f"{mm.group(1)}{now_iso}",
            text,
            count=1,
            flags=re.MULTILINE,
        )
    return text


def iter_render_targets() -> list[Path]:
    return [
        ROADMAP_DIR / "status.md",
        ROADMAP_DIR / "README.md",
        ROADMAP_DIR / "overview.md",
        ROADMAP_DIR / "milestones.md",
        ROADMAP_DIR / "matrix.md",
        ROADMAP_DIR / "engineering" / "README.md",
        ROADMAP_DIR / "engineering" / "phase-timeline.md",
        ROADMAP_DIR / "engineering" / "waves" / "wave-1.md",
        ROADMAP_DIR / "engineering" / "waves" / "wave-2.md",
        ROADMAP_DIR / "engineering" / "waves" / "wave-3.md",
        ROADMAP_DIR / "engineering" / "waves" / "wave-4.md",
        ROADMAP_DIR / "gates" / "README.md",
    ]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="로드맵 status 블록 렌더러")
    parser.add_argument("--check", action="store_true", help="diff 만 보고 기록하지 않음 (CI)")
    args = parser.parse_args(argv)

    modules, labels, pw_matrix = parse_commercial_status(COMMERCIAL_STATUS)
    waves, active_wave = parse_wave_status(WAVE_STATUS)
    ctx = RenderContext(
        modules=modules,
        waves=waves,
        active_wave=active_wave,
        label_distribution=labels,
        phase_wave_matrix=pw_matrix,
    )

    changed: list[Path] = []
    for path in iter_render_targets():
        if not path.exists():
            sys.stderr.write(f"[warn] 대상 파일 없음: {path}\n")
            continue
        before = path.read_text(encoding="utf-8")
        after = render_file(path, ctx, skip_generated_at=args.check)
        if before != after:
            changed.append(path)
            if not args.check:
                path.write_text(after, encoding="utf-8")

    if args.check and changed:
        sys.stderr.write(
            "다음 파일의 auto 섹션이 최신 데이터와 다릅니다. 렌더 스크립트 실행하세요:\n"
        )
        for p in changed:
            sys.stderr.write(f"  {p.relative_to(REPO)}\n")
        return 1

    sys.stdout.write(f"갱신 {len(changed)} 파일 / 대상 {len(iter_render_targets())} 파일\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
