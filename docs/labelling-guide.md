# Endpoint sensitivity labelling guide

Label the endpoint's **business sensitivity**, not whether a vulnerability is
present. Use the path, HTTP method, response purpose, and available target
documentation. If the endpoint cannot be understood confidently, press `s` and
record why in a later review.

## LOW

Public content with no user-specific or operational data.

Examples:

- `/`
- `/assets/app.js`
- `/about`

## MEDIUM

Ordinary user data or user-facing functionality where compromise matters to one
user but does not control authentication, privileges, or high-impact money
movement.

Examples:

- `/users/me/profile`
- `/orders/history`
- `/community/posts`

## HIGH

Authentication, session, token, account-recovery, or account-control surfaces.
These endpoints can affect identity or access for a user.

Examples:

- `/auth/login`
- `/users/me/password`
- `/password-reset/request`

## CRITICAL

Administrative, privileged, payment, financial-transfer, or system-wide
management surfaces. Use this class when compromise could affect many users or
move/control high-value funds.

Examples:

- `/admin/users`
- `/payments/transfer`
- `/internal/tenant-management`

## Consistency rules

1. Prefer the most specific path meaning over generic words such as `api` or
   `v1`.
2. A public documentation endpoint is LOW unless it exposes sensitive data.
3. Login and token endpoints are HIGH even when they return an error.
4. Payment history is MEDIUM; payment execution or transfer is CRITICAL.
5. Do not infer sensitivity from a vulnerability finding.
6. Keep the same decision for normalized ID variants such as `/users/1` and
   `/users/:id`.

The labeller stores the class, labeler, and optional notes in
`eval/labels/endpoints_labelled.csv`. Skipped rows remain available on the
next run.
