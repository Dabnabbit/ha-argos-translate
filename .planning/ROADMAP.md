# Roadmap: Argos Translate

## Milestones

- ✅ **v1.0 MVP** — Phases 1-3 (shipped 2026-02-21)
- [ ] **v1.1 Enhancement** — Phases 4-6 (in progress)

## Phases

<details>
<summary>✅ v1.0 MVP (Phases 1-3) — SHIPPED 2026-02-21</summary>

- [x] Phase 1: API Client + Data Layer (2/2 plans) — completed 2026-02-21
- [x] Phase 2: Translation Service + Card (2/2 plans) — completed 2026-02-21
- [x] Phase 3: Polish + Validation (2/2 plans) — completed 2026-02-21

Full details: `.planning/milestones/v1.0-ROADMAP.md`

</details>

### v1.1 Enhancement

- [x] **Phase 4: Options Flow Fix** — Users can reconfigure server credentials without re-adding the integration
- [ ] **Phase 5: Auto-Detect + Card Polish** — Users can translate without knowing the source language; card is accessible and responsive (UAT gap closure in progress)
- [ ] **Phase 6: Deploy Validation + Stabilization** — Integration is verified working on real HA hardware and ready for release

## Phase Details

### Phase 4: Options Flow Fix
**Goal**: Users can reconfigure host, port, API key, and SSL without removing and re-adding the integration, and changes take effect immediately
**Depends on**: Nothing (first phase of v1.1; v1.0 shipped)
**Requirements**: OPTS-01, OPTS-02
**Success Criteria** (what must be TRUE):
  1. User opens Integration settings, changes host or API key, saves, and the integration immediately connects to the new server without a HA restart
  2. Saving an invalid host in options shows a connection error before committing the change
  3. After saving valid new credentials, HA logs show the integration reloading and the coordinator rebuilding against the new server address
**Plans:** 1 plan (complete)
Plans:
- [x] 04-01-PLAN.md — Add async_reload to options flow + reload test assertions

### Phase 5: Auto-Detect + Card Polish
**Goal**: Users can translate without selecting a source language, see the detected language in the card, and interact with an accessible and mobile-friendly card
**Depends on**: Phase 4
**Requirements**: DTCT-01, DTCT-02, DTCT-03, DTCT-04, DTCT-05, DTCT-06, CPOL-01, CPOL-02, CPOL-03, CPOL-04
**Success Criteria** (what must be TRUE):
  1. User selects "Auto-detect" in the source dropdown, translates text, and sees "Detected: [Language] ([confidence]%)" appear below the output
  2. Automation author calls `argos_translate.translate` with `source: "auto"` and receives `detected_language` and `detection_confidence` in the response data
  3. When source is "Auto-detect", the target dropdown shows all available languages (not filtered by source)
  4. When the detected language is not installed, the card shows a user-visible message explaining the limitation instead of silently failing
  5. Card displays specific error messages distinguishing connection failure, bad request, and timeout; disabled translate button shows a reason why it is disabled; all form controls have ARIA labels; language row wraps properly on narrow screens
**Plans:** 4 plans (3 complete, 1 gap closure)
Plans:
- [x] 05-01-PLAN.md — Backend auto-detect: api.py /detect + dict return, services.py validation bypass + detection fields, tests
- [x] 05-02-PLAN.md — Card polish: error discrimination, disabled button reason, ARIA labels, responsive layout with CSS container queries
- [x] 05-03-PLAN.md — Card auto-detect UI: Auto-detect dropdown default, target filtering, detection feedback display
- [ ] 05-04-PLAN.md — UAT gap closure: swap pair validation, status indicator update, container query fix, grid height, textarea resize

### Phase 6: Deploy Validation + Stabilization
**Goal**: Integration is verified working end-to-end on a real Home Assistant instance and all bugs discovered during testing are resolved
**Depends on**: Phase 5
**Requirements**: STAB-01, STAB-02, STAB-03, STAB-04
**Success Criteria** (what must be TRUE):
  1. Integration installs via manual copy to `custom_components/` on a real HA instance and loads without errors in the HA log
  2. Config flow completes successfully against the real LibreTranslate server running on the homelab QNAP
  3. All sensors show correct values, the translate service call returns translated text, and the Lovelace card functions correctly on real hardware
  4. Any bugs found during manual testing are fixed with corresponding test updates, and CI passes cleanly
**Plans**: TBD

## Progress

| Phase | Milestone | Plans Complete | Status | Completed |
|-------|-----------|----------------|--------|-----------|
| 1. API Client + Data Layer | v1.0 | 2/2 | Complete | 2026-02-21 |
| 2. Translation Service + Card | v1.0 | 2/2 | Complete | 2026-02-21 |
| 3. Polish + Validation | v1.0 | 2/2 | Complete | 2026-02-21 |
| 4. Options Flow Fix | v1.1 | 1/1 | Complete | 2026-02-21 |
| 5. Auto-Detect + Card Polish | v1.1 | 3/4 | UAT gap closure | — |
| 6. Deploy Validation + Stabilization | v1.1 | 0/? | Not started | — |
