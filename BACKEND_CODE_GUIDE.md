# Backend Code Guide — in Simple English

This guide explains what the code in `src/` **actually does when it runs**.
Not definitions. Not theory. Just: "when this line runs, what happens?"

Think of the project like this:
- A **Tenant** = one company / organization using the system.
- A **User** = a person. Every person has a role and belongs to a company (except platform staff).
- A **Course** = a course owned by one company.
- A **CourseAssignment** = "this course is given to this person".
- A **LearningProgress** = "how far did this person get in that course (0-100%)?"

Final chain: `Course -> CourseAssignment -> LearningProgress`.

---

## 1. What happens when a request comes in?

Example: `GET /api/courses/1/`

1. Django looks in `src/config/urls.py`.
   It sees `path("api/", include("courses.urls"))`, so it sends the request to the courses app.
2. The courses app uses a router. The router sees `courses/1/` and calls `CourseViewSet`.
3. First it checks your JWT token:
   You send `Authorization: Bearer <access_token>`.
   Django decodes the token, checks if it is expired and who you are.
   Now `request.user` = you.
4. Then it checks permissions: "Are you allowed to even try this?"
   If not, you get `403 Forbidden`. If you have no token, you get `401`.
5. Then it runs `get_queryset()`: "Which rows are you allowed to see?"
   If the row you asked for is not in that list, you get `404 Not Found` (even if it exists for another company).
6. Then it runs the serializer: "Is your data valid?"
   If not, you get `400 Bad Request`.
7. Then it saves to Postgres and sends back JSON.

Every endpoint follows these same steps.

URL map — where each URL goes:

| You call | What happens |
|---|---|
| `GET /` | Returns "Welcome to the Home Page!" |
| `POST /api/auth/token/` | You send username + password, you get back tokens |
| `POST /api/auth/token/refresh/` | You send refresh token, you get a new access token |
| `GET /api/auth/me/` | Returns who you are |
| `POST /api/auth/register/` | A new normal user joins an existing company |
| `POST /api/auth/tenant-application/` | A new company applies (creates company + admin, both waiting) |
| `POST /api/auth/application-status/` | Applicant asks "am I approved yet?" First time after approval, they get a temp password |
| `POST /api/auth/change-password/` | Logged-in user changes password |
| `GET/POST /api/auth/users/` | List or create users |
| `GET/POST /api/tenants/` | Only SUPER_ADMIN can see/create companies |
| `POST /api/tenants/<id>/approve/` | SUPER_ADMIN approves a waiting company |
| `POST /api/tenants/<id>/reject/` | SUPER_ADMIN rejects it |
| `GET /api/tenants/public/` | Anyone can see the list of active companies (no login needed) |
| `GET/POST /api/courses/` | List or create courses |
| `GET/POST /api/assignments/` | Give a course to a user |
| `GET/PATCH /api/progress/<id>/` | See or update progress % |

---

## 2. Settings — `src/config/settings.py` — what does it set up?

```python
AUTH_USER_MODEL = 'accounts.User'
```

What this does: it tells Django "do not use the built-in User table, use our own User table in the accounts app." So every time Django checks a password or login, it looks at our table with `role` and `tenant` columns.

```python
DATABASES = { ... "ENGINE": "django.db.backends.postgresql", ... }
```

What this does: it tells Django where to save everything. It reads DB name, user, password, host from the `.env` file and connects to Postgres. If you delete the DB, all tenants, users, courses disappear.

```python
REST_FRAMEWORK = { "DEFAULT_AUTHENTICATION_CLASSES": (JWTAuthentication,) }
```

What this does: every API request must prove who you are with a JWT token. No session cookies. No CSRF. Just the `Bearer` token in the header.

```python
SIMPLE_JWT = { "ACCESS_TOKEN_LIFETIME": 15 minutes, "REFRESH_TOKEN_LIFETIME": 1 day }
```

What this does: after you log in, your access token works for only 15 minutes. Then it stops working and you get `401`. You use the refresh token (valid 1 day) to get a new access token without typing your password again.

---

## 3. Users — `src/accounts/models.py` — line by line

```python
class UserRole(models.TextChoices):
    SUPER_ADMIN = "SUPER_ADMIN", "Super Admin"
    ADMIN = "ADMIN", "Admin"
    SUPER_VIEWER = "SUPER_VIEWER", "Super Viewer"
    TENANT_ADMIN = "TENANT_ADMIN", "Tenant Admin"
    TENANT_USER = "TENANT_USER", "Tenant User"
```

