"""설비보전 엔티티 메타 선언 단위 테스트."""

from __future__ import annotations

from oneerp_qm_app.maintenance.entities import ENTITY_METAS


class Test엔티티메타:
    """EntityMeta 선언 정합성 테스트."""

    def test_엔티티_수(self) -> None:
        """10개 엔티티가 선언되어야 한다."""
        assert len(ENTITY_METAS) == 10

    def test_컬렉션명_중복_없음(self) -> None:
        """컬렉션명이 중복되지 않아야 한다."""
        collections = [em.collection for em in ENTITY_METAS]
        assert len(collections) == len(set(collections))

    def test_프리픽스_중복_없음(self) -> None:
        """넘버링 프리픽스가 중복되지 않아야 한다."""
        prefixes = [em.prefix for em in ENTITY_METAS]
        assert len(prefixes) == len(set(prefixes))

    def test_api_경로_중복_없음(self) -> None:
        """API 경로가 중복되지 않아야 한다."""
        paths = [em.api_path for em in ENTITY_METAS]
        assert len(paths) == len(set(paths))

    def test_마스터_엔티티_존재(self) -> None:
        """마스터 archetype 엔티티가 존재한다."""
        masters = [em for em in ENTITY_METAS if em.archetype == "master"]
        assert len(masters) == 5

    def test_트랜잭션_엔티티_존재(self) -> None:
        """트랜잭션 archetype 엔티티가 존재한다."""
        txns = [em for em in ENTITY_METAS if em.archetype == "transaction"]
        assert len(txns) == 5

    def test_모든_api_경로_v1_포함(self) -> None:
        """모든 API 경로에 /api/v1/ 접두사가 포함되어야 한다."""
        for em in ENTITY_METAS:
            assert em.api_path.startswith("/api/v1/"), (
                f"{em.collection}의 api_path가 /api/v1/로 시작하지 않습니다"
            )
