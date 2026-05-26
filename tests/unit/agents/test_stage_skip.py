from __future__ import annotations

from scripts.agents.stage_skip import evaluate_skip


def test_FE_only_변경은_be_typebridge_skip() -> None:
    skip = evaluate_skip(
        changed_files=["web/app/buying/price/page.tsx"],
        plan_meta=None,
        public_iface_changed=False,
    )
    assert skip == {"be", "typebridge"}


def test_BE_only_공개_iface_변경_없음은_typebridge_fe_visual_skip() -> None:
    skip = evaluate_skip(
        changed_files=["services/buying/app/routers/price.py"],
        plan_meta=None,
        public_iface_changed=False,
    )
    assert skip == {"typebridge", "fe", "visual"}


def test_BE_only_공개_iface_변경시_fe_visual_skip() -> None:
    skip = evaluate_skip(
        changed_files=["services/buying/app/routers/price.py"],
        plan_meta=None,
        public_iface_changed=True,
    )
    assert skip == {"fe", "visual"}


def test_BE와_FE_동시_변경은_skip_없음() -> None:
    skip = evaluate_skip(
        changed_files=[
            "services/buying/app/routers/price.py",
            "web/app/buying/price/page.tsx",
        ],
        plan_meta=None,
        public_iface_changed=True,
    )
    assert skip == set()


def test_plan_메타_pipeliner_skip_stages_override() -> None:
    skip = evaluate_skip(
        changed_files=[
            "services/buying/app/routers/price.py",
            "web/app/buying/price/page.tsx",
        ],
        plan_meta={"pipeliner_skip_stages": ["visual"]},
        public_iface_changed=True,
    )
    assert "visual" in skip
