# API Contracts: Subscription Tiers, Entitlements & TVOD

**Branch**: `012-entitlements-tvod` | **Date**: 2026-02-17

All endpoints under `/api/v1/`. Auth via `Authorization: Bearer <token>` unless marked **Guest-accessible**.

---

## Package Management (Admin)

### `GET /admin/packages`
List all subscription packages.

**Auth**: Admin
**Response 200**:
```json
[
  {
    "id": "uuid",
    "name": "Premium",
    "description": "Full catalog access",
    "tier": "premium",
    "title_count": 142
  }
]
```

---

### `POST /admin/packages`
Create a new subscription package.

**Auth**: Admin
**Request**:
```json
{
  "name": "Basic",
  "description": "Standard library access",
  "tier": "basic"
}
```
**Response 201**: Package object (same shape as GET item)
**Response 422**: Validation error if name missing

---

### `PUT /admin/packages/{package_id}`
Update a package's name, description, or tier.

**Auth**: Admin
**Request**: Same fields as POST (all optional)
**Response 200**: Updated package object
**Response 404**: Package not found

---

### `DELETE /admin/packages/{package_id}`
Delete a package. Cascades to PackageContent. Does not delete UserEntitlements (they become orphaned with null package reference — handle in service).

**Auth**: Admin
**Response 204**: No content
**Response 409**: Cannot delete if active user entitlements exist

---

### `POST /admin/packages/{package_id}/titles`
Assign a title to a package.

**Auth**: Admin
**Request**:
```json
{ "title_id": "uuid" }
```
**Response 201**:
```json
{ "package_id": "uuid", "title_id": "uuid", "content_type": "vod_title" }
```
**Response 409**: Title already assigned to this package

---

### `DELETE /admin/packages/{package_id}/titles/{title_id}`
Remove a title from a package.

**Auth**: Admin
**Response 204**: No content
**Response 404**: Assignment not found

---

### `PATCH /admin/users/{user_id}/subscription`
Update a user's subscription tier. Creates/replaces the user's SVOD entitlement pointing to the named package. Also updates `User.subscription_tier` for display.

**Auth**: Admin
**Request**:
```json
{
  "package_id": "uuid",
  "expires_at": null
}
```
Set `package_id: null` to cancel subscription.
**Response 200**:
```json
{
  "user_id": "uuid",
  "package_id": "uuid",
  "subscription_tier": "premium",
  "expires_at": null
}
```

---

## Offer Management (Admin)

### `GET /admin/titles/{title_id}/offers`
List all offers (including inactive) for a title.

**Auth**: Admin
**Response 200**:
```json
[
  {
    "id": "uuid",
    "offer_type": "rent",
    "price_cents": 399,
    "currency": "USD",
    "rental_window_hours": 48,
    "is_active": true,
    "created_at": "2026-02-17T00:00:00Z"
  }
]
```

---

### `POST /admin/titles/{title_id}/offers`
Create an offer for a title. Fails if an active offer of the same type already exists.

**Auth**: Admin
**Request**:
```json
{
  "offer_type": "rent",
  "price_cents": 399,
  "currency": "USD",
  "rental_window_hours": 48
}
```
`rental_window_hours` required when `offer_type = "rent"`, ignored otherwise.
**Response 201**: Offer object
**Response 409**: Active offer of this type already exists for this title

---

### `PATCH /admin/titles/{title_id}/offers/{offer_id}`
Update an offer (e.g., change price, deactivate).

**Auth**: Admin
**Request** (all fields optional):
```json
{
  "price_cents": 299,
  "is_active": false
}
```
**Response 200**: Updated offer object

---

## Catalog — Access Options (User/Guest)

### `GET /catalog/titles` — Modified response
Existing endpoint. Each title now includes `access_options` in the response.

**Auth**: Optional (guest-accessible)
**Additional fields per title**:
```json
{
  "id": "uuid",
  "title": "Inception",
  "...(existing fields)": "...",
  "access_options": [
    { "type": "svod", "label": "Included with your subscription" },
    { "type": "rent", "price_cents": 399, "currency": "USD", "rental_window_hours": 48 },
    { "type": "buy",  "price_cents": 999, "currency": "USD" }
  ],
  "user_access": {
    "has_access": true,
    "access_type": "svod",
    "expires_at": null
  }
}
```

For unauthenticated (guest) requests: `user_access` is omitted; `access_options` shows all configured offers.
For authenticated users: `user_access` reflects their current entitlement.

---

### `GET /catalog/titles/{title_id}` — Modified response
Same `access_options` + `user_access` additions as above.

---

## TVOD Transactions (User)

### `POST /catalog/titles/{title_id}/purchase`
Rent or buy a title. Creates a `UserEntitlement` with `source_type='tvod'`.

**Auth**: Required (redirected to login for guests)
**Rate limit**: 10 requests/hour per user (stricter TVOD limit, FR-025)
**Request**:
```json
{ "offer_type": "rent" }
```
or
```json
{ "offer_type": "buy" }
```
**Response 201**:
```json
{
  "entitlement_id": "uuid",
  "title_id": "uuid",
  "offer_type": "rent",
  "expires_at": "2026-02-19T00:00:00Z",
  "price_cents": 399,
  "currency": "USD"
}
```
**Response 404**: Title or active offer not found
**Response 409**: User already has an active entitlement of this type (already rented/owned)
**Response 429**: Rate limit exceeded

---

## Viewing Sessions (User)

### `POST /viewing/sessions`
Start a new playback session. Checks concurrent stream limit. Cleans up abandoned sessions first.

**Auth**: Required
**Request**:
```json
{
  "title_id": "uuid",
  "content_type": "vod_title"
}
```
**Response 201**:
```json
{
  "session_id": "uuid",
  "started_at": "2026-02-17T10:00:00Z"
}
```
**Response 403**: No entitlement for this title
**Response 429**: Concurrent stream limit reached (includes list of active sessions to stop)

---

### `PUT /viewing/sessions/{session_id}/heartbeat`
Signal that the session is still active. Resets the 5-minute abandonment timer.

**Auth**: Required
**Response 200**: `{ "last_heartbeat_at": "2026-02-17T10:03:00Z" }`
**Response 404**: Session not found or already ended

---

### `DELETE /viewing/sessions/{session_id}`
End a session explicitly (user stops playback or stops another session to free a slot).

**Auth**: Required
**Response 204**: No content
**Response 404**: Session not found

---

### `GET /viewing/sessions`
List caller's active sessions (for "stop a session" UI).

**Auth**: Required
**Response 200**:
```json
[
  {
    "session_id": "uuid",
    "title_id": "uuid",
    "title_name": "Inception",
    "started_at": "2026-02-17T10:00:00Z",
    "last_heartbeat_at": "2026-02-17T10:05:00Z"
  }
]
```

---

## Error Responses

### Rate limit exceeded (429)
```json
{
  "detail": "Rate limit exceeded",
  "retry_after": 60
}
```
Headers: `Retry-After: 60`

### Access denied (403)
```json
{
  "detail": "No active entitlement for this title",
  "access_options": [
    { "type": "rent", "price_cents": 399, "currency": "USD", "rental_window_hours": 48 }
  ]
}
```

### Concurrent stream limit (429 from session start)
```json
{
  "detail": "Concurrent stream limit reached",
  "limit": 1,
  "active_sessions": [
    {
      "session_id": "uuid",
      "title_name": "Inception",
      "started_at": "2026-02-17T10:00:00Z"
    }
  ]
}
```
