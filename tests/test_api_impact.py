"""API tests for the Phase 7 impact / reverse-index endpoint."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient

from govops.api import app, config_store
from govops.config import ApprovalStatus, ConfigValue, ValueType


UTC = timezone.utc


@pytest.fixture
def client():
    config_store.clear()
    _seed_fixture()
    with TestClient(app) as c:
        yield c
    config_store.clear()


def _seed_fixture() -> None:
    """Seed three jurisdictions worth of records spanning two distinct citations,
    one global entry, and one rejected supersession that must be filtered out.
    """
    config_store.put(
        ConfigValue(
            domain="rule",
            key="ca-oas.rule.age-65.min_age",
            jurisdiction_id="ca-oas",
            value=65,
            value_type=ValueType.NUMBER,
            effective_from=datetime(1985, 1, 1, tzinfo=UTC),
            citation="OAS Act, R.S.C. 1985, c. O-9, s. 3(1)",
            author="seed",
            approved_by="seed",
            rationale="Original min age.",
        )
    )
    config_store.put(
        ConfigValue(
            domain="rule",
            key="ca-oas.rule.age-65.min_years",
            jurisdiction_id="ca-oas",
            value=10,
            value_type=ValueType.NUMBER,
            effective_from=datetime(1985, 1, 1, tzinfo=UTC),
            citation="OAS Act, R.S.C. 1985, c. O-9, s. 3(2)",
            author="seed",
            approved_by="seed",
            rationale="Original min residency.",
        )
    )
    # A rejected proposal that also references the same statute — must NOT
    # appear in impact results.
    config_store.put(
        ConfigValue(
            domain="rule",
            key="ca-oas.rule.age-65.min_age",
            jurisdiction_id="ca-oas",
            value=70,
            value_type=ValueType.NUMBER,
            effective_from=datetime(2032, 1, 1, tzinfo=UTC),
            citation="OAS Act, R.S.C. 1985, c. O-9, s. 3(1)",
            author="reviewer",
            rationale="Out-of-scope proposal; rejected.",
            status=ApprovalStatus.REJECTED,
        )
    )
    # A different jurisdiction with its own statute.
    config_store.put(
        ConfigValue(
            domain="rule",
            key="fr-cnav.rule.age.min_age",
            jurisdiction_id="fr-cnav",
            value=62,
            value_type=ValueType.NUMBER,
            effective_from=datetime(2010, 11, 9, tzinfo=UTC),
            citation="Code de la sécurité sociale, art. L. 161-17-2",
            author="seed",
            approved_by="seed",
            rationale="French statutory min age.",
        )
    )
    # A global record (jurisdiction_id=None) referencing GovOps engine convention.
    config_store.put(
        ConfigValue(
            domain="engine",
            key="global.engine.evidence.dob_types",
            jurisdiction_id=None,
            value=["birth_certificate", "passport"],
            value_type=ValueType.LIST,
            effective_from=datetime(2024, 1, 1, tzinfo=UTC),
            citation="GovOps engine convention v1.0",
            author="seed",
            approved_by="seed",
            rationale="Accepted DOB evidence types.",
        )
    )


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------


class TestImpactValidation:
    def test_missing_citation_returns_400(self, client):
        r = client.get("/api/impact")
        assert r.status_code == 400
        assert "citation" in r.json()["detail"].lower()

    def test_blank_citation_returns_400(self, client):
        r = client.get("/api/impact", params={"citation": "   "})
        assert r.status_code == 400


# ---------------------------------------------------------------------------
# Matching behaviour
# ---------------------------------------------------------------------------


class TestImpactMatching:
    def test_matches_oas_act_records(self, client):
        r = client.get("/api/impact", params={"citation": "OAS Act"})
        assert r.status_code == 200
        data = r.json()
        assert data["query"] == "OAS Act"
        assert data["total"] == 2
        keys_returned = {
            v["key"] for section in data["results"] for v in section["values"]
        }
        assert keys_returned == {
            "ca-oas.rule.age-65.min_age",
            "ca-oas.rule.age-65.min_years",
        }

    def test_match_is_case_insensitive(self, client):
        r = client.get("/api/impact", params={"citation": "oas act"})
        assert r.status_code == 200
        assert r.json()["total"] == 2

    def test_normalized_query_collapses_whitespace(self, client):
        r = client.get("/api/impact", params={"citation": "OAS    Act"})
        data = r.json()
        assert data["query"] == "OAS Act"
        assert data["total"] == 2

    def test_excludes_rejected_records(self, client):
        # The rejected ca-oas record at 2032 has citation "OAS Act, ... s. 3(1)"
        # Even with a precise match it must not appear.
        r = client.get(
            "/api/impact",
            params={"citation": "OAS Act, R.S.C. 1985, c. O-9, s. 3(1)"},
        )
        data = r.json()
        # Only the 1985 approved min_age record matches; the rejected supersession is filtered.
        assert data["total"] == 1
        only = data["results"][0]["values"][0]
        assert only["status"] == "approved"

    def test_no_matches_returns_empty_results(self, client):
        r = client.get("/api/impact", params={"citation": "nonexistent statute"})
        data = r.json()
        assert data["total"] == 0
        assert data["jurisdiction_count"] == 0
        assert data["results"] == []


# ---------------------------------------------------------------------------
# Grouping & labels
# ---------------------------------------------------------------------------


class TestImpactGrouping:
    def test_groups_by_jurisdiction(self, client):
        # Match across all citations: every approved record in the fixture
        # references something — but no single substring matches all four.
        # Pick "1985" which appears in both CA citations + nothing else.
        r = client.get("/api/impact", params={"citation": "1985"})
        data = r.json()
        assert data["jurisdiction_count"] == 1
        section = data["results"][0]
        assert section["jurisdiction_id"] == "ca-oas"
        assert len(section["values"]) == 2

    def test_global_records_appear_under_global_label(self, client):
        r = client.get("/api/impact", params={"citation": "GovOps engine"})
        data = r.json()
        assert data["total"] == 1
        section = data["results"][0]
        assert section["jurisdiction_id"] is None
        assert section["jurisdiction_label"] == "Global"

    def test_global_section_listed_first(self, client):
        # Add a record sharing a citation token with the global one.
        config_store.put(
            ConfigValue(
                domain="rule",
                key="ca-oas.rule.engine-marker",
                jurisdiction_id="ca-oas",
                value=1,
                value_type=ValueType.NUMBER,
                effective_from=datetime(2024, 1, 1, tzinfo=UTC),
                citation="GovOps engine convention v1.0 — CA reference",
                author="seed",
                approved_by="seed",
                rationale="Test fixture.",
            )
        )
        r = client.get("/api/impact", params={"citation": "GovOps engine"})
        data = r.json()
        assert data["jurisdiction_count"] == 2
        assert data["results"][0]["jurisdiction_id"] is None
        assert data["results"][1]["jurisdiction_id"] == "ca-oas"

    def test_jurisdiction_label_resolves_via_registry(self, client):
        r = client.get("/api/impact", params={"citation": "OAS Act"})
        section = r.json()["results"][0]
        # Label is "Old Age Security (OAS) — Canada (federal)" or similar — exact
        # text comes from the registry, but it must include both program + country.
        label = section["jurisdiction_label"]
        assert "Old Age Security" in label
        assert "Canada" in label

    def test_unknown_jurisdiction_prefix_falls_back_to_raw_id(self, client):
        config_store.put(
            ConfigValue(
                domain="rule",
                key="zz-test.rule.example",
                jurisdiction_id="zz-test",
                value=1,
                value_type=ValueType.NUMBER,
                effective_from=datetime(2024, 1, 1, tzinfo=UTC),
                citation="Hypothetical Act, s. 1",
                author="seed",
                approved_by="seed",
                rationale="Test.",
            )
        )
        r = client.get("/api/impact", params={"citation": "Hypothetical Act"})
        section = r.json()["results"][0]
        assert section["jurisdiction_id"] == "zz-test"
        assert section["jurisdiction_label"] == "zz-test"


# ---------------------------------------------------------------------------
# Response shape contract
# ---------------------------------------------------------------------------


def test_impact_response_shape(client):
    r = client.get("/api/impact", params={"citation": "OAS Act"})
    assert r.status_code == 200
    data = r.json()
    assert set(data.keys()) == {"query", "total", "jurisdiction_count", "results"}
    for section in data["results"]:
        assert set(section.keys()) == {"jurisdiction_id", "jurisdiction_label", "values"}
        for v in section["values"]:
            # Each value is a serialised ConfigValue — sanity-check the load-bearing fields.
            assert "id" in v
            assert "key" in v
            assert "citation" in v
            assert "effective_from" in v
            assert "status" in v
