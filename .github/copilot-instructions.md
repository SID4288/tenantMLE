# Copilot Instructions

## Project

This is a Django REST Framework multi-tenant learning platform.

The project demonstrates:

* Multi-tenancy
* Role-based access control
* Tenant data isolation
* Tenant trial/expiration lifecycle
* Course management
* Course assignments
* Learning progress

The highest-priority concerns are:

1. Multi-tenancy
2. Authorization
3. Data isolation
4. Backend quality
5. Tenant lifecycle
6. Testing
7. System design

Security and tenant isolation must never be weakened to simplify implementation or make tests pass.

---

## Tech Stack

* Python
* Django
* Django REST Framework
* JWT authentication
* Django ORM
* PostgreSQL
* Docker
* Django REST Framework tests

PostgreSQL is the intended application database and will run in Docker for local development.

---

## Infrastructure

* PostgreSQL should run through Docker for local development.
* Database configuration should use environment variables rather than hardcoded credentials.
* Do not introduce SQLite-specific behavior unless explicitly required for testing.
* Database-related code should be compatible with PostgreSQL.
* Keep infrastructure changes separate from unrelated application changes.
* Do not introduce unnecessary infrastructure or dependencies.

---

## Project Structure

* `accounts/` — users, roles, authentication, permissions
* `tenants/` — tenant model and lifecycle
* `courses/` — courses and course permissions
* `learning/` — course assignments and learning progress
* `config/` — Django project configuration

---

## Roles

The system has five roles:

* `SUPER_ADMIN` — platform-level administrator
* `ADMIN` — platform-level administrator with a defined subset of permissions
* `SUPER_VIEWER` — platform-level read-only user
* `TENANT_ADMIN` — manages users and courses within their own tenant
* `TENANT_USER` — learner within a tenant

Authorization must always be enforced on the backend.

Never rely on frontend restrictions for security.

Role permissions must be explicit and enforced server-side.

---

## Tenant Isolation

Tenant isolation is a critical security requirement.

A tenant user or tenant admin must never access another tenant's data, including by manually changing an object ID in an API request.

Examples:

* Tenant A User → Tenant A Course: allowed
* Tenant A User → Tenant B Course: denied
* Tenant A Admin → Tenant A User: allowed
* Tenant A Admin → Tenant B User: denied
* Tenant A Admin → Tenant A Course: allowed
* Tenant A Admin → Tenant B Course: denied

Tenant identity for tenant-scoped operations must be derived from authenticated server-side context whenever possible.

Do not trust client-supplied tenant IDs to determine ownership of tenant-scoped data.

Prefer enforcing isolation through:

* Querysets
* Serializers
* Permissions
* Server-side validation

Never rely on frontend filtering for security.

Cross-tenant access attempts should fail safely, including when an attacker manually changes object IDs.

---

## Tenant Lifecycle

Tenants support:

* `TRIAL_ACTIVE`
* `EXPIRED`
* `ACTIVE`

The system must:

* Calculate trial expiration correctly.
* Detect expired trials.
* Restrict tenant learning functionality when expired.
* Preserve existing tenant data after expiration.
* Support reactivation where appropriate.
* Handle repeated expiration processing safely.
* Avoid invalid state transitions.

Tenant expiration must not delete:

* Users
* Courses
* Assignments
* Learning progress

---

## Coding Rules

* Inspect existing code before making changes.
* Read the relevant models, serializers, permissions, views/viewsets, URLs, and tests before modifying security-sensitive behavior.
* Prefer small, focused changes.
* Preserve existing behavior unless the task explicitly requires changing it.
* Do not rewrite working code unnecessarily.
* Do not introduce dependencies unless necessary.
* Follow Django and DRF conventions.
* Keep business and security logic on the backend.
* Avoid duplicating business logic between serializers, views, and permissions.
* Prefer reusable business/service logic when the same rule is used in multiple places.
* Validate client input on the backend.
* Do not trust client-supplied authorization or tenant ownership information.
* Use database transactions when multiple related database writes must succeed or fail together.
* Consider database integrity and failure behavior when changing persistence logic.
* Do not silently weaken authorization to make a test pass.
* Do not remove or modify tests merely to make them pass.
* Do not implement unrelated improvements during a focused task.
* Do not refactor merely for style.