What this does: it creates 5 fixed roles. Every user has exactly one role stored as text in the DB. All permission checks later just ask "what is `user.role`?"

```python
class User(AbstractUser):
```

What this does: it takes Django's normal User (which already knows how to handle username, password hashing, login, active/inactive) and adds extra columns to it.

```python
email = models.EmailField(unique=True)
```

What this does: every user must have a different email. If you try to create two users with the same email, the database says no. The code needs this because later it looks up applicants by email.

```python
role = models.CharField(max_length=20, choices=UserRole.choices, default=UserRole.TENANT_USER)
```

What this does: it adds a `role` column. If you create a user and forget to set a role, it automatically becomes `TENANT_USER` (the lowest role). `max_length=20` just means the text cannot be longer than 20 characters.

```python
tenant = models.ForeignKey('tenants.Tenant', on_delete=models.PROTECT, null=True, blank=True, related_name='users')
```

What exactly does this line do? This is the most important line:
- It adds a `tenant` column to every user. That column stores "which company does this user belong to?" It holds the ID of a row in the Tenant table.
- `'tenants.Tenant'` means "link to the Tenant table". It is written as text (in quotes) to avoid a circular import problem.
- `on_delete=models.PROTECT` means: if you try to delete a company that still has users, Django stops you and raises an error. It protects you from accidentally deleting people when you delete a company.
- `null=True, blank=True` means: this field is allowed to be empty. Platform staff (`SUPER_ADMIN`, `ADMIN`, `SUPER_VIEWER`) have no company, so their `tenant` is empty (`None`). Normal company users must have it filled.
- `related_name='users'` means: from a company you can do `tenant.users.all()` and you get all its users. It creates the backward link.

```python
must_change_password = models.BooleanField(default=False)
```

What this does: it adds a True/False flag. When a company is approved, the admin's flag is set to True. That means "you logged in with a temp password, you must change it". The frontend reads this from `/me/` and forces you to the change-password page.

```python
temp_password_revealed = models.BooleanField(default=False)
```

What this does: it makes sure the temp password is shown only once. First time the applicant checks their status, the code creates a temp password, sets this to True, and shows it. Second time, it sees True and says "already shown, I will not show it again".

```python
def __str__(self):
    return self.email
```

What this does: when you look at a user in admin or print it, it shows the email instead of something confusing like `User object (1)`.

Passwords are never saved as plain text. When the code calls `user.set_password("abc123")`, Django converts it to a long hash and saves the hash. When you log in, Django hashes what you typed and compares hashes.

---

## 4. Companies — `src/tenants/models.py` — line by line

```python
class TenantStatus(models.TextChoices):
    TRIAL_ACTIVE = "TRIAL_ACTIVE", ...
    EXPIRED = "EXPIRED", ...
    ACTIVE = "ACTIVE", ...
    PENDING = "PENDING", ...
    REJECTED = "REJECTED", ...
```

What this does: a company is always in one of these 5 states. `PENDING` = waiting for approval. `TRIAL_ACTIVE` = approved, 30-day trial running. `EXPIRED` = trial time ran out. `ACTIVE` = paid / permanent. `REJECTED` = refused.

```python
name = models.CharField(max_length=255)
slug = models.SlugField(unique=True)
```

What this does: `name` is the display name like "Acme School" (two companies can have the same name). `slug` is the URL-safe unique ID like `acme-school` or `acme-school-2`. The code auto-creates the slug from the name and adds `-2`, `-3` if it already exists, so it never crashes on duplicates.

```python
status = models.CharField(..., default=TenantStatus.TRIAL_ACTIVE)
```

What this does: if you create a company and forget to set status, it becomes `TRIAL_ACTIVE`. This is just a safety net. Real code always sets it explicitly: applications set `PENDING`, approvals set `TRIAL_ACTIVE`.

```python
trial_started_at = models.DateTimeField()
trial_ends_at = models.DateTimeField()
```

What this does: it stores when the 30-day trial starts and ends. They are not auto-filled because the approval step needs to reset them (trial starts at approval, not at application).

