# AI-Assisted Development

I used an GitHub AI coding agent throughout development for frontend implementation, backend implementation/review, debugging, and automated testing.

I kept the context focused by giving the agent only the relevant files and functions for each task instead of repeatedly providing the whole project. Project-wide instructions were kept in `.github/copilot-instructions.md`.

For example, for automated testing I used a focused prompt like:

```text
Create automated tests for the courses app.

Files:
- src/courses/models.py
- src/courses/permissions.py
- src/courses/serializers.py
- src/courses/views.py
- src/courses/tests.py

Cover:
- course creation and updates
- role permissions
- tenant isolation
- cross-tenant ID access
- expired tenant access

Use the existing models and API structure. Keep the tests focused on the courses app and run them after implementation.
```

I used the same approach for other backend apps, providing specific paths and functions to reduce unnecessary context and token usage. I reviewed the generated changes and verified them with the application and tests.