---

## Testing Rules

Tests are important for:

* Authentication
* Authorization
* Role permissions
* Tenant isolation
* Tenant expiration
* Tenant reactivation
* Course management
* Course assignment
* Learning progress
* Data integrity

When modifying security-sensitive code:

1. Inspect existing tests.
2. Add or update meaningful tests.
3. Include cross-tenant access cases where relevant.
4. Include ID-manipulation/IDOR-style cases where relevant.
5. Test important invalid-input and edge cases.
6. Run the relevant Django test suite.
7. Do not consider the task complete if relevant tests fail.

Prefer API-level tests using DRF's `APITestCase` where behavior is exposed through the API.

Tests should focus on meaningful behavior and security boundaries rather than attempting to achieve 100% coverage.

---

## Working With Existing Code

Before changing a file:

1. Read the relevant model.
2. Read related serializers.
3. Read permissions.
4. Read views/viewsets.
5. Read URLs.
6. Read existing tests.
7. Trace the request flow.
8. Identify existing authorization and tenant-isolation rules.

Do not assume existing implementation is wrong simply because it could be refactored.

Prefer the smallest change that correctly solves the requested problem.

---

## Backend Reliability

When implementing operations that modify multiple related records:

* Consider transaction boundaries.
* Avoid partially completed operations.
* Preserve database integrity if a later operation fails.
* Consider what happens if the server crashes during the operation.
* Prefer atomic database operations where appropriate.

Do not add unnecessary complexity merely to handle hypothetical failures.

---

## API and Security Principles

* Authentication identifies the caller.
* Authorization determines what the caller is allowed to do.
* Tenant isolation determines which tenant data the caller may access.
* Object-level access must be enforced server-side.
* Never assume that knowing an object ID grants access to that object.
* Never trust tenant IDs, user IDs, or role values supplied by untrusted clients when those values can be derived from authenticated server-side state.
* A successful HTTP request must not bypass tenant or role restrictions.
* Security checks should remain effective for direct API requests, not only normal frontend flows.

---

## AI Course Generation

The AI-powered course creation feature is design-only.

Do NOT implement the AI course-generation functionality unless explicitly requested.

Do NOT generate or write the final AI course-generation design.

The final AI course-generation design must be written and understood by the project author.

---

## Agent Behavior

When asked to implement a feature:

1. Inspect the existing implementation.
2. Identify the smallest set of relevant files.
3. Explain what needs to change before making broad changes.
4. Make the smallest reasonable change.
5. Add or update relevant tests.
6. Run the relevant tests.
7. Report:

   * Files changed
   * What changed
   * Tests run
   * Test results
   * Any remaining concerns
8. Stop when the requested task is complete.

When asked to debug:

1. Identify the root cause.
2. Reproduce or inspect the failing behavior.
3. Do not immediately rewrite unrelated code.
4. Make the smallest correct fix.
5. Run the failing test again.
6. Run the relevant broader test suite if appropriate.
7. Report the root cause and fix.

---

## Context and Scope Control

* Only inspect files relevant to the current task.
* Do not scan the entire repository unless necessary.
* Do not modify unrelated files.
* Do not implement unrelated improvements.
* Do not refactor merely for style.
* Prefer the smallest context necessary to complete the task.
* Do not ask for or consume the entire project context when a focused subset is sufficient.
* Keep Agent tasks narrowly scoped.
* Avoid repeating project-wide context in individual task prompts when it is already covered here.
* After completing the requested task and relevant tests, stop.

When uncertain about a significant architectural decision, ask before making a large change.

---

## Definition of Done

A task is not complete merely because the code runs.

Before considering a task complete:

* The requested behavior works.
* Authorization remains correct.
* Tenant isolation remains intact.
* Relevant edge cases are considered.
* Relevant tests pass.
* Database integrity is preserved where applicable.
* No unrelated behavior was changed.
* No unnecessary dependencies were introduced.
* The implementation follows the existing project architecture.
