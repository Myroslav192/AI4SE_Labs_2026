# PINES Management Processes — Reporting and Administrative Tools

**Status:** REVIEW PASSED

**Review rounds:** 5; **revisions:** 4; **source documents:** 20; **accepted requirements:** 25.

Review passed means the configured checks found no remaining errors; it is not proof of perfect semantic completeness.

## 1. Scope

Reporting, analysis, batch administrative utilities and supporting infrastructure used by PINES staff, managers and administrators to manage collections, patrons, transactions and financial records across the consortium. This specification covers report content, batch item utilities, data access controls, operational constraints (OS, browsers, accessibility), and developer-provided metadata/documentation. It does not redefine OPAC patron-facing features except where reports read OPAC-created data.

## 2. Priority scale

| Priority | Meaning |
|---|---|
| P1 — Essential | Explicitly high, mandatory or critical obligations, including source-stated compliance and operational necessities. |
| P2 — Important | Standard required capabilities without an explicit critical or optional signal. |
| P3 — Optional | Desirable enhancements or explicitly low-priority capabilities. |

Priorities are inferred from source evidence and include an individual justification. 'Shall' alone does not establish P1.

## 3. Controlled vocabulary

| Term | Definition |
|---|---|
| report template | A saved, administrator-managed report definition that staff can run as-is or (where allowed) clone and modify. |
| background report | A report run as an asynchronous job on the server or reporting subsystem that does not block interactive clients. |
| item transfer | A batch operation that moves item records from one location to another (for pull lists, outreach, mobile libraries, temporary events, etc.). |
| last copy | An item or bibliographic instance that, within the chosen scope (library or system), is the only copy owned by that scope. |
| OPAC | Online Public Access Catalog — the patron-facing web/catalog interface that creates holds and transactions which reports may read. |

## 4. Requirements

### REQ-0001 — Accessibility, standards and platform constraints

**Kind:** constraint. **Priority:** P1.

The system shall comply with accessibility requirements (support screen readers, screen magnification and other assistive technologies and produce standards-compliant HTML), use a fully relational database back-end, and provide development/training environments with migration capability to production. The reporting subsystem shall not constrain OPAC functionality or responsiveness. In keeping with stakeholder accessibility requirements, management processes shall explicitly be usable with screen-reading and screen-magnification software and other assistive technologies and shall produce standards-compliant HTML to permit assistive tools to function. The vendor shall explicitly document the use of a fully relational database back-end and shall provide mechanisms to migrate configurations and artifacts (export/import of templates, permission settings, saved queries and other configuration items) between development, training and production environments to support safe testing and staged rollouts; this migration capability must be described in developer and operational documentation so administrators can reproduce configurations across environments. The training and development environments must be isolated from production data so staff can experiment without risking production (for example by using separate datasets, scrubbed/anonymized data or strict write isolation). The migration/export/import mechanisms described shall support safely moving configurations and artifacts (templates, permission settings, saved queries and other configuration items) between isolated development, training and production environments, and the developer documentation shall describe safe procedures for these migrations. The accessibility requirement shall explicitly reference example assistive technologies used during testing and support (for example: JAWS and NVDA screen readers and ZoomText screen-magnification software) and shall require standards-compliant semantic HTML output with appropriate alt text, ARIA attributes and labels so screen-reading and screen-magnification tools can function with management-reporting interfaces and exported report pages. The developer documentation shall list tested assistive technologies and give guidance on accessible export formats and any known limitations. Stakeholders explicitly stated that Section 508 compliance is mandatory and the documentation shall record that legal requirement; the developer documentation shall list representative assistive technologies used during testing (for example JAWS and NVDA screen readers and ZoomText screen-magnification software) and require standards-compliant semantic HTML output with appropriate alt text, ARIA attributes and labels. The migration/export/import capability between development, training and production environments shall explicitly support moving report templates, permission settings, saved queries and other configuration artifacts and the developer documentation shall describe safe migration procedures, isolation practices (for example scrubbed/anonymized datasets for training) and any known limitations of these migration mechanisms. The system shall comply with Section 508 accessibility requirements; the developer documentation shall list representative assistive technologies used during testing (for example: JAWS and NVDA screen readers and ZoomText screen-magnification software), describe accessible export formats, and document any known limitations so administrators and accessibility testers can reproduce and verify compliance.

**Priority rationale:** Legal accessibility obligations and architectural constraints were explicitly stated by multiple stakeholders and technical staff; compliance is essential.