```python
def refresh_status(self):
    if self.status == TRIAL_ACTIVE and timezone.now() >= self.trial_ends_at:
        self.status = EXPIRED
        self.save(...)
    return self.status
```

What this does: every time someone makes a request, this runs. It asks "is this trial company past its end date?" If yes, it flips it to `EXPIRED` and saves. If it is already `EXPIRED` or `ACTIVE` or `PENDING`, it does nothing. There is no background job / cron — expiry happens lazily on the next request. If you removed this, expired trials would work forever.

```python
def reactivate(self):
    self.status = ACTIVE
    self.save(...)
```

What this does: it turns a company into permanent `ACTIVE`. This only exists in Python code, there is no API endpoint for it, so you cannot call it from the frontend.

---

## 5. Courses — `src/courses/models.py` — line by line

```python
tenant = models.ForeignKey('tenants.Tenant', on_delete=models.CASCADE, related_name='courses')
```

What exactly does this line do?
- It adds a `tenant` column to every course. It stores "which company owns this course?"
- Unlike User, here there is no `null=True`, so every course MUST belong to a company. You cannot create a course without a company.
- `on_delete=models.CASCADE` means: if you delete the company, all its courses are automatically deleted too. Compare: users use `PROTECT` (block deletion), courses use `CASCADE` (delete together). Reason: users are identity (don't lose them silently), courses are content (they belong to the company).
- `related_name='courses'` means you can do `tenant.courses.all()` to get all courses of a company.

```python
title = models.CharField(max_length=255)
description = models.TextField(blank=True, null=True)
```

What this does: every course has a title (required, max 255 chars) and a description (optional, can be empty string or NULL).

---

## 6. Assignments and Progress — `src/learning/models.py` — line by line

```python
course = models.ForeignKey("courses.Course", on_delete=models.CASCADE, related_name="assignments")
user = models.ForeignKey("accounts.User", on_delete=models.CASCADE, related_name="course_assignments")
```

What does this do? It creates the assignment table with two links: "which course?" + "which person?" Together they mean "this person must do this course". If the course is deleted, the assignment is deleted. If the user is deleted, the assignment is deleted. `course.assignments.all()` gives all people assigned to a course. `user.course_assignments.all()` gives all courses assigned to a person.

```python
assigned_at = models.DateTimeField(auto_now_add=True)
```

What this does: when the assignment row is created, Django fills in the current time automatically. You cannot set it from the API (it is read-only in the serializer).

```python
class Meta:
    constraints = [models.UniqueConstraint(fields=["course", "user"], name="unique_course_assignment")]
```

What exactly does this do? It tells the database: "never allow the same course + same user twice". Even if someone bypasses the API and writes directly to the DB, the DB throws an error. The serializer also checks this and returns `400`, but this is the final safety net against double-assigning and race conditions.

```python
assignment = models.OneToOneField("CourseAssignment", on_delete=models.CASCADE, related_name="progress")
```

What exactly does this do? It creates the progress table. Each progress row points to exactly one assignment, and each assignment has exactly one progress row. `OneToOne` = one-to-one, not many. If the assignment is deleted, the progress is deleted. You can do `assignment.progress` to get the percentage.

```python
progress_percentage = models.PositiveIntegerField(default=0)
```

What this does: stores 0 to... well, DB only checks it is >= 0. The "max 100" check is done in the serializer, not the DB. New progress starts at 0.

```python
started_at = models.DateTimeField(auto_now_add=True)
completed_at = models.DateTimeField(null=True, blank=True)
```

What this does: `started_at` is filled automatically when progress is created. `completed_at` stays empty until the user reaches 100%. When the code sees 100, it fills in now. When it sees less than 100, it clears it back to empty. You cannot set `completed_at` from the API — the server decides it.

---

## 7. Login and tokens — what really happens?

`POST /api/auth/token/` with `{username, password}`:
1. Django looks up the user by username.
2. It hashes the password you sent and compares to the stored hash. It also checks `is_active`. If the user is waiting for approval (`is_active=False`), login fails even with the right password.
3. If all good, it creates two signed strings: access token (15 min) + refresh token (1 day) and sends them back.
4. Your frontend must save both and send `Authorization: Bearer <access>` on every later request.

`POST /api/auth/token/refresh/` with `{refresh}`:
1. Django checks the refresh token signature and expiry.
2. It sends back a new access token.

`GET /api/auth/me/`:
1. Django reads your token, finds you.
2. It returns your id, username, email, role, tenant id, and `must_change_password`.
3. Frontend uses this to decide: "should I force this user to change password now?"

---

## 8. How a new company joins — step by step

Step 1 — Apply: `POST /api/auth/tenant-application/` with `{organization_name, admin_name, admin_email}`. No login needed.
- Code cleans the org name, checks the username/email are not already taken.
- It makes a slug: `"My School"` becomes `my-school`, or `my-school-2` if taken.
- In one atomic transaction (all-or-nothing), it creates:
  - a Tenant with status `PENDING`, trial window now to now+30 days (placeholder),
  - a User with role `TENANT_ADMIN`, `is_active=False`, and an unusable password (cannot log in at all).
- Returns `201` with tenant + user info.

Step 2 — Approve: `POST /api/tenants/<id>/approve/`. Only `SUPER_ADMIN` can do this.
- Code checks the company is still `PENDING`, else returns `400`.
- It finds the waiting admin. In one transaction it:
  - flips company to `TRIAL_ACTIVE` and resets trial to now to now+30 days (trial starts now, not at application time),
  - sets admin to `is_active=True`, `must_change_password=True`, `temp_password_revealed=False`.
- Now the admin can log in, but only with a temp password.

Reject: `POST /api/tenants/<id>/reject/` flips `PENDING` to `REJECTED`. Admin stays inactive forever.

Step 3 — Get temp password: `POST /api/auth/application-status/` with `{admin_email}`. No login needed.
- Code finds the admin by email (case-insensitive, so `Foo@x.com` = `foo@x.com`).
- If still `PENDING`, it says "still waiting", no password.
- If `REJECTED`, it says "not approved", no password.
- If approved and this is the first check: it creates a random 12-letter password using `secrets` (secure random, not normal `random`), hashes it with `set_password`, sets `revealed=True`, saves, and returns the plain password ONCE.
- Second check: it sees `revealed=True` and does NOT return the password again. It just says "already issued".
- It uses `select_for_update` + transaction = locks the row so two requests at the same time cannot both create different passwords.

Step 4 — First login + change: log in with temp password, then `POST /api/auth/change-password/` with `{current_password, new_password}`.
- Code checks `current_password` matches the hash, else `400`.
- It checks new password is at least 8 chars and not too common (Django validators).
- It hashes the new password, saves, and sets `must_change_password=False`.
- Now `/me/` shows False and the temp password no longer works.

---

## 9. Permissions — "who is allowed to do what?"

All checks live in `permissions.py` files. Each one just asks about `request.user.role` and `request.method`.

- `IsSuperAdmin`: passes only if you are logged in AND your role is `SUPER_ADMIN`. Used for companies list/approve/reject. Everyone else gets `403`.
- `IsUserManager`: `SUPER_VIEWER` can only do `GET/HEAD/OPTIONS` (read-only). `SUPER_ADMIN`, `ADMIN`, `TENANT_ADMIN` can do everything. `TENANT_USER` gets `403` for all user management.
- `IsTenantActive`: platform staff (`SUPER_ADMIN/ADMIN/SUPER_VIEWER`) always pass. Company users must have a company, and the company must not be `EXPIRED` or `REJECTED`. Before checking, it calls `refresh_status()`, so an expired trial is flipped to `EXPIRED` right here and then blocked with `403`.
- `IsCourseManager` / `IsAssignmentManager`: only `SUPER_ADMIN`, `ADMIN`, `TENANT_ADMIN` pass. Used only on writes (create/update/delete). Reads don't need it, so viewers and normal users can still read.
- `IsProgressManager`: managers pass fully. `TENANT_USER` passes only for `PATCH/PUT` (update own progress). They cannot create or delete progress.

Important pattern: reads use `[IsAuthenticated, IsTenantActive]`, writes add one more manager check. So removing the manager check would let anyone write.

---

## 10. Tenant isolation — "how do we stop Company A seeing Company B?"

Three layers work together:

1. `get_queryset()` — hides rows. Example in `courses/views.py`:
   - Platform staff: `Course.objects.all()` = see everything.
   - `TENANT_ADMIN`: `Course.objects.filter(tenant_id=my_tenant)` = see only my company's courses.
   - `TENANT_USER`: `Course.objects.filter(tenant_id=my_tenant, assignments__user_id=my_id)` = see only my company's courses that are assigned to me.
   - If you ask for `/courses/999/` from another company, it is not in your queryset, so Django returns `404`, not `403`. This hides even the existence of the other company's data.

2. Serializer `validate()` — blocks bad writes with `400`. Example: `TENANT_ADMIN` tries to create a user with `role=ADMIN` or with another company's ID → validation error. `TENANT_ADMIN` tries to assign a course from another company → validation error.

3. `perform_create / perform_update` — ignores what the client sent and forces the right company. Example: `TENANT_ADMIN` creates a course without sending `tenant` → code does `serializer.save(tenant=my_tenant)`. So even if they tried to spoof another tenant, it gets overwritten.

If you removed `get_queryset` filtering, any logged-in user could list all companies' data. That's a total isolation failure.

---

## 11. Courses, assignments, progress — what happens?

Create course: `POST /api/courses/` with `{title, description, tenant?}`.
- `TENANT_USER` gets `403` (not a manager).
- `TENANT_ADMIN` does not send `tenant` — code injects their own company.
- `ADMIN/SUPER_ADMIN` must send `tenant`, else serializer returns `400 "tenant required"`.

List courses: `GET /api/courses/`.
- Admin sees own company's courses. User sees only assigned ones. Unassigned course in own company → `404` for that user.

Assign: `POST /api/assignments/` with `{course, user}`.
- Code checks: both exist, both belong to same company, user role is `TENANT_USER` (you cannot assign a course to an admin), not already assigned, and if requester is `TENANT_ADMIN`, the course must be in their own company.
- If all pass, in one transaction it creates the assignment AND a progress row at 0%. If progress creation fails, the assignment is rolled back (nothing saved).
- Duplicate → `400`. Cross-company → `400`.

Update progress: `PATCH /api/progress/<id>/` with `{progress_percentage}`.
- You cannot `POST` to `/progress/` — code always returns `405`. Progress is only born together with an assignment.
- You cannot change `assignment`, `started_at`, `completed_at` from API — they are read-only. If you send them, they are ignored.
- Percentage must be 0–100, else `400`.
- If you send 100, code sets `completed_at=now`. If you send less than 100, code clears `completed_at` to empty.

---

## 12. What do the errors mean?

- `400`: your data is wrong. Examples: duplicate assignment, percentage 101, creating platform user without tenant, approving a non-pending company, wrong current password.
- `401`: you are not logged in (no token, bad token, expired token, wrong password on login).
- `403`: you are logged in but not allowed. Examples: normal user tries to create a course, viewer tries to edit, anyone from an expired company tries anything, tenant admin tries to open `TenantViewSet`.
- `404`: not found OR not yours. Examples: you ask for another company's course/user/assignment by ID — you get `404` on purpose so you cannot tell if it exists.
- `405`: you tried `POST /api/progress/` — not allowed, progress comes from assignments.

---

## 13. Roles in plain words

- `SUPER_ADMIN`: boss of the whole system. Can create companies, approve/reject, see everything.
- `ADMIN`: like super admin for data (sees all users/courses), but cannot touch companies (approve/reject) and cannot create super-admins.
- `SUPER_VIEWER`: can only look, never change. Every write returns `403`.
- `TENANT_ADMIN`: boss of one company. Sees only own company. Can create normal users and courses (company auto-filled). Cannot create admins or touch other companies.
- `TENANT_USER`: normal student. Cannot manage users or courses. Sees only courses assigned to them. Can only update own progress percentage.

---

## 14. Quick traces to test yourself

1. `GET /api/courses/` as Tenant Admin: token → you are admin of company A → permission passes (active) → queryset = `filter(tenant=A)` → return only A's courses.
2. `POST /api/assignments/ {B-course, A-user}` as A-admin: permission passes → serializer sees `course.tenant(B) != user.tenant(A)` → `400`, nothing saved.
3. Onboarding: apply → `PENDING` → approve → `TRIAL_ACTIVE` → status check mints temp once → login → `/me` shows `must_change_password=true` → change password → flag false.
4. `PATCH /api/progress/5/` as stranger: row 5 not in your queryset → `404` before any validation.
5. Expired trial opens any protected page: `refresh_status()` flips to `EXPIRED` → `IsTenantActive` returns False → `403`, queryset never runs.
