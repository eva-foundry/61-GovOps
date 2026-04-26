"""Phase 2 backcompat registry — Domain 1 (rule.parameter).

Per [ADR-004](../../docs/design/ADRs/ADR-004-backcompat-during-migration.md),
this module mirrors today's Python constants into ``LEGACY_CONSTANTS`` so
``ConfigStore.resolve_value()`` can resolve rule parameters via the legacy
tier while the substrate is still being seeded (Phase 2 -> Phase 3 -> Phase 6).

Key schema (per [ADR-006](../../docs/design/ADRs/ADR-006-per-parameter-granularity.md)):
``<jurisdiction>.rule.<rule-slug>.<param>``

The jurisdiction segment is the country code ``ca``, ``br``, ``es``, ``fr``,
``de``, or ``ua``. The rule slug is the ``LegalRule.id`` with the leading
``rule-`` (and country-prefix where present) stripped.

This whole module is **deleted at Phase 2 exit** once values move to
``lawcode/<jurisdiction>/config/*.yaml`` (Phase 3) and the substrate
(Phase 6 admin UI). Until then, the registry is the single source of truth
for these defaults.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from govops.config import ConfigStore, register_legacy

# ---------------------------------------------------------------------------
# Domain 1: rule.parameter.*
# ---------------------------------------------------------------------------

# Canada — Old Age Security (OAS)
register_legacy("ca.rule.age-65.min_age", 65)
register_legacy("ca.rule.residency-10.min_years", 10)
register_legacy("ca.rule.residency-10.home_countries", ["CA", "CANADA", "CAN"])
register_legacy("ca.rule.residency-pension-type.full_years", 40)
register_legacy("ca.rule.residency-pension-type.min_years", 10)
register_legacy("ca.rule.legal-status.accepted_statuses", ["citizen", "permanent_resident"])
register_legacy("ca.rule.evidence-age.required_types", ["birth_certificate"])

# Brazil — Aposentadoria por Idade (INSS)
register_legacy("br.rule.age.min_age", 65)
register_legacy("br.rule.contribution.min_years", 15)
register_legacy("br.rule.contribution.home_countries", ["BR", "BRAZIL"])
register_legacy("br.rule.contribution-calc.full_years", 40)
register_legacy("br.rule.contribution-calc.min_years", 15)
register_legacy("br.rule.status.accepted_statuses", ["citizen", "permanent_resident"])
register_legacy("br.rule.evidence.required_types", ["birth_certificate"])

# Spain — Pension de jubilacion
register_legacy("es.rule.age.min_age", 66)
register_legacy("es.rule.contribution-min.min_years", 15)
register_legacy("es.rule.contribution-min.home_countries", ["ES", "SPAIN"])
register_legacy("es.rule.contribution-calc.full_years", 36)
register_legacy("es.rule.contribution-calc.min_years", 15)
register_legacy("es.rule.status.accepted_statuses", ["citizen", "permanent_resident"])
register_legacy("es.rule.evidence.required_types", ["birth_certificate"])

# France — Retraite de base (CNAV)
register_legacy("fr.rule.age.min_age", 64)
register_legacy("fr.rule.trimestres-min.min_years", 2)
register_legacy("fr.rule.trimestres-min.home_countries", ["FR", "FRANCE"])
register_legacy("fr.rule.trimestres-calc.full_years", 43)
register_legacy("fr.rule.trimestres-calc.min_years", 2)
register_legacy("fr.rule.status.accepted_statuses", ["citizen", "permanent_resident"])
register_legacy("fr.rule.evidence.required_types", ["birth_certificate"])

# Germany — Regelaltersrente (DRV)
register_legacy("de.rule.age.min_age", 67)
register_legacy("de.rule.wartezeit.min_years", 5)
register_legacy("de.rule.wartezeit.home_countries", ["DE", "GERMANY"])
register_legacy("de.rule.beitragszeit.full_years", 45)
register_legacy("de.rule.beitragszeit.min_years", 5)
register_legacy("de.rule.status.accepted_statuses", ["citizen", "permanent_resident"])
register_legacy("de.rule.evidence.required_types", ["birth_certificate"])

# Ukraine — Pensiia za vikom (PFU)
register_legacy("ua.rule.age.min_age", 60)
register_legacy("ua.rule.stazh-min.min_years", 25)
register_legacy("ua.rule.stazh-min.home_countries", ["UA", "UKRAINE"])
register_legacy("ua.rule.stazh-calc.full_years", 35)
register_legacy("ua.rule.stazh-calc.min_years", 25)
register_legacy("ua.rule.status.accepted_statuses", ["citizen", "permanent_resident"])
register_legacy("ua.rule.evidence.required_types", ["birth_certificate"])


# ---------------------------------------------------------------------------
# Domain 2: engine.threshold.*
# Evidence-type vocabularies the engine uses to classify supplied evidence
# items. Globally scoped — every jurisdiction's engine reads the same lists.
# ---------------------------------------------------------------------------

register_legacy(
    "global.engine.evidence.dob_types",
    ["birth_certificate", "passport", "id_card"],
)
register_legacy(
    "global.engine.evidence.residency_types",
    ["tax_record", "residency_declaration", "passport_stamps", "utility_bill"],
)


# ---------------------------------------------------------------------------
# Domain 5: global.config.*
# Cross-cutting defaults that aren't tied to a jurisdiction or rule.
# ---------------------------------------------------------------------------

register_legacy("global.config.default_language", "en")
register_legacy(
    "global.config.supported_languages",
    {
        "en": "English",
        "fr": "Francais",
        "pt": "Portugues",
        "es": "Espanol",
        "de": "Deutsch",
        "uk": "Ukrainska",
    },
)


# ---------------------------------------------------------------------------
# Phase 3 helper — substrate is populated from YAML at module import time.
#
# Path resolution: AIA_LAWCODE_PATH overrides the default. The default is
# ``<repo-root>/lawcode/`` derived from this file's location (three levels
# up from src/govops/legacy_constants.py).
#
# Once Phase 3.3 retires the register_legacy() calls above, the YAML files
# under ``lawcode/`` become the single source of truth and this module
# shrinks to just the loader bootstrap + resolve_param() helper.
# ---------------------------------------------------------------------------

_resolver = ConfigStore()


def _default_lawcode_path() -> Path:
    return Path(__file__).resolve().parent.parent.parent / "lawcode"


_lawcode_path = Path(os.environ.get("AIA_LAWCODE_PATH") or _default_lawcode_path())
if _lawcode_path.exists():
    _resolver.load_from_yaml(_lawcode_path)


_JURISDICTION_PREFIX_TO_ID = {
    "ca": "ca-oas",
    "br": "br-inss",
    "es": "es-jub",
    "fr": "fr-cnav",
    "de": "de-drv",
    "ua": "ua-pfu",
    # "global" and "ui" map to the global scope (None / "global" — equivalent).
}

_RP_MISSING: Any = object()


def resolve_param(key: str, default: Any = _RP_MISSING) -> Any:
    """Resolve a parameter via the substrate first, then LEGACY_CONSTANTS.

    Extracts the jurisdiction code from the first dotted segment of the key
    (``ca.rule.age-65.min_age`` → ``ca-oas``) so the substrate query matches
    YAML records scoped to the full jurisdiction id.

    Returns the bare value (not a ``ResolutionResult``). With no default,
    raises ``ConfigKeyNotMigrated`` in strict mode if neither tier holds the
    key. With an explicit ``default``, returns it instead — useful for
    optional lookups (e.g. translation fallbacks) that should never raise.
    """
    prefix = key.split(".", 1)[0]
    jurisdiction_id = _JURISDICTION_PREFIX_TO_ID.get(prefix)
    if default is _RP_MISSING:
        return _resolver.resolve_value(key, jurisdiction_id=jurisdiction_id).value
    return _resolver.resolve_value(
        key, jurisdiction_id=jurisdiction_id, default=default
    ).value


# ---------------------------------------------------------------------------
# Domain 4: ui.label.* (per-key, per-language)
# Mirrors the Jinja-era _TRANSLATIONS dict from i18n.py. Schema:
#   ui.label.<original-key>.<lang>
# Key paths preserve the original dotted key (e.g. ui.label.nav.about.en).
# Once Phase 6 retires the Jinja templates, these entries can be retired
# alongside them; web/src/messages/*.json is the canonical translation
# source for the React frontend.
# ---------------------------------------------------------------------------

register_legacy("ui.label.case.applicant_profile.de", "Antragstellerprofil")
register_legacy("ui.label.case.applicant_profile.en", "Applicant Profile")
register_legacy("ui.label.case.applicant_profile.es", "Perfil del solicitante")
register_legacy("ui.label.case.applicant_profile.fr", "Profil du demandeur")
register_legacy("ui.label.case.applicant_profile.pt", "Perfil do requerente")
register_legacy("ui.label.case.applicant_profile.uk", "Профiль заявника")
register_legacy("ui.label.case.audit_trail.de", "Prufpfad")
register_legacy("ui.label.case.audit_trail.en", "Audit Trail")
register_legacy("ui.label.case.audit_trail.es", "Pista de auditoria")
register_legacy("ui.label.case.audit_trail.fr", "Piste d'audit")
register_legacy("ui.label.case.audit_trail.pt", "Trilha de auditoria")
register_legacy("ui.label.case.audit_trail.uk", "Аудиторський слiд")
register_legacy("ui.label.case.evidence.de", "Nachweise")
register_legacy("ui.label.case.evidence.en", "Evidence")
register_legacy("ui.label.case.evidence.es", "Evidencias")
register_legacy("ui.label.case.evidence.fr", "Preuves")
register_legacy("ui.label.case.evidence.pt", "Evidencias")
register_legacy("ui.label.case.evidence.uk", "Докази")
register_legacy("ui.label.case.full_audit.de", "Vollstandiges Prufpaket")
register_legacy("ui.label.case.full_audit.en", "Full Audit Package")
register_legacy("ui.label.case.full_audit.es", "Paquete de auditoria completo")
register_legacy("ui.label.case.full_audit.fr", "Dossier d'audit complet")
register_legacy("ui.label.case.full_audit.pt", "Pacote de auditoria completo")
register_legacy("ui.label.case.full_audit.uk", "Повний аудиторський пакет")
register_legacy("ui.label.case.human_review.de", "Menschliche Prufung")
register_legacy("ui.label.case.human_review.en", "Human Review")
register_legacy("ui.label.case.human_review.es", "Revision humana")
register_legacy("ui.label.case.human_review.fr", "Revision humaine")
register_legacy("ui.label.case.human_review.pt", "Revisao humana")
register_legacy("ui.label.case.human_review.uk", "Перевiрка людиною")
register_legacy("ui.label.case.missing_evidence.de", "Fehlende Nachweise")
register_legacy("ui.label.case.missing_evidence.en", "Missing Evidence")
register_legacy("ui.label.case.missing_evidence.es", "Evidencias faltantes")
register_legacy("ui.label.case.missing_evidence.fr", "Preuves manquantes")
register_legacy("ui.label.case.missing_evidence.pt", "Evidencias ausentes")
register_legacy("ui.label.case.missing_evidence.uk", "Вiдсутнi докази")
register_legacy("ui.label.case.recommendation.de", "Empfehlung")
register_legacy("ui.label.case.recommendation.en", "Recommendation")
register_legacy("ui.label.case.recommendation.es", "Recomendacion")
register_legacy("ui.label.case.recommendation.fr", "Recommandation")
register_legacy("ui.label.case.recommendation.pt", "Recomendacao")
register_legacy("ui.label.case.recommendation.uk", "Рекомендацiя")
register_legacy("ui.label.case.residency_history.de", "Aufenthaltshistorie")
register_legacy("ui.label.case.residency_history.en", "Residency History")
register_legacy("ui.label.case.residency_history.es", "Historial de residencia")
register_legacy("ui.label.case.residency_history.fr", "Historique de residence")
register_legacy("ui.label.case.residency_history.pt", "Historico de residencia")
register_legacy("ui.label.case.residency_history.uk", "Iсторiя проживання")
register_legacy("ui.label.case.rule_assessment.de", "Regel-fur-Regel-Bewertung")
register_legacy("ui.label.case.rule_assessment.en", "Rule-by-Rule Assessment")
register_legacy("ui.label.case.rule_assessment.es", "Evaluacion regla por regla")
register_legacy("ui.label.case.rule_assessment.fr", "Evaluation regle par regle")
register_legacy("ui.label.case.rule_assessment.pt", "Avaliacao regra por regra")
register_legacy("ui.label.case.rule_assessment.uk", "Оцiнка за правилами")
register_legacy("ui.label.common.back_to_cases.de", "Zuruck zu den Fallen")
register_legacy("ui.label.common.back_to_cases.en", "Back to cases")
register_legacy("ui.label.common.back_to_cases.es", "Volver a casos")
register_legacy("ui.label.common.back_to_cases.fr", "Retour aux dossiers")
register_legacy("ui.label.common.back_to_cases.pt", "Voltar aos casos")
register_legacy("ui.label.common.back_to_cases.uk", "Назад до справ")
register_legacy("ui.label.common.evaluate.de", "Fall bewerten")
register_legacy("ui.label.common.evaluate.en", "Evaluate Case")
register_legacy("ui.label.common.evaluate.es", "Evaluar caso")
register_legacy("ui.label.common.evaluate.fr", "Evaluer le dossier")
register_legacy("ui.label.common.evaluate.pt", "Avaliar caso")
register_legacy("ui.label.common.evaluate.uk", "Оцiнити справу")
register_legacy("ui.label.common.jurisdiction.de", "Rechtsgebiet")
register_legacy("ui.label.common.jurisdiction.en", "Jurisdiction")
register_legacy("ui.label.common.jurisdiction.es", "Jurisdiccion")
register_legacy("ui.label.common.jurisdiction.fr", "Juridiction")
register_legacy("ui.label.common.jurisdiction.pt", "Jurisdicao")
register_legacy("ui.label.common.jurisdiction.uk", "Юрисдикцiя")
register_legacy("ui.label.common.status.de", "Status")
register_legacy("ui.label.common.status.en", "Status")
register_legacy("ui.label.common.status.es", "Estado")
register_legacy("ui.label.common.status.fr", "Statut")
register_legacy("ui.label.common.status.pt", "Estado")
register_legacy("ui.label.common.status.uk", "Статус")
register_legacy("ui.label.common.view.de", "Ansehen")
register_legacy("ui.label.common.view.en", "View")
register_legacy("ui.label.common.view.es", "Ver")
register_legacy("ui.label.common.view.fr", "Voir")
register_legacy("ui.label.common.view.pt", "Ver")
register_legacy("ui.label.common.view.uk", "Переглянути")
register_legacy("ui.label.dashboard.actions.de", "Aktionen")
register_legacy("ui.label.dashboard.actions.en", "Actions")
register_legacy("ui.label.dashboard.actions.es", "Acciones")
register_legacy("ui.label.dashboard.actions.fr", "Actions")
register_legacy("ui.label.dashboard.actions.pt", "Acoes")
register_legacy("ui.label.dashboard.actions.uk", "Дii")
register_legacy("ui.label.dashboard.active_cases.de", "Aktive Falle")
register_legacy("ui.label.dashboard.active_cases.en", "Active Cases")
register_legacy("ui.label.dashboard.active_cases.es", "Casos activos")
register_legacy("ui.label.dashboard.active_cases.fr", "Dossiers actifs")
register_legacy("ui.label.dashboard.active_cases.pt", "Casos ativos")
register_legacy("ui.label.dashboard.active_cases.uk", "Активнi справи")
register_legacy("ui.label.dashboard.applicant.de", "Antragsteller")
register_legacy("ui.label.dashboard.applicant.en", "Applicant")
register_legacy("ui.label.dashboard.applicant.es", "Solicitante")
register_legacy("ui.label.dashboard.applicant.fr", "Demandeur")
register_legacy("ui.label.dashboard.applicant.pt", "Requerente")
register_legacy("ui.label.dashboard.applicant.uk", "Заявник")
register_legacy("ui.label.dashboard.case_id.de", "Fall-ID")
register_legacy("ui.label.dashboard.case_id.en", "Case ID")
register_legacy("ui.label.dashboard.case_id.es", "ID del caso")
register_legacy("ui.label.dashboard.case_id.fr", "No de dossier")
register_legacy("ui.label.dashboard.case_id.pt", "ID do caso")
register_legacy("ui.label.dashboard.case_id.uk", "ID справи")
register_legacy("ui.label.dashboard.dob.de", "Geburtsdatum")
register_legacy("ui.label.dashboard.dob.en", "Date of Birth")
register_legacy("ui.label.dashboard.dob.es", "Fecha de nacimiento")
register_legacy("ui.label.dashboard.dob.fr", "Date de naissance")
register_legacy("ui.label.dashboard.dob.pt", "Data de nascimento")
register_legacy("ui.label.dashboard.dob.uk", "Дата народження")
register_legacy("ui.label.dashboard.legal_status.de", "Rechtsstatus")
register_legacy("ui.label.dashboard.legal_status.en", "Legal Status")
register_legacy("ui.label.dashboard.legal_status.es", "Situacion legal")
register_legacy("ui.label.dashboard.legal_status.fr", "Statut juridique")
register_legacy("ui.label.dashboard.legal_status.pt", "Situacao legal")
register_legacy("ui.label.dashboard.legal_status.uk", "Правовий статус")
register_legacy("ui.label.dashboard.title.de", "Fallubersicht")
register_legacy("ui.label.dashboard.title.en", "Case Dashboard")
register_legacy("ui.label.dashboard.title.es", "Panel de casos")
register_legacy("ui.label.dashboard.title.fr", "Tableau de bord des dossiers")
register_legacy("ui.label.dashboard.title.pt", "Painel de casos")
register_legacy("ui.label.dashboard.title.uk", "Панель справ")
register_legacy("ui.label.footer.license.de", "Offenes offentliches Gut (Apache 2.0)")
register_legacy("ui.label.footer.license.en", "Open Public Good (Apache 2.0)")
register_legacy("ui.label.footer.license.es", "Bien publico abierto (Apache 2.0)")
register_legacy("ui.label.footer.license.fr", "Bien public ouvert (Apache 2.0)")
register_legacy("ui.label.footer.license.pt", "Bem publico aberto (Apache 2.0)")
register_legacy("ui.label.footer.license.uk", "Вiдкрите суспiльне благо (Apache 2.0)")
register_legacy("ui.label.footer.tagline.de", "Richtliniengesteuerte Dienstleistungsmaschine")
register_legacy("ui.label.footer.tagline.en", "Policy-Driven Service Delivery Machine")
register_legacy("ui.label.footer.tagline.es", "Maquina de prestacion de servicios impulsada por politicas")
register_legacy("ui.label.footer.tagline.fr", "Machine de prestation de services axee sur les politiques")
register_legacy("ui.label.footer.tagline.pt", "Maquina de prestacao de servicos orientada por politicas")
register_legacy("ui.label.footer.tagline.uk", "Полiтично-орiєнтована машина надання послуг")
register_legacy("ui.label.nav.about.de", "Info")
register_legacy("ui.label.nav.about.en", "About")
register_legacy("ui.label.nav.about.es", "Acerca de")
register_legacy("ui.label.nav.about.fr", "A propos")
register_legacy("ui.label.nav.about.pt", "Sobre")
register_legacy("ui.label.nav.about.uk", "Про нас")
register_legacy("ui.label.nav.api.de", "API")
register_legacy("ui.label.nav.api.en", "API")
register_legacy("ui.label.nav.api.es", "API")
register_legacy("ui.label.nav.api.fr", "API")
register_legacy("ui.label.nav.api.pt", "API")
register_legacy("ui.label.nav.api.uk", "API")
register_legacy("ui.label.nav.authority.de", "Autoritatskette")
register_legacy("ui.label.nav.authority.en", "Authority Chain")
register_legacy("ui.label.nav.authority.es", "Cadena de autoridad")
register_legacy("ui.label.nav.authority.fr", "Chaine d'autorite")
register_legacy("ui.label.nav.authority.pt", "Cadeia de autoridade")
register_legacy("ui.label.nav.authority.uk", "Ланцюг повноважень")
register_legacy("ui.label.nav.cases.de", "Falle")
register_legacy("ui.label.nav.cases.en", "Cases")
register_legacy("ui.label.nav.cases.es", "Casos")
register_legacy("ui.label.nav.cases.fr", "Dossiers")
register_legacy("ui.label.nav.cases.pt", "Casos")
register_legacy("ui.label.nav.cases.uk", "Справи")
register_legacy("ui.label.outcome.eligible.de", "BERECHTIGT")
register_legacy("ui.label.outcome.eligible.en", "ELIGIBLE")
register_legacy("ui.label.outcome.eligible.es", "ELEGIBLE")
register_legacy("ui.label.outcome.eligible.fr", "ADMISSIBLE")
register_legacy("ui.label.outcome.eligible.pt", "ELEGIVEL")
register_legacy("ui.label.outcome.eligible.uk", "ПРИДАТНИЙ")
register_legacy("ui.label.outcome.escalate.de", "ESKALIEREN")
register_legacy("ui.label.outcome.escalate.en", "ESCALATE")
register_legacy("ui.label.outcome.escalate.es", "ESCALAR")
register_legacy("ui.label.outcome.escalate.fr", "A TRANSMETTRE")
register_legacy("ui.label.outcome.escalate.pt", "ESCALAR")
register_legacy("ui.label.outcome.escalate.uk", "ПЕРЕДАТИ")
register_legacy("ui.label.outcome.fail.de", "FEHLGESCHLAGEN")
register_legacy("ui.label.outcome.fail.en", "FAIL")
register_legacy("ui.label.outcome.fail.es", "FALLO")
register_legacy("ui.label.outcome.fail.fr", "NON CONFORME")
register_legacy("ui.label.outcome.fail.pt", "REPROVADO")
register_legacy("ui.label.outcome.fail.uk", "НЕ ПРОЙДЕНО")
register_legacy("ui.label.outcome.ineligible.de", "NICHT BERECHTIGT")
register_legacy("ui.label.outcome.ineligible.en", "INELIGIBLE")
register_legacy("ui.label.outcome.ineligible.es", "NO ELEGIBLE")
register_legacy("ui.label.outcome.ineligible.fr", "INADMISSIBLE")
register_legacy("ui.label.outcome.ineligible.pt", "INELEGIVEL")
register_legacy("ui.label.outcome.ineligible.uk", "НЕПРИДАТНИЙ")
register_legacy("ui.label.outcome.insufficient_evidence.de", "UNZUREICHENDE NACHWEISE")
register_legacy("ui.label.outcome.insufficient_evidence.en", "INSUFFICIENT EVIDENCE")
register_legacy("ui.label.outcome.insufficient_evidence.es", "EVIDENCIA INSUFICIENTE")
register_legacy("ui.label.outcome.insufficient_evidence.fr", "PREUVES INSUFFISANTES")
register_legacy("ui.label.outcome.insufficient_evidence.pt", "EVIDENCIAS INSUFICIENTES")
register_legacy("ui.label.outcome.insufficient_evidence.uk", "НЕДОСТАТНЬО ДОКАЗIВ")
register_legacy("ui.label.outcome.needs_evidence.de", "NACHWEIS ERFORDERLICH")
register_legacy("ui.label.outcome.needs_evidence.en", "NEEDS EVIDENCE")
register_legacy("ui.label.outcome.needs_evidence.es", "NECESITA EVIDENCIA")
register_legacy("ui.label.outcome.needs_evidence.fr", "PREUVES REQUISES")
register_legacy("ui.label.outcome.needs_evidence.pt", "NECESSITA EVIDENCIA")
register_legacy("ui.label.outcome.needs_evidence.uk", "ПОТРIБНI ДОКАЗИ")
register_legacy("ui.label.outcome.pass.de", "BESTANDEN")
register_legacy("ui.label.outcome.pass.en", "PASS")
register_legacy("ui.label.outcome.pass.es", "APROBADO")
register_legacy("ui.label.outcome.pass.fr", "CONFORME")
register_legacy("ui.label.outcome.pass.pt", "APROVADO")
register_legacy("ui.label.outcome.pass.uk", "ПРОЙДЕНО")
register_legacy("ui.label.review.approve.de", "Empfehlung genehmigen")
register_legacy("ui.label.review.approve.en", "Approve recommendation")
register_legacy("ui.label.review.approve.es", "Aprobar recomendacion")
register_legacy("ui.label.review.approve.fr", "Approuver la recommandation")
register_legacy("ui.label.review.approve.pt", "Aprovar recomendacao")
register_legacy("ui.label.review.approve.uk", "Затвердити рекомендацiю")
register_legacy("ui.label.review.decision.de", "Entscheidung")
register_legacy("ui.label.review.decision.en", "Decision")
register_legacy("ui.label.review.decision.es", "Decision")
register_legacy("ui.label.review.decision.fr", "Decision")
register_legacy("ui.label.review.decision.pt", "Decisao")
register_legacy("ui.label.review.decision.uk", "Рiшення")
register_legacy("ui.label.review.escalate.de", "An Vorgesetzten eskalieren")
register_legacy("ui.label.review.escalate.en", "Escalate to supervisor")
register_legacy("ui.label.review.escalate.es", "Escalar al supervisor")
register_legacy("ui.label.review.escalate.fr", "Transmettre au superviseur")
register_legacy("ui.label.review.escalate.pt", "Escalar para supervisor")
register_legacy("ui.label.review.escalate.uk", "Передати керiвнику")
register_legacy("ui.label.review.modify.de", "Ergebnis andern")
register_legacy("ui.label.review.modify.en", "Modify outcome")
register_legacy("ui.label.review.modify.es", "Modificar resultado")
register_legacy("ui.label.review.modify.fr", "Modifier le resultat")
register_legacy("ui.label.review.modify.pt", "Modificar resultado")
register_legacy("ui.label.review.modify.uk", "Змiнити результат")
register_legacy("ui.label.review.rationale.de", "Begrundung")
register_legacy("ui.label.review.rationale.en", "Rationale")
register_legacy("ui.label.review.rationale.es", "Justificacion")
register_legacy("ui.label.review.rationale.fr", "Justification")
register_legacy("ui.label.review.rationale.pt", "Justificativa")
register_legacy("ui.label.review.rationale.uk", "Обгрунтування")
register_legacy("ui.label.review.reject.de", "Empfehlung ablehnen")
register_legacy("ui.label.review.reject.en", "Reject recommendation")
register_legacy("ui.label.review.reject.es", "Rechazar recomendacion")
register_legacy("ui.label.review.reject.fr", "Rejeter la recommandation")
register_legacy("ui.label.review.reject.pt", "Rejeitar recomendacao")
register_legacy("ui.label.review.reject.uk", "Вiдхилити рекомендацiю")
register_legacy("ui.label.review.request_info.de", "Weitere Informationen anfordern")
register_legacy("ui.label.review.request_info.en", "Request more information")
register_legacy("ui.label.review.request_info.es", "Solicitar mas informacion")
register_legacy("ui.label.review.request_info.fr", "Demander plus d'informations")
register_legacy("ui.label.review.request_info.pt", "Solicitar mais informacoes")
register_legacy("ui.label.review.request_info.uk", "Запросити додаткову iнформацiю")
register_legacy("ui.label.review.submit.de", "Prufung einreichen")
register_legacy("ui.label.review.submit.en", "Submit Review")
register_legacy("ui.label.review.submit.es", "Enviar revision")
register_legacy("ui.label.review.submit.fr", "Soumettre la revision")
register_legacy("ui.label.review.submit.pt", "Enviar revisao")
register_legacy("ui.label.review.submit.uk", "Надiслати перевiрку")
register_legacy("ui.label.status.decided.de", "Entschieden")
register_legacy("ui.label.status.decided.en", "Decided")
register_legacy("ui.label.status.decided.es", "Decidido")
register_legacy("ui.label.status.decided.fr", "Decide")
register_legacy("ui.label.status.decided.pt", "Decidido")
register_legacy("ui.label.status.decided.uk", "Вирiшено")
register_legacy("ui.label.status.escalated.de", "Eskaliert")
register_legacy("ui.label.status.escalated.en", "Escalated")
register_legacy("ui.label.status.escalated.es", "Escalado")
register_legacy("ui.label.status.escalated.fr", "Transmis")
register_legacy("ui.label.status.escalated.pt", "Escalado")
register_legacy("ui.label.status.escalated.uk", "Передано")
register_legacy("ui.label.status.intake.de", "Eingang")
register_legacy("ui.label.status.intake.en", "Intake")
register_legacy("ui.label.status.intake.es", "Recepcion")
register_legacy("ui.label.status.intake.fr", "Reception")
register_legacy("ui.label.status.intake.pt", "Entrada")
register_legacy("ui.label.status.intake.uk", "Прийом")
register_legacy("ui.label.status.recommendation_ready.de", "Empfehlung bereit")
register_legacy("ui.label.status.recommendation_ready.en", "Recommendation Ready")
register_legacy("ui.label.status.recommendation_ready.es", "Recomendacion lista")
register_legacy("ui.label.status.recommendation_ready.fr", "Recommandation prete")
register_legacy("ui.label.status.recommendation_ready.pt", "Recomendacao pronta")
register_legacy("ui.label.status.recommendation_ready.uk", "Рекомендацiя готова")