**Sources:** [DOC-010](#doc-010), [DOC-016](#doc-016), [DOC-018](#doc-018), [DOC-019](#doc-019). **Evidence candidates:** CAND-00071, CAND-00073, CAND-00074, CAND-00076, CAND-00191, CAND-00192, CAND-00193, CAND-00194, CAND-00201, CAND-00202, CAND-00203, CAND-00268, CAND-00163, CAND-00166, CAND-00190, CAND-00302, CAND-00308, CAND-00072.

### REQ-0002 — Operating environment and scalability

**Kind:** constraint. **Priority:** P1.

The system shall support a consortium-scale environment (example scale: 286 locations, ~17M annual circulations, large acquisition volumes), operate on Linux or Solaris servers, be usable via web-browser or Windows client, support IE 6.0+ and Firefox 2.0+ where web-based, and ensure report processing can occur without disrupting OPAC or circulation clients (by background processing, replicas or other architectural separation). The reporting and management processes must not constrain OPAC responsiveness or availability during peak operational periods, and shall explicitly document the supported server operating systems (Linux or Solaris) and architectural separation options (background jobs, reporting replicas or equivalent) used to prevent user-facing disruption. In addition, the specification shall record the deployment/operational assumption that Management Processes are consolidated at a central location and accept input from and provide services to multiple branches/locations (so design, capacity planning and failover considerations assume centralized management-process endpoints); this centralization assumption must be documented alongside the described architectural separation options so implementers and operators understand where services are hosted and how that affects latency, access control and scaling across the consortium. The reporting subsystem shall be designed to work with a fully-relational database schema (for example PostgreSQL); where performance or reproducible historical snapshots justify a separate reporting warehouse or denormalized reporting schema, those designs are permitted provided they are documented, isolated from the production transactional schema, and their synchronization/refresh behaviors are described in the deployment documentation. The reporting subsystem must operate in read-only mode with respect to OPAC data: it may query or replicate OPAC-created data but must not modify OPAC data or state. Historical deployment/operational details shall be recorded as deployment assumptions: historically the primary production environment ran Red Hat Enterprise Linux 5 on a server with dual quad-core CPUs and 32 GB RAM with PostgreSQL 8.3, and a secondary disaster-recovery/reporting site has historically run Solaris 10 on SPARC; these historical details shall be documented for operators and preserved as deployment assumptions where relevant. The deployment and operational-assumption section shall record the historical production environment details: a primary production host that historically ran Red Hat Enterprise Linux 5 on a dual quad-core CPU server with 32 GB RAM and PostgreSQL 8.3, and a secondary disaster-recovery/reporting site that historically ran Solaris 10 on SPARC hardware. The specification shall also record the assumption that Management Processes operate as part of an enterprise-level Library Automation System and shall preserve the documented recommendation to avoid denormalized reporting schemas that fight the relational model (preferring properly-written SQL, replicas or reporting-warehouse approaches where appropriate). The operating-environment and scale description shall also record the documented acquisition throughput literal from stakeholder evidence: 'purchasing and processing over 900,000 items per year' alongside the example scale of 286 locations and ~17M annual circulations. The specification shall reiterate that report processing must be achievable during open hours without disrupting OPAC or circulation clients (for example via background jobs, reporting replicas or equivalent architectural separation) and shall document the operational assumption that Management Processes are consolidated at a central location so implementers can account for latency, access control and scaling across the consortium. For operational clarity the document shall restate required host/platform support (Linux or Solaris), and web-access/browser compatibility constraints (usable via web-browser or Windows client and compatible with Internet Explorer 6.0+ and Firefox 2.0+ where web-based). Record the observed deployment-scale and product-version assumptions for operators: PINES currently operates the system across 286 library locations serving approximately 3.5 million patrons with a collection of approximately 9.6 million items, and the deployment note for the PINES environment records the production application version in use as 1.4.0.4; these figures shall be preserved as deployment-assumption documentation alongside the other historical environment details. Deployment documentation shall record the operational assumption that implementers may rely on the consortium's enterprise infrastructure (for example: redundant servers, backup systems and network connectivity) to meet availability and redundancy requirements; this assumption must be documented so operators understand where additional infrastructure investment may be required. (Source material supplied the numeric example scale and throughput figures and the requirement retains and documents those figures as deployment/operational assumptions.)

**Priority rationale:** Technical constraints and scale were repeatedly called out by IT stakeholders and working-group materials; non-disruption of OPAC is essential to operations.

**Sources:** [DOC-010](#doc-010), [DOC-014](#doc-014), [DOC-016](#doc-016), [DOC-018](#doc-018), [DOC-019](#doc-019). **Evidence candidates:** CAND-00205, CAND-00238, CAND-00265, CAND-00266, CAND-00267, CAND-00270, CAND-00272, CAND-00066, CAND-00067, CAND-00068, CAND-00069, CAND-00070, CAND-00160, CAND-00162, CAND-00167, CAND-00187, CAND-00199, CAND-00188, CAND-00189, CAND-00283, CAND-00284, CAND-00301, CAND-00303, CAND-00304, CAND-00307, CAND-00164.

### REQ-0003 — Authentication and role-based access control

**Kind:** functional. **Priority:** P1.

The system shall support streamlined but optional staff login mechanisms (e.g., card-swipe) and also traditional username/password; every login must identify which staff member is logged in for auditing. User rights shall be defined and administered via roles/security groups (Staff, Local Admin, Library Manager, Global Admin) to simplify permission changes and to control report and template operations. Access control must support assignment at multiple granularities including individuals, workgroups and arbitrary staff groups so administrators can target permissions to operational groupings, and the system shall provide easy-to-use administrative facilities for creating, editing and reassigning roles and permissions to follow staff and organizational changes. The administrative facilities shall make it straightforward to change an individual's effective permissions by modifying their role assignments (so permission changes can be managed via role edits rather than per-user edits), and the system shall record role-assignment changes for audit purposes. Streamlined authentication mechanisms (for example: card-swipe) shall be convenience mechanisms that still result in individual authentication/identification and must not bypass individual authentication entirely; the system shall link the swipe to the authenticated staff identity in the audit trail so each action remains attributable to a specific individual. (Candidate CAND-00144 is assigned here to record provenance for the existing role/permission administration clauses.) The role model shall include a Patron (public/OPAC) role to represent public-facing access; patrons' OPAC-access activities shall be readable by reporting subsystems but patrons shall have no management/reporting write privileges. The specification shall treat the Patron/OPAC role as distinct from staff roles for scope and access-control purposes so OPAC activity is scoped for reporting but does not confer administrative permissions. Changes to a user's assigned role(s) shall propagate to their effective report and template permissions immediately (that is, changing someone from one role to another updates their effective permissions according to the role definitions without requiring manual per-user edits).  The system shall provide a delivered set of example/predefined role templates and suggested permission sets (for example: Front-desk staff with permission to run basic reports and limited filters; Department heads who can create and modify templates; System administrators with full reporting and permission administration rights) so implementers and administrators can adopt or adapt common role configurations. The administrative reporting facilities shall provide a staff-account audit/report that includes, for each staff account, the date of last password change to support security reviews and compliance audits. In addition, the permission taxonomy and delivered role templates shall explicitly include and document the Patron (public/OPAC) role so implementers can clearly distinguish patron-scoped read-only OPAC activities from staff management and reporting privileges. The system shall include session-security measures (for example: configurable inactivity timeouts, automatic screen-lock or explicit logout reminders) to reduce the risk of unattended logged-in terminals; streamlined login mechanisms (for example card-swipe) shall provide immediate access for the staff user but must still result in individual authentication/identification and be recorded in the audit trail so each action remains attributable to a specific individual. Implementers shall implement and document user rights and privileges using security groups and/or roles; the system shall support assignment of those security groups/roles at the granularity of individual users, workgroups and arbitrary staff groups so administrators can target permissions to operational groupings. Role/permission artifacts (role definitions, group assignments and permission mappings) shall be exportable/importable as part of the migration/export/import mechanisms required elsewhere in this specification so role definitions and assignments can be moved between development, training and production environments and reproduced during deployments.

**Priority rationale:** Operational security, auditability and local administrative ease were emphasized repeatedly; ease of role administration and flexible access groups are essential for day-to-day operations.

**Sources:** [DOC-010](#doc-010), [DOC-012](#doc-012), [DOC-013](#doc-013), [DOC-014](#doc-014), [DOC-016](#doc-016), [DOC-018](#doc-018), [DOC-019](#doc-019). **Evidence candidates:** CAND-00140, CAND-00142, CAND-00143, CAND-00204, CAND-00141, CAND-00144, CAND-00165, CAND-00241, CAND-00242, CAND-00260, CAND-00269, CAND-00281, CAND-00282, CAND-00300, CAND-00075.

### REQ-0004 — Batch item transfer utility

**Kind:** functional. **Priority:** P1.

The system shall provide a batch item transfer utility that allows staff with appropriate permissions to: build queries for candidate materials (and save those queries as templates), manually select items from query results, change selected items' location fields for transfer, generate pull/transit lists (printable), and optionally schedule or execute an automatic revert to original location based on elapsed time or event criteria. The utility shall support preview and confirmation before applying changes, an undo mechanism where feasible, printable transit labels and transfer delay alerts, and shall record transfer history for each item. Batch updates shall use transaction-safe processing and be efficient for very large collections. (Sources: DOC-004, DOC-010, DOC-015, DOC-019) The utility shall provide an explicit undo capability for batch transfer operations that allows authorized staff to reverse applied batch location changes; if full immediate reversal is not feasible the system shall provide an explicit rollback operation or a configurable undo window and shall document any limitations of the undo facility. Access to the batch transfer utility shall be controlled by role-based permissions; default authorized roles shall include managers, administrators and transfer coordinators, and the set of authorized roles shall be configurable by administrators. Time-based auto-revert behavior shall be implemented by a configurable scheduled task (operator-configurable frequency) that evaluates transfer records and applies time-based reversion; the system shall also support event-based triggers (for example: status changes such as 'sold' or 'checked out at destination') that can cancel or override scheduled reversion. The system shall implement explicit precedence rules (for example: a 'checked out at destination' event cancels a pending scheduled revert unless an administrator has explicitly configured otherwise) and shall document these precedence and override behaviors. To avoid long-running locks on large collections, batch update operations shall support chunked processing with a configurable batch size and shall provide progress and retry reporting so operators can monitor and recover interrupted jobs; these processing constraints and recommended defaults shall be documented. The transfer utility's selection and confirmation UX shall support multi-select controls (checkboxes), explicit select-all and clear-selection actions, persistent selection across paged results, range/bulk selection operations, and the ability to upload or import barcode/TCN lists to define bulk selections. The preview step shall present a concise human-readable summary (for example: number of items affected, source location(s), destination location(s), and scheduled execution time if any) and require an explicit confirmation action before applying changes. Every transfer operation (manual, scheduled or automatic) shall write an auditable transfer-log entry recording at minimum: operator identifier, timestamp, affected item identifiers, source location, destination location, transfer method (manual/scheduled/automatic), and any optional reason or triggering event; this transfer history must be queryable and reportable to support audit and recovery workflows. Time- or event-based auto-revert definitions shall be configurable per saved transfer (for example: revert after N days unless a specified event occurs) and shall support attaching event-trigger definitions (examples: status change such as 'sold', an explicit 'checked out at destination' event, or manual event markers) to saved transfers; the documented precedence rules shall state how event-based triggers and scheduled reverts interact (for example: a checked-out-at-destination event cancels a pending revert unless an administrator configures an override). In particular, the auto-revert behavior described for saved transfers may be implemented as a configurable scheduled task that periodically evaluates transfer records and applies time- or status-based reversion per the saved-transfer definition; implementers shall support configuring the scheduled frequency and document the scheduled-task behavior.

**Priority rationale:** Multiple cataloging and branch staff identified this as critical for outreach, mobile services, and routine redistribution; technical staff noted batch/transaction safety is essential.

**Sources:** [DOC-004](#doc-004), [DOC-010](#doc-010), [DOC-015](#doc-015). **Evidence candidates:** CAND-00016, CAND-00017, CAND-00018, CAND-00019, CAND-00020, CAND-00021, CAND-00022, CAND-00023, CAND-00024, CAND-00025, CAND-00026, CAND-00027, CAND-00028, CAND-00029, CAND-00030, CAND-00031, CAND-00098, CAND-00148, CAND-00229.

### REQ-0005 — Canned, on-demand and open-template report interfaces

**Kind:** functional. **Priority:** P2.

The system shall support three reporting interfaces: canned report templates (predefined templates runnable ASAP or scheduled), on-demand editable reports for preset categories, and open-template reporting exposing all attributes for advanced ad-hoc queries. Administrators shall be able to create, publish and manage report templates; templates must be runnable as-is, clonable for modification, and support administrator limits on which filters/display fields can be altered. Canned reports shall be discoverable with descriptive hover pop-ups and a delivered set of pre-written templates (including pre-defined board/external-consumer templates); canned templates shall support running by yesterday's data, last week, last month or last year. The specification shall explicitly require a delivered set of pre-defined board reports (for consumption by library boards and other external consumers) that expose the basic statistics required by common state reporting (for example, the Georgia Annual Report), and the canned interface shall support both immediate (ASAP) execution and recurring schedules as part of the shipped product. The system shall support the reporting definitions described in Appendix A and shall ship with delivered templates that implement those Appendix-A definitions (runnable and schedulable). If Appendix A includes machine-readable report definitions the vendor shall document compatibility or provide mapping guidance so implementers can reproduce the Appendix-A reports. The system shall provide a set of pre-defined board/executive report templates targeted to director-level and external-consumer needs; these templates shall be documented, discoverable, installable with the product, and schedulable by authorized users without requiring authorship rights. The shipped product shall include a delivered set of pre-defined canned report templates (installable with the product) implementing Appendix A and shall include the explicitly enumerated canned reports from the source materials, including at minimum: Checkout Count; Renewals Count; Non-Cataloged Count; Circulation Count by Shelving Location; Items Added Count; Items Deleted Count; Items Currently Checked Out; Items Overdue by X Days; Bib Records Count; Bib Records with No Volumes Attached; Patron Count; Patron Count by Home Library; Bills Currently Owed by Patrons; and Detailed Payments Received. Canned reports shall support immediate (ASAP) execution and recurring schedules and shall support selecting common past-data ranges (for example: yesterday, last week, last month, last year) as described in the source. The system shall also support on-demand reports for pre-selected criteria (for maintenance, collection development and similar uses) that authorized users may run as needed. Delivered board/executive templates shall include activity metrics (checkouts, check-ins, holds placed and holds filled) and support cross-tabulation of those metrics by terminal, branch, system, hour, patron age range, patron type and patron location to meet director-level reporting needs; the shipped product shall include the named canned report examples (including Checkout Count and Renewals Count) within the delivered template set. The canned-templates/quick-access UI shall display a hover-over descriptive pop-up for each canned report/template title containing a human-readable description of the report so users can discover what each template produces before running it. The quick-access designer shall include a field-selection affordance (for example checkboxes or similar 'check off' controls) enabling users to select arbitrary report fields or display sections to include in a run. The scheduling UI for canned or quick-access reports shall explicitly support the cadences: Run ASAP, Hourly, Daily, Weekly, Monthly and Yearly.

**Priority rationale:** Stakeholders asked for distinct modes (canned, on-demand, open-template) to cover common and ad-hoc needs; canned/pre-defined board reports were repeatedly requested for governance and external consumption.

**Sources:** [DOC-010](#doc-010), [DOC-012](#doc-012), [DOC-014](#doc-014), [DOC-018](#doc-018). **Evidence candidates:** CAND-00085, CAND-00086, CAND-00090, CAND-00117, CAND-00118, CAND-00135, CAND-00180, CAND-00285, CAND-00286, CAND-00287, CAND-00288, CAND-00289, CAND-00290, CAND-00291, CAND-00292, CAND-00293, CAND-00294, CAND-00295, CAND-00296, CAND-00297, CAND-00298, CAND-00120.

### REQ-0006 — Data quality and bibliographic integrity reports

**Kind:** functional. **Priority:** P2.

The system shall provide data quality reports for identifying bibliographic and item anomalies such as bibliographic records with no volumes attached, records missing specific MARC fields, items with invalid item type or excessively long call numbers, items with zero use count or candidate weeding lists, and a mechanism to retrieve last-edit and last-circulation metadata separately. These outputs shall support generation of weeding candidate lists and related analytics so cataloging staff can perform weeding workflows efficiently; weeding reports shall be easy to run and export and shall be identified as frequently used operational reports. (Sources: DOC-010, DOC-015, DOC-020, DOC-018) Data-quality and weeding outputs shall include counts and listings that support cataloging workflows such as: an 'items edited' count and an auditable way to retrieve/edit-history metadata; lists of items filtered by total use/count thresholds; the ability to list items created within a specified creation-date range; analytics that report the age of the collection by call-number ranges; and counts of bibliographic records edited or added by user and by library so managers can audit contribution volumes and identify training or workflow issues.

**Priority rationale:** Cataloging staff require specialized data-quality and weeding reporting to maintain catalog integrity and support routine weeding decisions; users identified these as frequently used.

**Sources:** [DOC-010](#doc-010), [DOC-014](#doc-014), [DOC-015](#doc-015), [DOC-018](#doc-018). **Evidence candidates:** CAND-00114, CAND-00158, CAND-00181, CAND-00159, CAND-00184, CAND-00248, CAND-00251, CAND-00252, CAND-00254, CAND-00256, CAND-00257.

### REQ-0007 — Deletion-audit and deletion reporting

**Kind:** functional. **Priority:** P1.

The system shall log all successful and attempted (denied) deletions of records (item, patron, bibliographic) to an audit table via database triggers or equivalent, capturing record type, record identifier, user who attempted the deletion, timestamp, and the operator's location; a report interface shall enable aggregation of deletions by period, by user, by location and by type for auditing and compliance. The reporting capability must support counting and tracking deletions per location and for the system as a whole to support local and consortium-level audits. The deletion audit shall record the record's status immediately prior to deletion (for example a 'pre_deletion_status' field) and shall capture an optional operator-supplied deletion_reason where available; these values shall be persisted by the audit trigger (or equivalent) and exposed in the deletion-report interface alongside existing audit fields (record type, identifier, user, timestamp and operator location).

**Priority rationale:** Stakeholders require traceability for accountability and compliance; technical staff indicated database triggers are feasible and necessary.

**Sources:** [DOC-007](#doc-007), [DOC-010](#doc-010), [DOC-015](#doc-015). **Evidence candidates:** CAND-00046, CAND-00048, CAND-00051, CAND-00052, CAND-00155, CAND-00102, CAND-00047, CAND-00049, CAND-00050, CAND-00234.

### REQ-0008 — Developer-provided data specifications, process descriptions and help

**Kind:** functional. **Priority:** P1.

The developer shall supply comprehensive data specifications (field names, types and relationships) for authority, bibliographic, order, item, hold/request and other records used by management reports; a high-level description of major processes (imports/exports, validation flows) and an online, hierarchical, cross-linked HTML help system. Error reporting shall include high-level and low-level, query-specific feedback for administrators. Concretely, the developer-supplied materials must include complete data specifications for authority, bibliographic, order, item and hold/request records, high-level descriptions of import/export and validation processes (including bibliographic record import/export and validation against authority sources), and an online hierarchical HTML help system that documents and illustrates management-reporting features and common administrative workflows. The system shall provide thorough front-end error reporting and feedback for Local and Global System Administrators, including both high-level user-facing messages and low-level, query-specific diagnostic feedback accessible from the administrative interface so administrators can diagnose and correct malformed queries, data-mapping problems, import/export failures and similar issues without relying solely on back-end logs. The developer documentation must describe error message formats and where detailed diagnostics are surfaced in the UI. Management Processes shall interface with external vendor systems using published APIs and/or automated transfers of standard-format data files (for example USMARC21 and EDIFACT); the developer must document supported integration methods, file formats, authentication approaches and expected synchronization/ingest behaviors. Administrative diagnostics shall include, at minimum, the failed SQL statement or query fragment, the implicated table and field(s), the database error code/type, and a human-readable explanation or suggested corrective action; the developer documentation shall describe where and how these diagnostics are surfaced in the administrative UI. The developer documentation shall explicitly describe dependencies on the Acquisitions and Cataloging modules (that is, which Management-Process reports rely on data structures provided by those modules) and shall document supported vendor-integration methods, including published APIs and standard-format file transfers (for example USMARC21 and EDIFACT). The documentation shall note that EDI/ordering data may be present for some vendors but cannot be assumed to be present at every library and shall describe how reports behave when those vendor datasets are missing. The online hierarchical HTML help system shall be full-text searchable and organized for ease of navigation (for example: index/table-of-contents, breadcrumbing and cross-links) so administrators and authors can locate topics quickly and reliably. The online HTML help system shall be usable with common assistive technologies (for example: screen readers and screen-magnification software) and the developer documentation for the help system shall list which assistive technologies were used during testing and describe how accessibility is supported. The help-system documentation shall describe where accessibility-related controls, semantics or landmarks (for example ARIA roles/landmarks, labels or other assistive hooks) are exposed in the help UI so administrators and accessibility testers can locate and verify accessibility features.

**Priority rationale:** Staff need documentation and meaningful error feedback to author and troubleshoot reports; developer-provided specs, process descriptions and help were repeatedly required.

**Sources:** [DOC-010](#doc-010), [DOC-016](#doc-016), [DOC-018](#doc-018), [DOC-019](#doc-019). **Evidence candidates:** CAND-00077, CAND-00078, CAND-00079, CAND-00080, CAND-00206, CAND-00207, CAND-00195, CAND-00196, CAND-00197, CAND-00198, CAND-00200, CAND-00209, CAND-00237, CAND-00271, CAND-00273, CAND-00168, CAND-00208.

### REQ-0009 — Financial reporting and audit trail

**Kind:** functional. **Priority:** P1.

The system shall provide financial reports including value-of-items aggregations (using purchase price fields) for an entire collection or a selected portion, patron account balances by patron/home library/system, fines and charges accrued per period and per type, fines waived per period and branch, and payments by period and payment method. The system shall maintain an auditable ledger of patron payments that records which charges payments are applied to and shall support reconciliation and compliance with applicable accounting/archival retention policies. The reporting capability must explicitly include the ability to generate item-value reports (aggregated value of items for a given scope), support queries for patron accounts with balances greater than a configurable threshold (to identify accounts needing attention), and ensure reports and data archiving comply with standard accounting practice and applicable state, county and municipal auditing requirements. This requirement therefore also covers the system ability to track and verify financial transactions end-to-end (payment application, reconciliation and reporting) as an auditable function. (Sources: DOC-010, DOC-019) Financial reporting shall continue to support queries for patron accounts with balances greater than a configurable threshold. When a payment is processed at the front desk or other channel the system shall apply the payment and update the patron's account balance and related reports in near real-time so staff see the updated state without manual delay. The system shall report payments collected per library/branch and allow filtering and aggregation of payments by branch and time period. The system shall support and enforce configurable data-retention policies for financial and audit records and shall be capable of retaining specified records for 7 years where required by state or local law; administrators must be able to configure retention durations and the system must prevent premature deletion of retained records. The financial reporting capability shall support joining financial data attached to patron records and item records so combined queries and reconciliations may relate payments, fines and item-level charges across those data sources; reports shall break down payments by payment type (for example: cash, credit card, check and similar methods) to support daily reconciliation and auditing; reporting shall also support queries or lists driven by fine/charge-processing reasons (for example a 'fines stopped' or 'fines waived' reason) so operators can retrieve items or accounts filtered by those reasons; finally, the item-value reporting options shall include the ability to aggregate price/value by call-number ranges to support valuation analyses scoped by classification. The financial reporting capability shall include an enhanced 'Aged Debt' detailed report that provides configurable aging buckets, per-branch and per-account detail lines, and exportable outputs to support collections follow-up and reconciliations; this enhancement shall build on any partially-available existing aged-debt outputs and document the fields and calculations used to produce the aging detail.

**Priority rationale:** Finance stakeholders explicitly required value and ledger capabilities and legal/audit compliance; tracking/verification of transactions is essential for accounting integrity.

**Sources:** [DOC-010](#doc-010), [DOC-011](#doc-011), [DOC-014](#doc-014), [DOC-017](#doc-017). **Evidence candidates:** CAND-00124, CAND-00125, CAND-00126, CAND-00127, CAND-00112, CAND-00113, CAND-00110, CAND-00111, CAND-00177, CAND-00128, CAND-00129, CAND-00130, CAND-00131, CAND-00239, CAND-00240, CAND-00249, CAND-00255, CAND-00264.

### REQ-0010 — Historical reporting and reporting warehouse

**Kind:** functional. **Priority:** P2.

The system shall support historical reporting requirements (snapshots for given dates/date ranges). Where required for performance and reproducible historical snapshots, a reporting warehouse or other archival mechanism shall be provided to retain historical state separate from production row-level changes. The system shall indicate whether a result is from a historical snapshot or real-time data. The reporting capability must explicitly support both historical (warehouse/snapshot) queries and real-time reporting modes; the system shall document which mode produced a given result and provide the historical-warehouse option for date-or-date-range selection as requested by stakeholders, and shall identify reports that must be run in real-time (for example, 'what's overdue today') versus those that may rely on snapshots. The historical-reporting capability shall explicitly include a 'snapshot bills' report that can reproduce bill/account state as of a selected past date or date-range; the system shall indicate whether returned results derive from a historical snapshot or from real-time data and shall document the snapshot creation, retention and retrieval behavior for bill/account snapshots.

**Priority rationale:** Users requested historical snapshots and technical staff indicated a warehouse may be required to provide this reliably without impacting production; supporting both real-time and historical modes addresses both operational and reporting needs.

**Sources:** [DOC-010](#doc-010), [DOC-019](#doc-019), [DOC-020](#doc-020). **Evidence candidates:** CAND-00121, CAND-00122, CAND-00211, CAND-00274.

### REQ-0011 — Holds purchase alert

**Kind:** functional. **Priority:** P2.

The system shall provide a 'holds purchase alert' facility that identifies titles with sustained unmet demand (for example high holds-per-copy ratios or a persistent queue of unfilled holds) to assist selectors and acquisitions staff. The alert criteria shall be operator-configurable (for example: holds-per-copy threshold, minimum number of distinct patrons with holds, maximum unfilled-hold age) and the alert shall be runnable per-branch or system scope, exportable (CSV/Excel-compatible), and schedulable as a background job. The documentation shall describe how the alert behaves when supporting acquisitions or EDI/order data are not available at a particular library.

**Priority rationale:** Assists selectors and acquisitions staff in addressing unmet patron demand; operationally useful though not safety-critical.

**Sources:** [DOC-014](#doc-014). **Evidence candidates:** CAND-00261.

### REQ-0012 — Inactive patrons reporting and outreach export

**Kind:** functional. **Priority:** P1.

The system shall generate lists of patrons with no circulation or electronic activity in the last X days, where X is configurable (supporting at least 30, 90, 180, 365 and arbitrary values) and the report can be scoped to System, Home Library, County or other levels. The report shall optionally include current mailing addresses, flag or separate patrons with outstanding fines, allow exclusion rules (do-not-disturb, VIPs, staff, opt-outs), be exportable to CSV and be runnable as a background job for large patron sets. (Sources: DOC-009, DOC-020) The definition of 'electronic activity' used to determine inactivity shall explicitly include accessing digital collections (if integrated) in addition to OPAC login, online hold placement and online renewals. The inactive-patron report shall aggregate electronic-activity events that may be stored across multiple event tables (for example: OPAC logins, online hold placements, online renewals and digital-resource access records) into a single combined query/measure so the inactivity calculation correctly identifies patrons with no activity across all tracked event sources. The inactive-patron report shall explicitly include the ability to produce lists of patrons whose account 'status' field is set to an inactive value (for example: inactive, barred, etc.) and shall permit scoping and export of that list at System, Home Library, County or other configured levels. The documentation shall identify which status values are treated as inactive for reporting purposes and describe how inactive-status patrons interact with exclusion rules (do-not-disturb, opt-outs) and outreach exports. For very large patron sets the inactive-patron report shall support execution as a background job and provide mechanisms for caching report results or intermediate query results to avoid repeated expensive queries; the system documentation shall describe cache behavior, invalidation semantics and any recommended caching strategies for large-scale deployments. When executed at System scope the inactive-patron report shall provide aggregated counts grouped by patrons' Home Library and shall support ranking/sorting of those aggregates (for example: "top N branches by inactive-patron count"); these group-level aggregates shall be included in exported outputs. Additionally, a Home-Library scoped inactive-patron report shall support creating or recording cleanup assignments from the report UI or export/workflow mechanism (for example: assign a cleanup task to a branch or specific staff member, set an optional due date and track assignment status); assignments created from the report must be auditable (recording who created the assignment, timestamp, assignee and any due date) and queryable for follow-up. When run at System scope the inactive-patron report shall provide aggregated counts grouped by patrons' Home Library and shall support ranking/sorting of those aggregates so operators can identify branches with the most inactive patrons; when scoped to a Home Library the report shall support creating or recording cleanup assignments (assignee and optional due date) from the report UI and shall record assignment audit fields (creator, timestamp, assignee and any due date) so assignments are queryable and auditable.

**Priority rationale:** Multiple libraries run these reports routinely for database cleanup and outreach; performance concerns require background processing.

**Sources:** [DOC-009](#doc-009), [DOC-010](#doc-010), [DOC-014](#doc-014). **Evidence candidates:** CAND-00059, CAND-00061, CAND-00062, CAND-00063, CAND-00103, CAND-00058, CAND-00236, CAND-00259, CAND-00065, CAND-00060, CAND-00278, CAND-00279.

### REQ-0013 — Item record purging and last-copy protection

**Kind:** functional. **Priority:** P1.

The system shall provide reports and a safety-controlled utility to identify item records for purging using customizable criteria (status, time in status, last circulation dates, combinations of criteria), assist with batch status conversions, and provide an efficient mechanism to delete volume and copy entries and orphan bibliographic records. Critically, the system shall produce a 'last copy report' that flags items which are the last copy within a chosen scope (branch or system) so catalogers can avoid accidental deletion. Purging operations shall be driven from read-only candidate reports, require a separate explicit confirmation step, and create an audit trail recording who performed actions and when. The utility may be schedulable for recurring runs but must protect against accidental mass deletion. The requirement explicitly covers the requested utility and reports for identifying purge candidates based on customizable criteria such as status. The specification intentionally leaves the choice of automated versus manual purging as an operational decision: purging workflows may be manual operator-initiated actions, scheduled automated runs, or a combination provided that all purge operations are driven from read-only candidate reports, require an explicit confirmation step, create an auditable trail of who performed actions and when, and implement safeguards to prevent accidental mass deletion; the deployment documentation shall state which mode(s) are enabled. The 'last copy' reporting outputs shall explicitly support cataloging workflows by providing bibliographic identifiers and exportable bibliographic context (for example MARC identifiers or OCLC numbers and exportable metadata) so catalogers can safely locate and update WorldCat or other union-catalog entries; the developer documentation shall state this intended use-case and describe which fields are included to support those external cataloging edits. Batch status-conversion and purge-assist workflows driven from candidate reports shall include operational safety controls: a human-readable preview step summarizing number of items affected, source status(es), target status, and scope; a required explicit confirmation action before applying changes; an auditable log entry for every applied batch-status change capturing at minimum operator identifier, timestamp, affected item identifiers, source status, target status and optional reason; and either an immediate undo capability where feasible or a documented configurable undo/rollback window with stated limitations. To avoid long-running locks and to aid recovery, large batch status-change operations shall support chunked processing with a configurable chunk size, progress reporting, and retry/resume semantics. Role-based permissions shall control who may author, schedule or execute bulk status-conversion and purge operations, and administrators must be able to require an elevated confirmation/authorization step for bulk changes that exceed configured thresholds (for example: more than N items or more than X% of a branch's collection). For last-copy detection and reporting, the report shall support both branch-scoped and system-scoped modes: for each item record the system shall evaluate whether any other copies exist within the selected scope (branch or system) and, if none exist, flag the item as a last copy; the report shall expose bibliographic identifiers and exportable bibliographic context (for example MARC identifiers or OCLC numbers) to support cataloging follow-up, and the developer documentation shall describe any caching or replication delays and how those delays affect last-copy detection and reporting latency.

**Priority rationale:** Cataloging and collection staff defined this as critical (last-copy protection named 'CRITICAL'), and stakeholders required safety/audit controls.

**Sources:** [DOC-006](#doc-006), [DOC-010](#doc-010), [DOC-015](#doc-015). **Evidence candidates:** CAND-00037, CAND-00040, CAND-00041, CAND-00042, CAND-00043, CAND-00044, CAND-00045, CAND-00151, CAND-00152, CAND-00153, CAND-00154, CAND-00101, CAND-00233, CAND-00038, CAND-00039.

### REQ-0014 — Material volume reporting

**Kind:** functional. **Priority:** P1.

The system shall provide reports that show the volume of material for a selected library or group of libraries at any point in time, including counts for new acquisitions, items on shelf (checked in) and items out in circulation, and allow breaking down results by category (examples: total items, holds count, adult fiction, board books). Categories shall be configurable per library and templates shall be able to expose custom categories for reuse. Additionally, the reporting capability shall explicitly support analysis of the collection and its use by patrons (circulation patterns and item-level usage) so catalogers and managers can evaluate collection use and inform acquisitions, redistribution and weeding decisions; this analysis must be possible at branch and system scopes and be exportable for further offline analysis. (Sources: DOC-001, DOC-010, DOC-015)

**Priority rationale:** Direct stakeholder request as a key monthly/board reporting need and repeated endorsement across working-group documents; added patron-usage analysis is similarly essential for collection management.

**Sources:** [DOC-001](#doc-001), [DOC-010](#doc-010), [DOC-015](#doc-015), [DOC-017](#doc-017). **Evidence candidates:** CAND-00001, CAND-00002, CAND-00003, CAND-00004, CAND-00094, CAND-00157, CAND-00173.

### REQ-0015 — Miscellaneous quick-access and fine-grained features

**Kind:** functional. **Priority:** P2.

The system shall support assorted usability and integration items requested repeatedly: ability to include selection criteria in outputs (report results shall display the date selection criteria and report name at the top or bottom of outputs to clarify context), upload text files (barcodes/TCNs) to filter reports, allow pivot-compatible exports, allow retrieval of MARC fields in single-row outputs, allow report result comparison columns (month-over-month, percent change), and provide an address-book for delivery recipients. The specification requires visible inclusion of the selection criteria in generated outputs to aid consumers in interpreting exported reports; consequently, the system shall provide the query selections along with results so users can see which filters or selections produced the returned rows. (Sources: DOC-010, DOC-015) The system shall support filtering by survey name (not only survey ID) by resolving survey names to internal IDs internally; the behavior for duplicate names, case-sensitivity and error handling when a name cannot be resolved shall be documented in the administrative documentation. Where survey-response datasets exist (for example: voter survey responses), the reporting subsystem shall support filtering and aggregation on those survey-response fields and shall document the behavior when such datasets are not present. The administrative documentation shall list which survey-response datasets (for example named surveys and their available response fields) are available to reporting and shall describe how the reporting UI and exports behave when a named survey's responses are unavailable.

**Priority rationale:** These features improve day-to-day usability for report consumers and were frequently requested; inclusion of query selections with results prevents misinterpretation of exported reports.

**Sources:** [DOC-010](#doc-010), [DOC-012](#doc-012), [DOC-014](#doc-014), [DOC-019](#doc-019). **Evidence candidates:** CAND-00123, CAND-00137, CAND-00214, CAND-00258.

### REQ-0016 — Missing, damaged and in-transit reporting

**Kind:** functional. **Priority:** P1.

The system shall provide two related reports: (a) missing and damaged items report by branch with optional inclusion of condition notes (e.g., 'water damage', 'vandalism') and time-range filtering for trend analysis; and (b) an in-transit items report that lists items that have been in-transit more than X days (X configurable, default suggested 7 days), merging both transit-to and transit-from perspectives and allowing sorting by due date to prioritize follow-up. Both reports shall be runnable per branch and system-wide and shall support the specific operational need to list missing/damaged items per branch and to list items in-transit beyond a configurable threshold. The missing and damaged-items reports shall include aggregated counts grouped at the bibliographic/title level (per-title counts and a mechanism to flag or rank titles with repeated losses or damage over a selectable time range) so collection managers can identify problem titles. The reports shall also expose underlying item status fields (for example: missing, lost, long overdue), allow selection of which status values to include, and display each item's status in report outputs so counts and lists are interpretable. For in-transit detection the report shall support explicit transit-record conditions such as 'arrival_date is null and departure_date is more than X days ago' as a supported rule to identify items outstanding in transit beyond the configurable threshold; the documentation shall describe the exact transit-record fields and logic used to identify in-transit items. For in-transit detection the report shall support the stakeholder-proposed detection rule (for example: identify transit records where arrival_date is null and departure_date is more than X days ago) as a default or configurable option; the report shall permit administrators to configure alternative detection rules where local transit-record semantics differ and the documentation shall describe the exact transit-record fields and logic used to identify items outstanding in transit.

**Priority rationale:** Front-line and delivery staff repeatedly requested both reports to manage inventory, reduce losses, and coordinate deliveries.

**Sources:** [DOC-005](#doc-005), [DOC-010](#doc-010), [DOC-014](#doc-014), [DOC-015](#doc-015), [DOC-018](#doc-018). **Evidence candidates:** CAND-00034, CAND-00035, CAND-00036, CAND-00149, CAND-00150, CAND-00182, CAND-00183, CAND-00099, CAND-00100, CAND-00032, CAND-00230, CAND-00231, CAND-00232, CAND-00247, CAND-00033.

### REQ-0017 — Patron characteristics and demographic queries

**Kind:** functional. **Priority:** P1.

The system shall support limiting and grouping queries and reports by patron characteristics including configurable age ranges, zip code, county, home branch, patron type, and preferred language; it must support combined filters with AND/OR logic and include records with null/missing values rather than implicitly excluding them. Further, the reporting capability shall explicitly provide demographic-analysis facilities to support program planning (for example, cohort or zip/county-level breakdowns, configurable age-range buckets and language-based groupings) so outreach and program planners can target services based on patron population characteristics. (Sources: DOC-008, DOC-020) Demographic filters and groupings must be combinable with transaction- and activity-based criteria (for example: last-circulation date or inactivity windows such as 'no checkouts in the last N days') so queries like 'Juvenile patrons in zip 30505 with no checkouts in 6 months' are supported; this cross-filtering shall reference the Inactive Patrons reporting capability where appropriate. Data used to generate demographic statistics shall be anonymized prior to export or reporting; personally identifying information must be removed or aggregated so individuals cannot be re-identified, consistent with applicable laws and policies. Reports and statistics that include demographic breakdowns (for example transactions by geographical region and configurable age ranges) must anonymize or aggregate data prior to export or display so individual patrons cannot be re-identified; the documentation shall reference aggregation/suppression practices or thresholds to be determined for the deployment. Where patron age-range buckets are used, the system shall compute each patron's age at query time from the patron birth_date field and allow age brackets (buckets) to be defined and evaluated in the saved query so reports and saved templates reflect dynamic age ranges rather than requiring manual pre-computed age values.

**Priority rationale:** Program planners and outreach staff explicitly requested these filters and groupings for program targeting; configurability and inclusion of nulls were emphasized and demographic-analysis support is similarly critical for planning.

**Sources:** [DOC-008](#doc-008), [DOC-010](#doc-010), [DOC-017](#doc-017), [DOC-018](#doc-018), [DOC-020](#doc-020). **Evidence candidates:** CAND-00053, CAND-00054, CAND-00056, CAND-00057, CAND-00115, CAND-00222, CAND-00175, CAND-00186, CAND-00055, CAND-00093, CAND-00221, CAND-00235.

### REQ-0018 — Query tool and open-template reporting

**Kind:** functional. **Priority:** P1.

The system shall provide a user-friendly query/report designer across all record types (bib, item, patron, transaction, financial) that supports field selection, picklists, Boolean logic (AND/OR), configurable regular-expression use where appropriate, saved queries, and an 'open template' mode exposing all attributes for filtering and display. The open-template mode must expose attributes associated with circulation, patrons, items, bills and bibliographic records for both filtering and display so advanced users can construct fine-grained reports; administrators shall be able to restrict access to tables/fields. This capability must explicitly support the fine-grained reporting requirements described in stakeholder materials (Appendix-style fine-grained report support). The report/query designer shall be available via a web-based interface compatible with the supported browsers listed in the operating-environment requirements. The web-based designer shall allow saved templates and queries to include time-based circulation filters such as a 'last-circulated date' criterion so users can express and persist queries like 'haven't circulated in N months' as saved templates. The web-based query/report designer shall include user-friendly field-selection affordances such as drag-and-drop selection of fields into filter and display areas to simplify report construction for non-technical users; the open-template mode must expose MARC and other bibliographic fields (where present) for both filtering and display so advanced users may construct counts such as circulation-by-MARC-field and other fine-grained bibliographic queries.

**Priority rationale:** Repeated user demand for a flexible query designer and open-template reporting across multiple documents and survey results; fine-grained access is required for advanced administrative reporting.

**Sources:** [DOC-004](#doc-004), [DOC-010](#doc-010), [DOC-012](#doc-012), [DOC-014](#doc-014). **Evidence candidates:** CAND-00081, CAND-00132, CAND-00082, CAND-00091, CAND-00119, CAND-00145, CAND-00228, CAND-00243, CAND-00246.

### REQ-0019 — Report output formats, delivery and export

**Kind:** functional. **Priority:** P2.

Reports shall be exportable in CSV and HTML formats and provide reliable Excel-compatible output (or Excel export) for downstream use (pivot tables). The system shall support emailing report results to specified addresses (address book supported) and include the report selection criteria and report name in outputs. Export formats must preserve all null/blank fields and produce pivot-table-capable output. In particular, the vendor must support CSV exports explicitly to meet directors' spreadsheet needs and to permit integration with outreach systems that ingest CSV data. The system shall therefore explicitly document the supported export formats (CSV, HTML, and Excel-compatible output) and confirm preservation of null/blank fields in CSV exports. The system shall explicitly support Excel-compatible output, HTML and CSV exports and shall preserve null/blank fields in CSV exports. The system shall support emailing report results to specified addresses and shall provide an address-book facility for regularly used recipients. The UI shall permit editing recurring scheduled reports (for example, modify selections, schedule cadence and recipients) so recurring jobs can be maintained and adjusted via the administrative interface.

**Priority rationale:** Export and delivery features are important for directors and integrations; they were requested frequently but are not safety-critical relative to core reporting.

**Sources:** [DOC-002](#doc-002), [DOC-009](#doc-009), [DOC-014](#doc-014), [DOC-019](#doc-019). **Evidence candidates:** CAND-00213, CAND-00010, CAND-00064, CAND-00146, CAND-00210.

### REQ-0020 — Report scheduling, queue visibility, prioritization and cancellation

**Kind:** functional. **Priority:** P1.

The system shall allow reports to be scheduled (ASAP, hourly, daily, weekly, monthly, yearly), run as background jobs, show queue position and status (waiting, running, completed, failed) to requestors, allow certain reports to be prioritized to jump ahead in queue, and permit cancellation of scheduled or running reports. Administrators shall be able to configure recurring reports and their recipients. The system must ensure reports can be queued and processed in the background to avoid disruption during open hours and shall provide queue visibility to requestors so users know expected completion or position. (Sources: DOC-010, DOC-012, DOC-019, DOC-020, DOC-016) The queue display shall show the report submission timestamp (when the job was submitted) and shall display an explicit numeric count of how many reports are ahead of the user's report in addition to status and position indicators; these fields shall be visible in the UI and available in status messages provided to requestors. Long-running and background report processing routines shall periodically check for cancellation signals (or otherwise provide a mechanism to detect and apply cancellation requests) so that user- or administrator-initiated cancellations can be honored in a timely manner; the system documentation shall describe expected cancellation semantics and typical latency for cancellation to take effect. The report scheduling UI shall permit users to multi-select multiple canned or saved reports and queue them to run together as background jobs; each queued job shall have its own queue position and status visible to the requestor and be cancelable individually. The queue display and job-status model shall show each job's submission timestamp and explicit numeric counts of reports ahead of that job, and queued multi-report submissions shall participate in the same prioritization, cancellation and cancellation-latency semantics documented for single-report jobs. The scheduling and queue UI shall allow requestors to see submission timestamp, queue position, job status (waiting, running, completed, failed) and an explicit numeric count of how many jobs are ahead of each job. The UI shall permit multi-selecting multiple canned or saved reports and queuing them to run together as background jobs while treating each queued report as an individually queued job with its own queue position, status and cancellation ability; multi-report submissions shall participate in the same prioritization and cancellation semantics as single-report jobs. Administrators shall be able to configure priority rules so certain authorized reports may jump ahead in the queue, and long-running/background processing routines shall periodically check for cancellation signals (or otherwise provide a mechanism to detect and apply cancellation requests) so user- or administrator-initiated cancellations can be honored in a timely manner; the documentation shall describe expected cancellation semantics and typical latency for cancellation to take effect.

**Priority rationale:** Queue visibility and prioritization were repeatedly reported as operational needs to prevent user confusion and support directors' reporting needs; background processing to avoid disruption is high priority.

**Sources:** [DOC-012](#doc-012), [DOC-014](#doc-014), [DOC-016](#doc-016), [DOC-019](#doc-019), [DOC-020](#doc-020). **Evidence candidates:** CAND-00299, CAND-00138, CAND-00139, CAND-00161, CAND-00212, CAND-00226.

### REQ-0021 — Report templates, permissions and shared folders

**Kind:** functional. **Priority:** P1.

Administrators shall be able to create, publish and manage report templates; templates must be runnable as-is, clonable for modification, and support administrator limits on which filters/display fields can be altered. The system shall support fine-grained permissions for creating, cloning and running reports, and shared folders to manage access by role, workgroup or individual. Role-assignments must be administrable so permission changes follow role changes. The specification shall explicitly require fine-grained controls limiting who can create and clone reports and shall require shared-folder semantics that allow administrators to grant or deny execution, cloning or editing rights on specific templates or folders of templates to particular roles, workgroups or individuals; these shared-folder permissions must be documentable and manageable via the administrative UI so template visibility and editability can be maintained across organizational changes. Shared-folder and template permissions shall support scoping execution rights to particular data scopes (for example: restrict execution of a template to a staff member's branch, to a configured county, or to other configured data groups); administrators must be able to grant or deny execution, cloning or editing rights that are constrained to such data scopes and the administrative UI shall provide controls and auditability for configuring and tracking those scoped permissions. Administrators shall be able to configure template restrictions that prevent templates available to front-line staff from exposing deleted or purged records or other restricted data fields; templates intended for front-line staff must not allow enabling display of deleted/purged records unless an administrator with appropriate privilege explicitly grants that capability and documents that grant in the administrative UI. Administrators shall be able to prevent templates and cloned templates from exposing deleted or purged records or other protected status fields by configuring an administrator-controlled deny-list of display fields; the administrative UI shall make protected/blocked fields visible to administrators when authoring or editing templates and require an explicit administrative override to expose those fields.

**Priority rationale:** High priority across stakeholders for consistent board reports, controlled templates, and easy admin of permissions.

**Sources:** [DOC-010](#doc-010), [DOC-012](#doc-012), [DOC-020](#doc-020). **Evidence candidates:** CAND-00084, CAND-00224, CAND-00225, CAND-00223, CAND-00134, CAND-00083, CAND-00133, CAND-00280.

### REQ-0022 — Shelf-space utilization report

**Kind:** functional. **Priority:** P1.

The system shall produce a shelf-space report, per selected library or for the system, that compares for each genre and format: percentage of total circulations, percentage of the collection, and percentage of total shelf space; the report shall support side-by-side comparison across libraries and date-range filtering. Because shelf space may not be tracked directly, the requirement allows use of calculated estimates (e.g., item dimensions or item-count proxies) and requires the report to document the estimation method used. (Sources: DOC-003, DOC-010, DOC-015) The shelf-space report shall include, for branch-scoped outputs, an explicit system-average comparative value presented alongside the branch's results (for example: a system-average column, overlay or an explicit 'compare to system average' view) so branch managers can directly compare local percentages to the system-wide average; the documentation shall describe the scope and inclusion rules used to compute the system average (for example: which branches are included, whether branches with missing shelf-space estimates are excluded or imputed, and how estimation methods are applied across the system).

**Priority rationale:** Cataloging and collection managers requested this to support weeding/space decisions, and stakeholders emphasized per-branch and system views.

**Sources:** [DOC-003](#doc-003), [DOC-010](#doc-010), [DOC-015](#doc-015), [DOC-018](#doc-018). **Evidence candidates:** CAND-00012, CAND-00013, CAND-00014, CAND-00015, CAND-00096, CAND-00156, CAND-00185, CAND-00011.

### REQ-0023 — System capacity interface

**Kind:** functional. **Priority:** P1.

The system shall provide a high-level interface displaying capacity and key metrics for all branches at once, with the ability to drill down to individual branch detail, sort and filter by region, library type or current load, display trend data (growth/shrink patterns), and export results to CSV for directors. The interface shall support grouping of locations where necessary to avoid overwhelming displays. In addition to the original capacity and trend features, the interface shall explicitly support analysis of branch capacity and optimal distribution of the collection (views and reports that help plan redistribution and placement of material across branches) to aid operational planning and collection balance decisions. (Sources: DOC-002, DOC-010, DOC-018) The capacity overview shall include color-coded visual status indicators (for example: green/yellow/red) to allow quick at-a-glance assessment of branch capacity. Because the source does not define numeric thresholds for the color mappings, those mappings shall be administrator-configurable and documented alongside the interface so implementers/operators are not required to invent threshold values. The capacity overview shall support grouping or aggregation of locations (for example by region or administrator-defined groups) and provide summarized/rolled-up views to avoid overcrowded displays when many branches are present; the interface shall also provide operational-planning views that help managers decide redistribution or resource-allocation across branches (for example summaries highlighting over- and under-utilized locations to support redistribution decisions). The high-level/summary view referenced by this interface must present key metrics in the summary (for example: capacity utilization, growth/shrink trend indicators, and high-level item/hold counts) so operators can assess branch status at-a-glance; these summary metrics must be visible in the overview and be linkable/drillable to the detailed branch views so directors and managers can move from the summary to branch-specific detail efficiently.

**Priority rationale:** Expressed as a system-level need for cross-branch planning and explicitly requested by multiple stakeholders; branch-capacity analysis is an operational priority.

**Sources:** [DOC-002](#doc-002), [DOC-010](#doc-010), [DOC-017](#doc-017), [DOC-018](#doc-018). **Evidence candidates:** CAND-00007, CAND-00008, CAND-00095, CAND-00179, CAND-00174, CAND-00005, CAND-00009, CAND-00227, CAND-00276, CAND-00277, CAND-00006.

### REQ-0024 — Transaction reporting and types

**Kind:** functional. **Priority:** P1.

The system shall retain transaction history for a configurable period (transaction history retained X days configurable) while keeping monthly and annual aggregates indefinitely, and provide reports that group transactions by hour, terminal, branch and system; count types of check-in (book-drop, by terminal, by user/self-service) and check-out (staff checkout, self-checkout, staff renewal, self renewal, online renewals) individually and cumulatively; and produce transaction reports (holds placed, holds filled, check-outs) per patron, per library, per selected group, per system, or per county. Transaction reporting shall include activity reports that indicate traffic and volume of use (check-outs, check-ins, holds placed, holds filled) and support cross-tabulation across axes such as terminal, branch, library system, hour, patron age range, patron type and patron location to support detailed analysis. Archival and transaction-warehouse behavior for retained transactions must support anonymization or other measures required to protect patron privacy per applicable State Law while still providing useful demographic statistics and aggregates for planning and reporting. The system shall also provide holds-specific reporting and allow these reports at branch and system scope. Additionally, the reporting capability shall provide staff-productivity and workflow analysis derived from transaction metrics (for example, per-terminal and per-staff activity, time-based throughput metrics and comparisons) so managers can assess staffing and workflow efficiency; such staff-productivity reports must respect privacy/anonymization rules where required. (Sources: DOC-001, DOC-010, DOC-019) The reporting capability shall produce patron-behavior and predictive metrics such as average time-to-return per title and per branch, renewal rates and renewal likelihood per title/branch, percent renewals, and similar time-series/predictive aggregates; these metrics must be available with grouping and time-range options and be exportable for further analysis. The transaction-reporting capabilities shall support counts and groupings by circulation modifiers (for example: counts by circ-modifier where available) and by classification fields such as Dewey (for example: circulation count by Dewey ranges) where those bibliographic/classification values are available; reports shall be able to list items more than N days overdue together with available patron contact information (subject to privacy/anonymization rules) to support follow-up workflows; additionally the reporting subsystem shall include claims-returned and similar circulation-status event reporting so operational managers can track those workflows. The transaction-reporting capability shall explicitly include 'unfilled holds' and 'stale holds' reports that list holds not yet filled or not progressed within an operator-configurable stale-window, runnable at branch and system scopes and exportable for follow-up. Furthermore, check-in timestamps used for check-in reporting and time-series analyses shall exclude renewal events (that is, renewal actions shall not be treated as physical check-ins); the developer documentation shall define the exact event types that constitute renewals versus check-ins so reports and aggregates reflect true return activity. Transaction reporting shall include fines collected and patron registration events among the transaction event types available for grouping and reporting. The system shall provide reports on pre-overdue notices, overdue notices and holds notices sent (runnable at branch and system scope and exportable) so operational staff can audit and follow up on notice delivery activities.

**Priority rationale:** Detailed transaction counting and grouping are core reporting needs used daily by branches and managers, and staff-productivity analysis is operationally important for staffing and workflow decisions.

**Sources:** [DOC-010](#doc-010), [DOC-012](#doc-012), [DOC-014](#doc-014), [DOC-017](#doc-017), [DOC-020](#doc-020). **Evidence candidates:** CAND-00104, CAND-00105, CAND-00106, CAND-00107, CAND-00108, CAND-00109, CAND-00215, CAND-00216, CAND-00217, CAND-00218, CAND-00219, CAND-00220, CAND-00087, CAND-00088, CAND-00089, CAND-00116, CAND-00136, CAND-00176, CAND-00092, CAND-00244, CAND-00245, CAND-00250, CAND-00253, CAND-00262, CAND-00263, CAND-00275, CAND-00305, CAND-00306.

### REQ-0025 — Uncataloged material inventory and counting

**Kind:** functional. **Priority:** P2.

The system shall provide a minimal-labor workflow to record, distribute and count uncataloged material (e.g., paperback/children's board books) so those transactions contribute to circulation statistics and can be identified in reports while avoiding full cataloging overhead. (Sources: DOC-010, DOC-015) The uncataloged-material workflow shall minimize per-item processing time so branches can distribute these items rapidly, be operable with minimal branch labor, capture how uncataloged materials are being used, and ensure transactions for uncataloged items are counted and included in circulation statistics and exports (for example via a lightweight item-type or flag).  (Source wording preserved: "quick distribution (we need to process these fast), minimal branch labor (we can't spend a lot of time per item), and ability to identify how the material is being used. We also need to count transactions and include them in circulation statistics and reports.")

**Priority rationale:** Multiple branches identified uncataloged material handling as a practical need for rapid distribution and counting.

**Sources:** [DOC-010](#doc-010), [DOC-015](#doc-015). **Evidence candidates:** CAND-00097, CAND-00147.

## 5. Blacklist: discarded requirements

Duplicates are merged with all their sources; they are not discarded requirements.

### BL-0001 — Compile Executive Reports

**Category:** out_of_scope

**Original proposal:** - Compile a list of reports needed for an Executive Reports Interface.

**Reason for rejection:** This is a project deliverable / analysis task (compiling a list) rather than a software runtime obligation. If the intent is to require delivered executive templates, that should be expressed as concrete delivered-template requirements instead.

**Sources:** [DOC-017](#doc-017). **Evidence candidates:** CAND-00171.

### BL-0002 — Determine Templates

**Category:** out_of_scope

**Original proposal:** - Determine and create templates needed for all PINES libraries.

**Reason for rejection:** This is a project-authoring/operational task (creating templates for PINES) rather than a software behavior. If a shipped product obligation is intended (deliver templates), express that as a concrete requirement with the template list and fields.

**Sources:** [DOC-017](#doc-017). **Evidence candidates:** CAND-00172.

### BL-0003 — Document Reports Functionality

**Category:** out_of_scope

**Original proposal:** - Document optimal Reports functionality within a future Evergreen release and develop a list of requirements.

**Reason for rejection:** This is a project/working-group task (documenting future functionality) rather than a runtime software requirement. Project tasks belong in project-management artifacts (roadmap, work items) not in the product requirements; if a runtime capability is intended it must be specified as a concrete software requirement.

**Sources:** [DOC-017](#doc-017). **Evidence candidates:** CAND-00169.

### BL-0004 — Iterative UI Specification

**Category:** out_of_scope

**Original proposal:** She mentioned that UI and data structures would require further specification using an iterative, prototype- oriented methodology.

**Reason for rejection:** This prescribes a design process/methodology rather than a runtime software requirement. Process and design-method guidance belong in project/process documentation; if a runtime deliverable is required (for example interactive prototypes), specify those deliverables explicitly.

**Sources:** [DOC-017](#doc-017). **Evidence candidates:** CAND-00178.

### BL-0005 — Reports Testing Group

**Category:** out_of_scope

**Original proposal:** - Become the Reports testing group, through which all new Reports development would be filtered.

**Reason for rejection:** This is an organizational/governance assignment (testing-group role) rather than a software capability; it should be recorded in governance or project-plan documents, not as a runtime product requirement.

**Sources:** [DOC-017](#doc-017). **Evidence candidates:** CAND-00170.

## 6. Open questions and decisions requiring stakeholder input

### OQ-001 — How should 'shelf space' be calculated when no explicit shelf-space field exists?

Stakeholders require a shelf-space percentage metric but multiple sources note the database does not track shelf space directly. The specification permits estimation but the exact algorithm (item dimensions, per-format average linear inches, or item-count proxy) was not decided.

**Sources:** [DOC-003](#doc-003).

### OQ-002 — What scope and definitive metric(s) define 'capacity' for the capacity interface (e.g., physical shelf linear-feet, configured item limits, circulation processing capacity)?

Participants requested a system-wide capacity dashboard but asked different questions about what 'capacity' means. Implementation requires a stakeholder decision to select concrete metrics to display.

**Sources:** [DOC-002](#doc-002), [DOC-010](#doc-010).

### OQ-003 — Which archival retention policy values shall the system enforce by default (e.g., transaction retention X days, financial archival years)?

Documents reference configurable retention and an example 7-year finance retention but did not lock specific defaults; this requires policy decision for defaults and guidance for configuration.

**Sources:** [DOC-011](#doc-011), [DOC-020](#doc-020).

### OQ-004 — For auto-revert of transferred items: which event triggers or precedence rules should be supported (time-based first, event-based overrides, checked-out at destination to cancel auto-revert)?

Stakeholders asked for both time-based and event-based auto-revert behaviors, but interactions and precedence (e.g., revert after X days unless checked out at destination) were not fully specified.

**Sources:** [DOC-004](#doc-004).

### OQ-005 — Should historical reporting use a separate reporting replica with periodic snapshots, or a dedicated reporting warehouse mirroring the production schema?

Technical staff raised performance and reproducibility concerns; choice affects architecture, latency and complexity.

**Sources:** [DOC-010](#doc-010), [DOC-019](#doc-019).

## 7. Source register

Paths are relative to the input directory. Evidence line numbers refer to the normalized UTF-8 source copies in `sources/`.

<a id="doc-001"></a>
### DOC-001 — conversations/conv_pines014_material_volume.eml

Original file SHA-256: `7171c9cf4c3695773b0a63d6ddb45f8afa55885cdb5605beb11337e26e70f77f`.

<a id="doc-002"></a>
### DOC-002 — conversations/conv_pines015_capacity_interface.eml

Original file SHA-256: `5e209ce733ec1dfe55d75394cf4c9c8169291b7654dda112958ae33c6589012d`.

<a id="doc-003"></a>
### DOC-003 — conversations/conv_pines016_shelf_space.eml

Original file SHA-256: `476b2acea25db8c30aca3c399444684d0c90323294ee72d7436c16725bab9104`.

<a id="doc-004"></a>
### DOC-004 — conversations/conv_pines018_item_transfer.eml

Original file SHA-256: `42e9d374f4af35d14fb13b5d12e093ef43c260022f4cf9a7c1ff9c18927c1913`.

<a id="doc-005"></a>
### DOC-005 — conversations/conv_pines019_020_missing_intransit.eml

Original file SHA-256: `06277c9accc580f26c035d13f37f36fc4dce9224924fabdd3ba8413561e013b1`.

<a id="doc-006"></a>
### DOC-006 — conversations/conv_pines021_item_purging.eml

Original file SHA-256: `031e47dc1c52d97fb45d60f12b60a512642ba4d05a83c4f5519edec22091e5be`.

<a id="doc-007"></a>
### DOC-007 — conversations/conv_pines022_deletions.eml

Original file SHA-256: `9f00993bf51575573e6d3475138be76779582367f66283a7addf8f9b3dc2b3ba`.

<a id="doc-008"></a>
### DOC-008 — conversations/conv_pines023_patron_characteristics.eml

Original file SHA-256: `c7f96813dd0a858a8465d736479e5c7c670a89ad29064c3f93d5aba186210fd0`.

<a id="doc-009"></a>
### DOC-009 — conversations/conv_pines024_inactive_patrons.eml

Original file SHA-256: `a1c332ab4cc2919e0a4e51cc43038dff21cb662606c0f3e66cd21881a849467b`.

<a id="doc-010"></a>
### DOC-010 — early_draft_srs_galecia.txt

Original file SHA-256: `6116ff727dcfb1021f3e1480d48e694ab5ad533b5d346d5023f6ea8736fc3f03`.

<a id="doc-011"></a>
### DOC-011 — email_financial_reports.eml

Original file SHA-256: `530171325baf796d2cb860e3c1cd81b3d5c6ff3ccd200023d2bb83957cbfe50b`.

<a id="doc-012"></a>
### DOC-012 — email_report_features.eml

Original file SHA-256: `c1cbf3ee1a2bb49da58c4f901349a2edf0e1af051cdde6230f2421406ad6324f`.

<a id="doc-013"></a>
### DOC-013 — email_staff_login.eml

Original file SHA-256: `0d03f742f10e7469e03c83c36ee9dee65d62cf903d13239006b51b64b08b7f00`.

<a id="doc-014"></a>
### DOC-014 — evergreen_reference_2009.txt

Original file SHA-256: `eb115c87d4b919a0a299d4f79fdf2f644da0374942619d5d4d1658c417d96d41`.

<a id="doc-015"></a>
### DOC-015 — interview_cataloging_2009-05-08.txt

Original file SHA-256: `e4b3b19c6c61634e291712f374050f9b5f4367b93170619d31eaed46e20f52c1`.

<a id="doc-016"></a>
### DOC-016 — interview_sysadmin_2009-05-10.txt

Original file SHA-256: `fda777c641f28d4f05f287629d6b96787a3559ee12280246da9ee8345c3fecbe`.

<a id="doc-017"></a>
### DOC-017 — meeting_minutes/meeting_2009-03-15_minutes.txt

Original file SHA-256: `08cbd3ecab82e3e8e6357ffeb677f8dc608357bec50f6bcec391dfd2e481b3ae`.

<a id="doc-018"></a>
### DOC-018 — meeting_minutes/meeting_2009-07-20_minutes.txt

Original file SHA-256: `bcb7a84c633e9898921cea96a05b7ae97d341f9686fe93a6126027f1536a53e1`.

<a id="doc-019"></a>
### DOC-019 — meeting_tech_subcommittee_2009-06-30.txt

Original file SHA-256: `7fb4cc419dea729aa875e64b2ddcb1c58af5c2a1ea3ba4e80e72f654e5b32200`.

<a id="doc-020"></a>
### DOC-020 — survey_results_2009.txt

Original file SHA-256: `cc5bf9b6301b13553a1849853f7b5d3a408c9e339261c65dfa3b72e76ac09a81`.

## 8. Candidate disposition and evidence ledger

Every extracted or independently discovered candidate must have one accepted or rejected disposition. This measures candidate coverage, not guaranteed coverage of every possible interpretation of the corpus.

| Candidate | Disposition | Source and normalized lines | Literal evidence |
|---|---|---|---|
| CAND-00001 | REQ-0014 | DOC-001:96–100 | The system should provide the ability to report on the volume of material in a given library at any point in time, based on: - New acquisitions - Items on the shelf (checked in) - Items out in circulation (checked out) |
| CAND-00002 | REQ-0014 | DOC-001:102–107 | The report should allow breaking down volume in categories such as: - Total items in library - Number of holds - Number of adult fiction - Number of board books - Other customizable categories |
| CAND-00003 | REQ-0014 | DOC-001:83–84 | We can also add date filters - volume at any point in time, not just current. |
| CAND-00004 | REQ-0014 | DOC-001:59–60 | Can we make the categories customizable? Different libraries might want different breakdowns. |
| CAND-00005 | REQ-0023 | DOC-002:88–88 | The system should provide an interface showing the capacity of all branches. |
| CAND-00006 | REQ-0023 | DOC-002:90–90 | High-level overview of all branches' capacity at once |
| CAND-00007 | REQ-0023 | DOC-002:40–40 | Ability to drill down into individual branches |
| CAND-00008 | REQ-0023 | DOC-002:92–92 | Sorting and filtering capabilities (region, type, load) |
| CAND-00009 | REQ-0023 | DOC-002:93–93 | Trend data (growth/shrink patterns) |
| CAND-00010 | REQ-0019 | DOC-002:73–73 | export to CSV |
| CAND-00011 | REQ-0022 | DOC-003:105–109 | The system should provide, for each genre and format of material, the ability to compare: - The percentage of total circulations - The percentage of the collection - The percentage of total shelf space |
| CAND-00012 | REQ-0022 | DOC-003:111–111 | The report should be available per library and per system. |
| CAND-00013 | REQ-0022 | DOC-003:92–93 | Also, can we include a "comparison" view that shows each library's breakdown side by side? That would make it easy to spot outliers. |
| CAND-00014 | REQ-0022 | DOC-003:60–61 | Can we also filter by date range? Like, what was the shelf space utilization in Q1 vs. Q2? |
| CAND-00015 | REQ-0022 | DOC-003:76–77 | The tricky part is #3. Shelf space isn't directly tracked in the database. We'd need to estimate based on item dimensions or use item count as a proxy. |
| CAND-00016 | REQ-0004 | DOC-004:154–155 | The system should provide a utility for transferring batches of items between branches. |
| CAND-00017 | REQ-0004 | DOC-004:157–157 | Ability to query for candidate materials |
| CAND-00018 | REQ-0004 | DOC-004:158–158 | Ability to save queries for repeated use |
| CAND-00019 | REQ-0004 | DOC-004:159–159 | Ability to manually select titles from query results |
| CAND-00020 | REQ-0004 | DOC-004:160–160 | Ability to change records of selected items to move to new location |
| CAND-00021 | REQ-0004 | DOC-004:15–15 | Mechanisms: changing location field, generating pull lists |
| CAND-00022 | REQ-0004 | DOC-004:162–163 | Ability to revert items to original location after a set period of time and/or based on other criteria |
| CAND-00023 | REQ-0004 | DOC-004:104–104 | utility should show a preview before making changes. |
| CAND-00024 | REQ-0004 | DOC-004:108–108 | And we need an undo function! |
| CAND-00025 | REQ-0004 | DOC-004:100–101 | Not every staff member should be able to transfer items between branches. |
| CAND-00026 | REQ-0004 | DOC-004:135–135 | Can we track transfer history? |
| CAND-00027 | REQ-0004 | DOC-004:170–170 | Event-based and time-based auto-revert |
| CAND-00028 | REQ-0004 | DOC-004:89–89 | Also, can we generate transit labels? |
| CAND-00029 | REQ-0004 | DOC-004:122–123 | If an item transfer is delayed or has issues, notify me. |
| CAND-00030 | REQ-0004 | DOC-004:59–60 | Batch update of location field - straightforward database update with transaction safety. |
| CAND-00031 | REQ-0004 | DOC-004:70–70 | We should process in smaller batches to avoid locking the database. |
| CAND-00032 | REQ-0016 | DOC-005:89–89 | System provides reports of missing and damaged items per branch. |
| CAND-00033 | REQ-0016 | DOC-005:92–94 | System generates a list of items that have been in-transit for more than X days (X configurable), per branch and per system. The report merges transit-to and transit-from into one report for ease of front-line staff. |
| CAND-00034 | REQ-0016 | DOC-005:99–100 | for the in-transit report - can we sort by due date? Front-line staff need to chase the oldest items first. |
| CAND-00035 | REQ-0016 | DOC-005:56–57 | Also, can the report include item condition notes? Like "water damage" or "vandalism"? |
| CAND-00036 | REQ-0016 | DOC-005:36–37 | I need to see what's been in-transit for more than X days (X should be configurable, probably 7 days default). |
| CAND-00037 | REQ-0013 | DOC-006:10–10 | I need to identify item records to purge based on customizable criteria. |
| CAND-00038 | REQ-0013 | DOC-006:15–15 | I need a report to help convert items from one status to another in batch. |
| CAND-00039 | REQ-0013 | DOC-006:18–19 | CRITICAL: We need a "last copy report" that identifies our library system's last copies. |
| CAND-00040 | REQ-0013 | DOC-006:22–23 | We also need a quick way to delete volume entries along with copy entries, and delete records with no items attached. |
| CAND-00041 | REQ-0013 | DOC-006:55–55 | For the purging criteria - can we make them really customizable? |
| CAND-00042 | REQ-0013 | DOC-006:142–144 | - Read-only reports for identifying candidates - Separate confirmation step for actual deletions - Audit trail for all purges |
| CAND-00043 | REQ-0013 | DOC-006:102–103 | We need to track who purged what and when. This is for accountability and troubleshooting. |
| CAND-00044 | REQ-0013 | DOC-006:99–100 | Can we combine these? Like "items with status 'missing' for more than 6 months AND haven't circulated in 2 years"? |
| CAND-00045 | REQ-0013 | DOC-006:116–117 | can the purging utility be scheduled? Like, run automatically at the end of each year? |
| CAND-00046 | REQ-0007 | DOC-007:109–110 | The system should count and track record deletions (e.g., item records, patron records) per location and per system. |
| CAND-00047 | REQ-0007 | DOC-007:110–114 | Tracking should include: - Record type - Timestamp - User who performed the deletion - Location of the user |
| CAND-00048 | REQ-0007 | DOC-007:116–117 | Additionally, tracking of denied deletion attempts would be helpful for compliance and troubleshooting. |
| CAND-00049 | REQ-0007 | DOC-007:43–44 | we'd need: 1. A trigger in the database that logs deletions to an audit table |
| CAND-00050 | REQ-0007 | DOC-007:46–46 | 3. A report interface to query this audit table |
| CAND-00051 | REQ-0007 | DOC-007:48–49 | The report should show deletions per location and per system. We can aggregate by date range, by user, by record type. |
| CAND-00052 | REQ-0007 | DOC-007:74–76 | reports showing: - Total deletions per period (month, quarter, year) - Deletions by type (item vs patron vs other) |
| CAND-00053 | REQ-0017 | DOC-008:114–121 | The system should allow queries and reports to be limited or grouped by various patron characteristics, including: - Age range - Zip code - County of residence - Home branch - Patron type - Preferred language |
| CAND-00054 | REQ-0017 | DOC-008:124–124 | Both LIMIT (filter) and GROUP BY (aggregate) should be supported |
| CAND-00055 | REQ-0017 | DOC-008:125–125 | Filters can be combined with AND/OR logic |
| CAND-00056 | REQ-0017 | DOC-008:101–102 | We should include them in the report (with null values) rather than excluding them |
| CAND-00057 | REQ-0017 | DOC-008:48–48 | The age ranges need to be configurable too. Like, 0-5, 6-10, 11-15, etc. |
| CAND-00058 | REQ-0012 | DOC-009:133–135 | The system should generate a list of patrons with no circulation or electronic activity in the last X days (X configurable). Electronic activity includes OPAC login, online hold placement, online renewals. |
| CAND-00059 | REQ-0012 | DOC-009:73–79 | For the configurable X days - what ranges make sense? - 30 days (monthly check) - 90 days (quarterly check) - 180 days (semi-annual) - 365 days (annual) Can we make it fully customizable? Like any number of days? |
| CAND-00060 | REQ-0012 | DOC-009:137–141 | The list should be configurable to: - System - Home Library - County - (Other levels as needed) |
| CAND-00061 | REQ-0012 | DOC-009:144–144 | Include current mailing addresses for outreach |
| CAND-00062 | REQ-0012 | DOC-009:145–145 | Track inactive patrons with outstanding fines separately |
| CAND-00063 | REQ-0012 | DOC-009:115–120 | we should be able to EXCLUDE certain patrons from the inactive report. For example: - Patrons with "do not disturb" flags - VIP patrons - Staff members - Patrons who have opted out of communications |
| CAND-00064 | REQ-0019 | DOC-009:122–122 | the report should be exportable. We upload it to our outreach system. |
| CAND-00065 | REQ-0012 | DOC-009:104–105 | One performance note: for 3.5 million patrons, this query could be slow. We should run it as a background report and cache results. |
| CAND-00066 | REQ-0002 | DOC-010:126–127 | The system must support a library consortium with 286 locations, 17 million annual circulations, and purchasing/processing over 900,000 items per year. |
| CAND-00067 | REQ-0002 | DOC-010:128–129 | It is highly desirable that searches and reports can be processed during open hours without disrupting other system functions. |
| CAND-00068 | REQ-0002 | DOC-010:132–132 | The system must operate on a Linux or Solaris server environment. |
| CAND-00069 | REQ-0002 | DOC-010:135–136 | The system must be accessible through a web browser or a Windows-compatible client. |
| CAND-00070 | REQ-0002 | DOC-010:139–141 | If web-browser based, the system must be accessible through Microsoft Internet Explorer (version 6.0 and later) and Mozilla Firefox (version 2.0 and later). |
| CAND-00071 | REQ-0001 | DOC-010:144–146 | OE-5: The system must be accessible with screen-reading software, screen- magnification software, and other assistive technology programs designed to increase accessibility. |
| CAND-00072 | REQ-0001 | DOC-010:153–153 | The system must use a fully relational database back-end. |
| CAND-00073 | REQ-0001 | DOC-010:155–156 | The system must produce standards-compliant HTML output for web-based components. |
| CAND-00074 | REQ-0001 | DOC-010:159–160 | The system must provide a development and training environment with the ability to migrate configurations to a production environment. |
| CAND-00075 | REQ-0003 | DOC-010:163–165 | User rights and privileges will be controlled through security groups and or "roles" that allow access control for individuals, workgroups, and arbitrary staff groups. |
| CAND-00076 | REQ-0001 | DOC-010:168–169 | These requirements must not constrain functionality or features of the Online Public Access Catalog (OPAC) module. |
| CAND-00077 | REQ-0008 | DOC-010:176–179 | The developer must provide complete data specifications for authority records, bibliographic records, order records, item records, hold/request records, and other records maintained or accessed by the Management Processes. |
| CAND-00078 | REQ-0008 | DOC-010:182–185 | The developer must provide a thorough high-level description of major processes, including bibliographic record import and export, validation of bibliographic records against internal and external authority sources, and standard reports. |
| CAND-00079 | REQ-0008 | DOC-010:188–189 | The system must provide an online, hierarchical, and cross-linked help system in HTML that describes and illustrates all system functions. |
| CAND-00080 | REQ-0008 | DOC-010:192–194 | The system must provide thorough high-level error reporting and feedback, and shall allow low-level query-specific feedback for Local and Global System Administrators from the front-end interface. |
| CAND-00081 | REQ-0018 | DOC-010:250–251 | The system should provide a user-friendly interface for designing queries against all record types (bibliographic, item, patron, transaction, financial). |
| CAND-00082 | REQ-0018 | DOC-010:258–258 | Administrators should control staff access to tables and fields. |
| CAND-00083 | REQ-0021 | DOC-010:232–234 | System administrators should be able to create report templates that are available to staff. These templates should be runnable as-is or modifiable for individual needs. |
| CAND-00084 | REQ-0021 | DOC-010:243–244 | The system should provide distinct, fine-grained permission levels that limit who can create and clone reports. |
| CAND-00085 | REQ-0005 | DOC-010:261–262 | The system should provide pre-defined reports for consumption by library boards and other external consumers. |
| CAND-00086 | REQ-0005 | DOC-010:262–263 | These should include basic statistics like those required by the Georgia Annual Report and Application for State Aid. |
| CAND-00087 | REQ-0024 | DOC-010:265–266 | Activity reports should indicate traffic and volume of use, displaying statistics on check-outs, check-ins, holds placed, and holds filled. |
| CAND-00088 | REQ-0024 | DOC-010:266–269 | It should be possible to cross-tabulate per terminal, per branch, per library system, per hour, per patron age range, per patron type, and per patron location. |
| CAND-00089 | REQ-0024 | DOC-010:272–273 | Transactions should be archived in a form that protects patron privacy as defined by State Law, while providing useful demographic statistics. |
| CAND-00090 | REQ-0005 | DOC-010:298–299 | The system must be able to support the reporting definitions as described in the attached report examples (see Appendix A). |
| CAND-00091 | REQ-0018 | DOC-010:302–303 | The system must be able to support the fine-grained reports requirements as described in the attached specification (see Appendix B). |
| CAND-00092 | REQ-0024 | DOC-010:310–311 | The system should produce statistics that can be used to understand and predict patron behavior and use of materials. |
| CAND-00093 | REQ-0017 | DOC-010:317–318 | The system should produce useful demographic statistics, including transactions by geographical regions, age ranges, etc. |
| CAND-00094 | REQ-0014 | DOC-010:327–329 | Ability to report on the volume of material in a given library at any point in time, based on new acquisitions, items on the shelf, and items out in circulation. |
| CAND-00095 | REQ-0023 | DOC-010:334–334 | The system should provide an interface showing the capacity of all branches. |
| CAND-00096 | REQ-0022 | DOC-010:337–340 | For each genre and format of material, ability to compare: - The percentage of total circulations - The percentage of the collection - The percentage of total shelf space |
| CAND-00097 | REQ-0025 | DOC-010:345–346 | Ability to control inventory of uncataloged material, such as paperback books and children's board books. |
| CAND-00098 | REQ-0004 | DOC-010:355–356 | System should provide a utility for transferring batches of items between branches. |
| CAND-00099 | REQ-0016 | DOC-010:368–368 | The system should provide reports of missing and damaged items per branch. |
| CAND-00100 | REQ-0016 | DOC-010:371–372 | The system should generate a list of items that have been in-transit for more than X days (X configurable), per branch and per system. |
| CAND-00101 | REQ-0013 | DOC-010:377–378 | The system should provide a utility and reports for identifying item records to purge, based on customizable criteria such as: |
| CAND-00102 | REQ-0007 | DOC-010:390–391 | Ability to count and track record deletions (e.g., item records, patron records) per location and per system. |
| CAND-00103 | REQ-0012 | DOC-010:408–409 | The system should generate a list of patrons with no circulation or electronic activity in the last X days (X configurable). |
| CAND-00104 | REQ-0024 | DOC-010:417–417 | Transaction history is maintained for X days (X is configurable). |
| CAND-00105 | REQ-0024 | DOC-010:421–421 | Transactions can be grouped by hour, terminal, branch, and system. |
| CAND-00106 | REQ-0024 | DOC-010:426–426 | The system counts all types of check-in individually and cumulatively: |
| CAND-00107 | REQ-0024 | DOC-010:432–432 | The system counts all types of check-out individually and cumulatively: |
| CAND-00108 | REQ-0024 | DOC-010:441–441 | The system counts all hold requests, including how the hold was placed: |
| CAND-00109 | REQ-0024 | DOC-010:447–449 | The system can generate a report of transactions (holds placed, holds filled, and check-outs) per patron, per library, per selected group of libraries, per system, per county. |
| CAND-00110 | REQ-0009 | DOC-010:458–459 | The system can generate a report of the value of items (based on data in item record) in the entire collection or a portion. |
| CAND-00111 | REQ-0009 | DOC-010:464–465 | All reports and data archiving must comply with standard accounting practice and state, county, and municipal auditing requirements. |
| CAND-00112 | REQ-0009 | DOC-010:468–469 | Fines, charges, waivers, and ecommerce transactions are attached to patron and item records. |
| CAND-00113 | REQ-0009 | DOC-010:475–475 | - patron account balances by patron, home library, and system |
| CAND-00114 | REQ-0006 | DOC-010:538–540 | - Bib Records Added by user by library Count - Bib Records with No Volumes attached - Bib Records missing specific MARC fields |
| CAND-00115 | REQ-0017 | DOC-010:542–559 | PATRONS REPORTS: - Patron Count - Patron Added Count by Month - New Patron Count (patrons added the previous month by Demographic Category) - Patron Count by Age Demographic - Patron Count by County - Patron Count by County, City, and Zip Code - Patron Count by Home Library - Patron Count by Profile Group - Patron Count by survey answer - List of patrons by survey answer - Voter Survey Responses County by Week - List of Patrons by Expiration Date - Voter Reg Survey Responses Count by Week - List of patrons who are BARRED - List of Patrons with inactive status - List of Staff Accounts with date of last password change and account expiration - List of Patrons with specific wording in notes |
| CAND-00116 | REQ-0024 | DOC-010:561–571 | HOLDS REPORTS: - Holds Purchase Alert - Items Sent for Holds - Items Received for Holds - IntraPINES Loans for all Systems - IntraPINES Loans for all Facilities - IntraPINES Loans by System - IntraPINES Loans by Facility - Unfilled Holds - Annual # of holds placed - Stale Holds (holds sitting on hold shelf waiting for pickup for too long) |
| CAND-00117 | REQ-0005 | DOC-010:605–608 | Canned reports are generic reports set to run by the individual either ASAP or recurring. There should be a certain set of templates that are pre-written and delivered with the product. Will have the ability for it to run by yesterday's data, last week's, last month's, or last year's. |
| CAND-00118 | REQ-0005 | DOC-010:612–613 | On Demand Reports would be for pre-selected criteria but for things like maintenance reports or collections development and would be set to run on demand. |
| CAND-00119 | REQ-0018 | DOC-010:616–618 | Open template would have all attributes associated with say circulation, patrons, items, bills, and bibs to select from for filtering and the same attributes for displaying. |
| CAND-00120 | REQ-0005 | DOC-010:620–625 | 15.5 Quick Access Interface - Ability to hover over each title of canned report/template with pop-up box with description - Check off any part of data you want - Ability to select Run ASAP, Hourly, Daily, Weekly, Monthly, Yearly - Output would be in Excel, HTML, and CSV format |
| CAND-00121 | REQ-0010 | DOC-010:656–657 | Ability to have historical reporting - a reporting warehouse such that data can be acquired on a given date or date range |
| CAND-00122 | REQ-0010 | DOC-010:655–655 | Ability to have real time reporting |
| CAND-00123 | REQ-0015 | DOC-010:659–660 | Report results would include the date selection criteria at the top or bottom to quickly see date range selected along with the name of the report |
| CAND-00124 | REQ-0009 | DOC-011:14–16 | Value of items report - staff should be able to get the value of items based on data in item records. This could be the entire collection, or a portion. For example, they want to be able to get: |
| CAND-00125 | REQ-0009 | DOC-011:21–26 | Financial reports - staff need reports on: - Patron account balances by patron, home library, and system - Fines and charges accrued per time period (last 12 months, YTD, last month) - Fines waived per time period and per branch - Payments made per time period and per payment method (staff desk, self-check, OPAC) |
| CAND-00126 | REQ-0009 | DOC-011:28–29 | Audit trail - system must maintain a ledger of patron payments, including which charges payments are applied to, to facilitate reconciliation. |
| CAND-00127 | REQ-0009 | DOC-011:31–32 | Compliance - all reports and data archiving must comply with standard accounting practice and state, county, and municipal auditing requirements. |
| CAND-00128 | REQ-0009 | DOC-011:73–75 | - For fines and charges, the staff should be able to query patron accounts with balances greater than X dollars. This is useful for identifying accounts that need attention. |
| CAND-00129 | REQ-0009 | DOC-011:95–96 | Financial information needs to be easily updatable. When a patron makes a payment at the front desk, we need the system to reflect that immediately. |
| CAND-00130 | REQ-0009 | DOC-011:98–99 | Payments tracking by library is important for our end-of-month reports. Each branch needs to be able to see what payments were collected at their location. |
| CAND-00131 | REQ-0009 | DOC-011:56–57 | we need to ensure that data archiving follows state and local requirements. Some data needs to be retained for 7 years for audit purposes. |
| CAND-00132 | REQ-0018 | DOC-012:11–14 | We need a user-friendly interface for designing queries against all record types. Staff should be able to select fields to query, select values from picklists, use regular expressions from a dropdown, and use Boolean operators. |
| CAND-00133 | REQ-0021 | DOC-012:16–19 | Admins need to create report templates that are available to staff. Templates should be runnable as-is or modified. Changes shouldn't compromise results. Admins should be able to limit which filters and display fields can be altered. |
| CAND-00134 | REQ-0021 | DOC-012:25–26 | We need distinct, fine-grained permission levels limiting who can create and clone reports. |
| CAND-00135 | REQ-0005 | DOC-012:30–32 | Pre-defined reports for library boards with basic statistics (Georgia Annual Report requirements). Activity reports showing traffic and volume of use - checkouts, check-ins, holds placed, holds filled. |
| CAND-00136 | REQ-0024 | DOC-012:36–37 | Transactions archived protecting patron privacy per State Law, while providing useful demographic statistics. |
| CAND-00137 | REQ-0015 | DOC-012:39–39 | System provides query selections along with results. |
| CAND-00138 | REQ-0020 | DOC-012:41–41 | Ability to see where your report is in the queue. |
| CAND-00139 | REQ-0020 | DOC-012:124–124 | Important reports can jump queue. |
| CAND-00140 | REQ-0003 | DOC-013:90–91 | 1. System supports (but does not require) streamlined staff login methods, e.g. card swipe or individual login/password. |
| CAND-00141 | REQ-0003 | DOC-013:43–44 | we need individual authentication. The system must track WHICH staff member is logged in for audit purposes. |
| CAND-00142 | REQ-0003 | DOC-013:92–92 | User rights and privileges controlled through security groups/roles. |
| CAND-00143 | REQ-0003 | DOC-013:66–67 | access control for individuals, workgroups, and arbitrary staff groups. |
| CAND-00144 | REQ-0003 | DOC-013:94–94 | Easy administration of roles and permissions. |
| CAND-00145 | REQ-0018 | DOC-014:29–30 | Evergreen includes a report writer that allows staff to create custom reports using a web-based interface. |
| CAND-00146 | REQ-0019 | DOC-014:34–34 | Multiple output formats (CSV, HTML, sometimes Excel) |
| CAND-00147 | REQ-0025 | DOC-015:31–32 | We need to be able to track these as inventory even though they're not fully cataloged. |
| CAND-00148 | REQ-0004 | DOC-015:44–55 | The utility needs several capabilities: First, we need to query for candidate materials. Maybe we want all items in the children's section that haven't circulated in 6 months. Second, we need to save these queries for repeated use - we do this monthly. Third, we need to manually select titles from query results if we want to be more targeted. Fourth, we need to change records of selected items to move them to a new location. And there should be mechanisms for reverting items back to their original location after a set period of time - like when a mobile library returns to base. |
| CAND-00149 | REQ-0016 | DOC-015:59–60 | I need a report that shows all missing and damaged items per branch. |
| CAND-00150 | REQ-0016 | DOC-015:65–67 | The report should show items that have been in-transit for more than X days (configurable), per branch and per system. |
| CAND-00151 | REQ-0013 | DOC-015:72–75 | I need to identify items for purging based on customizable criteria. For example: - Item has been in status "missing" for more than X months - Item has status "discard/weed" |
| CAND-00152 | REQ-0013 | DOC-015:77–77 | We also need a report to assist in converting items from one status to another. |
| CAND-00153 | REQ-0013 | DOC-015:80–80 | the last copy report is CRITICAL. |
| CAND-00154 | REQ-0013 | DOC-015:85–86 | There also needs to be a quick, effective method for deleting volume entries along with copy entries, as well as records with no items attached. |
| CAND-00155 | REQ-0007 | DOC-015:91–92 | Yes, we need to count and track record deletions per location and per system. |
| CAND-00156 | REQ-0022 | DOC-015:100–104 | The shelf space report is important for collection management. For each genre and format, I need to compare: - Percentage of total circulations - Percentage of the collection - Percentage of total shelf space |
| CAND-00157 | REQ-0014 | DOC-015:107–107 | The material volume report helps me understand how much we have. |
| CAND-00158 | REQ-0006 | DOC-015:112–113 | Data quality reports - items with invalid item type, items with long call numbers, bibliographic records with no item records. |
| CAND-00159 | REQ-0006 | DOC-015:116–117 | I need to be able to see the last edit date on reports, but it should be only when the item is edited and not include the last circulation. |
| CAND-00160 | REQ-0002 | DOC-016:34–35 | So any reporting system needs to work on both Linux and Solaris. |
| CAND-00161 | REQ-0020 | DOC-016:40–41 | We need to make sure reports can be queued and processed in the background. |
| CAND-00162 | REQ-0002 | DOC-016:52–52 | So we need to support IE 6.0+ and Firefox 2.0+. |
| CAND-00163 | REQ-0001 | DOC-016:56–57 | As a public institution, we MUST comply with Section 508 accessibility requirements. |
| CAND-00164 | REQ-0002 | DOC-016:69–70 | The reporting system needs to work with the relational structure, not fight against it. |
| CAND-00165 | REQ-0003 | DOC-016:82–83 | The permission system needs to be controlled through security groups and/or "roles." |
| CAND-00166 | REQ-0001 | DOC-016:90–91 | Developers need a place to test new reports without affecting production. |
| CAND-00167 | REQ-0002 | DOC-016:101–102 | The management reporting system must not constrain the OPAC in any way. |
| CAND-00168 | REQ-0008 | DOC-016:108–108 | The HTML help needs to be searchable and easy to navigate. |
| CAND-00169 | BL-0003 | DOC-017:41–42 | - Document optimal Reports functionality within a future Evergreen release and develop a list of requirements. |
| CAND-00170 | BL-0005 | DOC-017:43–44 | - Become the Reports testing group, through which all new Reports development would be filtered. |
| CAND-00171 | BL-0001 | DOC-017:45–45 | - Compile a list of reports needed for an Executive Reports Interface. |
| CAND-00172 | BL-0002 | DOC-017:46–46 | - Determine and create templates needed for all PINES libraries. |
| CAND-00173 | REQ-0014 | DOC-017:59–59 | - Analyzing the Library collection and its use by patrons |
| CAND-00174 | REQ-0023 | DOC-017:60–60 | - Analyzing branch capacity and optimal distribution of the collection |
| CAND-00175 | REQ-0017 | DOC-017:61–61 | - Analyzing demographics and interests of patrons |
| CAND-00176 | REQ-0024 | DOC-017:62–62 | - Analyzing staff productivity and workflow |
| CAND-00177 | REQ-0009 | DOC-017:63–63 | - Tracking and verifying financial transactions |
| CAND-00178 | BL-0004 | DOC-017:73–75 | She mentioned that UI and data structures would require further specification using an iterative, prototype- oriented methodology. |
| CAND-00179 | REQ-0023 | DOC-018:37–37 | Need for cross-branch comparison reports |
| CAND-00180 | REQ-0005 | DOC-018:42–42 | Board/executive reports need to be pre-defined |
| CAND-00181 | REQ-0006 | DOC-018:43–43 | Data quality reports are needed |
| CAND-00182 | REQ-0016 | DOC-018:47–47 | In-transit item reports are critical for delivery coordination |
| CAND-00183 | REQ-0016 | DOC-018:48–48 | Missing/damaged item reports are needed per branch |
| CAND-00184 | REQ-0006 | DOC-018:51–51 | Weeding reports are frequently used |
| CAND-00185 | REQ-0022 | DOC-018:52–52 | Shelf space utilization reports are important |
| CAND-00186 | REQ-0017 | DOC-018:53–53 | Demographic analysis for program planning |
| CAND-00187 | REQ-0002 | DOC-018:78–78 | Management Processes shall operate on a Linux or Solaris server. |
| CAND-00188 | REQ-0002 | DOC-018:82–83 | Management Processes shall be accessible through a web-browser or a Windows-compatible client. |
| CAND-00189 | REQ-0002 | DOC-018:88–90 | Management Processes shall be accessible through Microsoft Internet Explorer (v.6.0 and later) and Mozilla Firefox (v.2.0 and later). |
| CAND-00190 | REQ-0001 | DOC-018:95–97 | Management Processes shall be accessible with screen-reading software, screen-magnification software, and other software programs designed to increase accessibility. |
| CAND-00191 | REQ-0001 | DOC-018:106–106 | Management Processes shall use a fully relational database back-end. |
| CAND-00192 | REQ-0001 | DOC-018:110–110 | Management Processes shall produce standards-compliant HTML. |
| CAND-00193 | REQ-0001 | DOC-018:114–115 | Management Processes shall provide a development and training environment with the ability to migrate configurations to a production environment. |
| CAND-00194 | REQ-0001 | DOC-018:120–122 | User rights and privileges will be controlled through security groups and/or "roles" that allow access control for individuals, workgroups, and arbitrary staff groups. |
| CAND-00195 | REQ-0008 | DOC-018:136–139 | The software developer shall provide complete data specifications for authority records, bibliographic records, order records, item records, hold/request records, and other records maintained or accessed by Management Processes. |
| CAND-00196 | REQ-0008 | DOC-018:144–147 | The software developer shall provide a thorough high-level description of major processes, including bibliographic record import and export, validation of bibliographic records against internal and external authority sources, and standard reports. |
| CAND-00197 | REQ-0008 | DOC-018:152–153 | The system shall provide an online, hierarchical, and cross-linked help system in HTML that describes and illustrates all system functions. |
| CAND-00198 | REQ-0008 | DOC-018:158–160 | The system shall provide thorough high-level error reporting and feedback and shall allow low-level query-specific feedback for Local and Global System Administrators from the front-end interface. |
| CAND-00199 | REQ-0002 | DOC-018:172–173 | Management Processes are consolidated at a central location, and accept input and provide services to multiple locations. |
| CAND-00200 | REQ-0008 | DOC-018:183–185 | Management Processes interface with a variety of vendor websites, via published APIs and/or automated transfer of standard-format data files (e.g., USMARC21, EDIFACT). |
| CAND-00201 | REQ-0001 | DOC-019:31–31 | Robert confirmed that the system must use a fully relational database back-end. |
| CAND-00202 | REQ-0001 | DOC-019:42–42 | The system must produce standards-compliant HTML. |
| CAND-00203 | REQ-0001 | DOC-019:54–55 | "What we need is a way to migrate configurations between them. Export/import of templates, permission settings, and saved queries." |
| CAND-00204 | REQ-0003 | DOC-019:64–65 | The system should make it easy to change someone's permissions by simply changing their role assignment. |
| CAND-00205 | REQ-0002 | DOC-019:75–75 | We absolutely cannot constrain the OPAC |
| CAND-00206 | REQ-0008 | DOC-019:84–90 | The developer must provide complete data specifications for: - Authority records - Bibliographic records - Order records - Item records - Hold/request records - Other records maintained or accessed by Management Processes |
| CAND-00207 | REQ-0008 | DOC-019:96–96 | The developer must provide a thorough high-level description of major processes |
| CAND-00208 | REQ-0008 | DOC-019:104–105 | The system shall provide an online, hierarchical, and cross-linked help system in HTML. |
| CAND-00209 | REQ-0008 | DOC-019:111–112 | The system shall provide thorough high-level error reporting and feedback, and shall allow low-level query-specific feedback for administrators. |
| CAND-00210 | REQ-0019 | DOC-019:163–163 | Excel, HTML, and CSV formats are required. |
| CAND-00211 | REQ-0010 | DOC-019:168–168 | "Some reports need to be real-time - like 'what's overdue today,'" |
| CAND-00212 | REQ-0020 | DOC-019:173–173 | The ability to cancel a scheduled or running report is technically feasible |
| CAND-00213 | REQ-0019 | DOC-019:178–178 | All nulls and blank fields must be included in the results |
| CAND-00214 | REQ-0015 | DOC-019:183–184 | The ability to filter by survey name rather than survey ID requires the system to resolve names to IDs internally. |
| CAND-00215 | REQ-0024 | DOC-020:109–110 | Transaction history maintained for X days (configurable), with monthly and annual aggregates retained indefinitely. |
| CAND-00216 | REQ-0024 | DOC-020:34–34 | Transactions can be grouped by hour, terminal, branch, and system. |
| CAND-00217 | REQ-0024 | DOC-020:114–115 | All types of check-in counted individually and cumulatively: book-drop, terminal, by user or self-service. |
| CAND-00218 | REQ-0024 | DOC-020:117–119 | All types of check-out counted individually and cumulatively: staff checkout, self checkout, staff renewal, self checkout renewal, online renewal, OPAC renewal. |
| CAND-00219 | REQ-0024 | DOC-020:121–122 | Holds counted with method of placement: at staff desk, public computer, or remotely. |
| CAND-00220 | REQ-0024 | DOC-020:124–125 | Transactions report can show holds placed, holds filled, and check-outs per patron, per library, per group of libraries, per system, per county. |
| CAND-00221 | REQ-0017 | DOC-020:127–128 | Demographic statistics include transactions by geographical regions and age ranges. Data must be anonymized. |
| CAND-00222 | REQ-0017 | DOC-020:130–131 | System produces statistics to understand/predict patron behavior and use of materials. |
| CAND-00223 | REQ-0021 | DOC-020:133–133 | Report templates can be created by administrators and run as-is or modified. |
| CAND-00224 | REQ-0021 | DOC-020:135–135 | Fine-grained permissions limit who can create and clone reports. |
| CAND-00225 | REQ-0021 | DOC-020:137–137 | Shared folders to allow/disallow staff from running specific reports. |
| CAND-00226 | REQ-0020 | DOC-020:139–139 | Ability to see where your report is in the queue. |
| CAND-00227 | REQ-0023 | DOC-002:41–42 | Maybe color-coding - green for under capacity, yellow for getting full, red for at/over capacity |
| CAND-00228 | REQ-0018 | DOC-004:33–34 | We do this monthly - move all items in genre X that haven't circulated in 6 months. |
| CAND-00229 | REQ-0004 | DOC-004:64–65 | Auto-revert mechanism - a scheduled task that checks transferred items and reverts them based on time or status criteria. |
| CAND-00230 | REQ-0016 | DOC-005:19–22 | We use the data for two purposes: 1. Auditing - showing how many items went missing/were damaged 2. Collection decisions - if we keep losing the same titles, maybe we need different copies or to move them to a different location |
| CAND-00231 | REQ-0016 | DOC-005:67–69 | The system currently tracks item status as "missing" or "long overdue" or various other statuses. We can query for items with status "missing" or "lost" and group by branch. |
| CAND-00232 | REQ-0016 | DOC-005:71–72 | For in-transit items, we need to check the transit table for items where the arrival date is null and the departure date is more than X days ago. |
| CAND-00233 | REQ-0013 | DOC-006:85–85 | Should it be automated or manual? |
| CAND-00234 | REQ-0007 | DOC-007:28–28 | - Possibly why (status before deletion?) |
| CAND-00235 | REQ-0017 | DOC-008:94–95 | The "age range" is calculated from the birth_date field, which means we need to compute it at query time. We can create age brackets in the query. |
| CAND-00236 | REQ-0012 | DOC-009:99–99 | These are stored in different tables, so we'd need a combined query. |
| CAND-00237 | REQ-0008 | DOC-010:211–213 | DE-2: Management Processes interface with a variety of vendor websites, via published APIs and/or automated transfer of standard-format data files (e.g., USMARC21, EDIFACT). |
| CAND-00238 | REQ-0002 | DOC-010:126–127 | OE-1: The system must support a library consortium with 286 locations, 17 million annual circulations, and purchasing/processing over 900,000 items per year. |
| CAND-00239 | REQ-0009 | DOC-011:70–71 | The financial data is attached to patron records AND item records. So when we query for financial reports, we need to be able to join these data sources. |
| CAND-00240 | REQ-0009 | DOC-011:77–78 | The financial reports need to show payments by method - cash, credit card, check, etc. This helps with daily reconciliation. |
| CAND-00241 | REQ-0003 | DOC-012:60–62 | If I change someone from "Staff" to "Manager," their report permissions should update automatically based on the role. |
| CAND-00242 | REQ-0003 | DOC-013:69–72 | At Piedmont, we have several different types of staff: - Front desk staff (can run basic reports, limited filters) - Department heads (can create and modify templates) - System administrators (full access to all reports and permissions) |
| CAND-00243 | REQ-0018 | DOC-014:32–32 | - Drag-and-drop field selection |
| CAND-00244 | REQ-0024 | DOC-014:136–136 | - Circulation Count by Circ Modifier (partially available) |
| CAND-00245 | REQ-0024 | DOC-014:137–137 | - Circulation Count by Dewey (not available) |
| CAND-00246 | REQ-0018 | DOC-014:138–138 | - Circulation Count by MARC fields (not available) |
| CAND-00247 | REQ-0016 | DOC-014:58–58 | - List of Items with Missing Status |
| CAND-00248 | REQ-0006 | DOC-014:141–141 | - Items Edited Count (not available) |
| CAND-00249 | REQ-0009 | DOC-014:142–142 | - List of Items by Fines Stopped Reason (not available) |
| CAND-00250 | REQ-0024 | DOC-014:143–143 | - Items more than XX days overdue with patron contact info (not available) |
| CAND-00251 | REQ-0006 | DOC-014:144–144 | - List of Items with specific Total Use Count (not available) |
| CAND-00252 | REQ-0006 | DOC-014:146–146 | - List of Items by Creation Date Range (not available) |
| CAND-00253 | REQ-0024 | DOC-014:147–147 | - Claims Returned report (not available) |
| CAND-00254 | REQ-0006 | DOC-014:149–149 | - Age of collection by call number (not available) |
| CAND-00255 | REQ-0009 | DOC-014:150–150 | - Price value of collection by call number (not available) |
| CAND-00256 | REQ-0006 | DOC-014:151–151 | - Bib Records Edited Count (not available) |
| CAND-00257 | REQ-0006 | DOC-014:152–152 | - Bib Records Added by user by library Count (not available) |
| CAND-00258 | REQ-0015 | DOC-014:157–157 | - Voter Survey Responses (not available) |
| CAND-00259 | REQ-0012 | DOC-014:158–158 | - List of Patrons with inactive status (not available) |
| CAND-00260 | REQ-0003 | DOC-014:159–159 | - Staff Accounts with date of last password change (not available) |
| CAND-00261 | REQ-0011 | DOC-014:160–160 | - Holds Purchase Alert (not available) |
| CAND-00262 | REQ-0024 | DOC-014:161–161 | - Unfilled Holds (not available) |
| CAND-00263 | REQ-0024 | DOC-014:162–162 | - Stale Holds (not available) |
| CAND-00264 | REQ-0009 | DOC-014:163–163 | - Aged Debt detailed report (partially available, needs enhancement) |
| CAND-00265 | REQ-0002 | DOC-016:31–32 | Our main server is a Red Hat Enterprise Linux 5 box with dual quad-core processors and 32GB of RAM. |
| CAND-00266 | REQ-0002 | DOC-016:32–32 | It runs PostgreSQL 8.3 for the database. |
| CAND-00267 | REQ-0002 | DOC-016:32–34 | We also have a secondary site that runs Solaris 10 on SPARC hardware for disaster recovery and reporting. |
| CAND-00268 | REQ-0001 | DOC-016:57–64 | The system needs to work with: - Screen readers like JAWS and NVDA - Screen magnification software like ZoomText - Other assistive technology programs We can't have blind staff members unable to run reports. The HTML output needs to be properly structured with alt tags, ARIA labels, and proper semantic HTML. And the system needs to produce standards-compliant HTML. |
| CAND-00269 | REQ-0003 | DOC-016:77–77 | Patron (public access through OPAC) |
| CAND-00270 | REQ-0002 | DOC-018:167–170 | AS-1: Management Processes are part of an enterprise-level Library Automation System. [Discussion: This means we can rely on the infrastructure being enterprise-grade. Evergreen is that system for PINES.] |
| CAND-00271 | REQ-0008 | DOC-018:177–181 | DE-1: Management Processes rely on the data structures and functionality of an enterprise-level Library Automation System, including Acquisitions and Cataloging modules. [Discussion: The data we report on comes from the ILS. We don't manage acquisitions or cataloging ourselves.] |
| CAND-00272 | REQ-0002 | DOC-019:36–39 | "I strongly recommend against denormalization for reporting," Robert said. "Maintaining sync between a reporting warehouse and the live database creates more problems than it solves. Modern SQL databases can handle complex analytical queries if they're written properly." |
| CAND-00273 | REQ-0008 | DOC-019:144–150 | DE-2: Management Processes interface with a variety of vendor websites, via published APIs and/or automated transfer of standard-format data files (e.g., USMARC21, EDIFACT). "We have some vendors that provide EDI ordering data," Robert explained. "The reporting system needs to handle this data, but we can't rely on it being present at every library." |
| CAND-00274 | REQ-0010 | DOC-020:101–101 | "Need a snapshot bills report going back in time" |
| CAND-00275 | REQ-0024 | DOC-020:103–103 | "Checkin date/time should not include renewals" |
| CAND-00276 | REQ-0023 | DOC-002:51–55 | From a technical standpoint, this is doable. The data is centralized in our database, so we can build queries that aggregate across all branches. One consideration: with 286 locations, the overview might get crowded. Maybe we should group by system/region? Or allow filtering? |
| CAND-00277 | REQ-0023 | DOC-002:8–10 | As a branch manager, I need to see the capacity of all branches in our system, not just my own. When we're deciding where to move items or allocate resources, it helps to see the big picture. |
| CAND-00278 | REQ-0012 | DOC-009:27–28 | At the system level, I can see which branches have the most inactive patrons. |
| CAND-00279 | REQ-0012 | DOC-009:29–29 | At the home library level, I can assign cleanup tasks to specific branches. |
| CAND-00280 | REQ-0021 | DOC-010:238–240 | For example, front-line staff could set a call number range for a weeding report or add/remove display fields from a pick list, but they should not be able to alter the template to display deleted items. |
| CAND-00281 | REQ-0003 | DOC-013:16–17 | 2. It leads to security issues - staff get in a hurry and sometimes share passwords or leave terminals logged in. |
| CAND-00282 | REQ-0003 | DOC-013:20–21 | The staff member simply swipes their employee ID badge and is logged in immediately. This is much faster and more secure. |
| CAND-00283 | REQ-0002 | DOC-014:21–22 | PINES currently operates Evergreen across 286 library locations, serving approximately 3.5 million patrons with a collection of 9.6 million items. |
| CAND-00284 | REQ-0002 | DOC-014:14–15 | The current version in production at PINES is 1.4.0.4. |
| CAND-00285 | REQ-0005 | DOC-014:48–48 | - Checkout Count |
| CAND-00286 | REQ-0005 | DOC-014:49–49 | - Renewals Count |
| CAND-00287 | REQ-0005 | DOC-014:50–50 | - Non-Cataloged Count |
| CAND-00288 | REQ-0005 | DOC-014:51–51 | - Circulation Count by Shelving Location |
| CAND-00289 | REQ-0005 | DOC-014:54–54 | - Items Added Count |
| CAND-00290 | REQ-0005 | DOC-014:55–55 | - Items Deleted Count |
| CAND-00291 | REQ-0005 | DOC-014:56–56 | - Items Currently Checked Out |
| CAND-00292 | REQ-0005 | DOC-014:57–57 | - Items Overdue by X Days |
| CAND-00293 | REQ-0005 | DOC-014:61–61 | - Bib Records Count |
| CAND-00294 | REQ-0005 | DOC-014:62–62 | - Bib Records with No Volumes Attached |
| CAND-00295 | REQ-0005 | DOC-014:65–65 | - Patron Count |
| CAND-00296 | REQ-0005 | DOC-014:66–66 | - Patron Count by Home Library |
| CAND-00297 | REQ-0005 | DOC-014:69–69 | - Bills Currently Owed by Patrons |
| CAND-00298 | REQ-0005 | DOC-014:70–70 | - Detailed Payments Received |
| CAND-00299 | REQ-0020 | DOC-014:78–78 | - No ability to check multiple reports to run at the same time |
| CAND-00300 | REQ-0003 | DOC-018:46–46 | Staff login needs (card swipe) - already discussed via email |
| CAND-00301 | REQ-0002 | DOC-018:66–69 | OE-1: Management Processes must support the needs of a large, multiple-system library consortium. Specifically, the system must support a library consortium with 286 locations, 17 million annual circulations, purchasing and processing over 900,000 items per year. |
| CAND-00302 | REQ-0001 | DOC-018:98–100 | [Discussion: Susan emphasized this is a legal requirement for public institutions. We need to support JAWS, NVDA, ZoomText, and other assistive technologies. Section 508 compliance is mandatory.] |
| CAND-00303 | REQ-0002 | DOC-018:126–127 | CO-5: These requirements shall not constrain functionality or features of the Online Public Access Catalog (OPAC) module. |
| CAND-00304 | REQ-0002 | DOC-019:124–125 | Robert: "This means we can rely on the infrastructure - redundant servers, backup systems, network connectivity." |
| CAND-00305 | REQ-0024 | DOC-020:35–36 | Transactions include check-ins, check-outs, fines collected, patron registrations, etc. |
| CAND-00306 | REQ-0024 | DOC-010:648–648 | Ability to run reports for pre-overdue, overdue, and holds notices sent |
| CAND-00307 | REQ-0002 | DOC-010:126–127 | OE-1: The system must support a library consortium with 286 locations, 17 million annual circulations, and purchasing/processing over 900,000 items per year. |
| CAND-00308 | REQ-0001 | DOC-016:56–64 | ROBERTY: This is non-negotiable. As a public institution, we MUST comply with Section 508 accessibility requirements. The system needs to work with: - Screen readers like JAWS and NVDA - Screen magnification software like ZoomText - Other assistive technology programs We can't have blind staff members unable to run reports. The HTML output needs to be properly structured with alt tags, ARIA labels, and proper semantic HTML. And the system needs to produce standards-compliant HTML. |

## 9. Review status and known limitations

Final automatic review: **REVIEW PASSED**. Independent coverage audits compared every original source document with the draft. A separate traceability agent checks every assigned candidate against the meaning of its source and assigned paragraph. Revision rounds review the whole specification and grounded candidate ledger; full source rescans are optional.

- **WARNING / description:** Shelf-space calculation method is ambiguous; the spec permits estimation but lacks an agreed algorithm (matches CAND-00015). Suggested action: Require explicit estimation algorithm for shelf-space (dimensions, proxies, or alternative) and document methodology.
- **WARNING / terminology:** Capacity metrics definition is ambiguous (which physical or system capacity metrics to display). It is referenced by CAND-00067 and CAND-00008 lacking a single definition. Suggested action: Define a single, concrete set of capacity metrics (e.g., shelf space, item-count thresholds, load factors) and align all capacity-related candidates.
- **WARNING / terminology:** Default archival retention policy values are not specified (CAND-00131 and CAND-00215 are open questions about policy defaults). Suggested action: Decide and document default retention periods (e.g., 7 years for financial/audit data) and provide guidance for configuration.

Semantic deduplication, conflict resolution and interpretation use LLM judgment and may still require human review. Historical product descriptions and stakeholder statements are treated as corpus evidence, not verified present-day facts.
