## Feedback Method API

The Feedback Method API allows you to manage feedback methods.

### List Feedback Methods

Retrieve a list of all feedback methods.

**Endpoint:** `GET /api/feedback-methods/`

**Request:**
```http
GET /api/feedback-methods/ HTTP/1.1
```

**Response (Success):**
```json
[
  {
    "id": "d4e5f6a7-b8c9-0123-defg-56789abcdef1",
    "name": "Email",
    "description": "Feedback received via email",
    "created_at": "2024-01-15T10:30:45Z"
  },
  {
    "id": "e5f6a7b8-c9d0-1234-efgh-6789abcdef12",
    "name": "Phone",
    "description": "Feedback received via phone call",
    "created_at": "2024-01-15T10:30:45Z"
  },
  {
    "id": "f6a7b8c9-d0e1-2345-fghi-789abcdef123",
    "name": "In Person",
    "description": "Feedback received in person",
    "created_at": "2024-01-15T10:30:45Z"
  }
]
```

### Get Feedback Method

Retrieve a specific feedback method by ID.

**Endpoint:** `GET /api/feedback-methods/{id}/`

**Request:**
```http
GET /api/feedback-methods/d4e5f6a7-b8c9-0123-defg-56789abcdef1/ HTTP/1.1
```

**Response (Success):**
```json
{
  "id": "d4e5f6a7-b8c9-0123-defg-56789abcdef1",
  "name": "Email",
  "description": "Feedback received via email",
  "created_at": "2024-01-15T10:30:45Z"
}
```

**Response (Error):**
```json
{
  "detail": "Not found."
}
```
