### Update Feedback

Update an existing feedback entry.

**Endpoint:** `PUT /api/feedback/{id}/`

**Request:**
```http
PUT /api/feedback/a1b2c3d4-e5f6-7890-abcd-1234567890ab/ HTTP/1.1
Content-Type: application/json

{
  "title": "Updated Medication Error Feedback",
  "status": "In Progress",
  "management_owner": "e5f6a7b8-c9d0-1234-efgh-6789abcdef12",
  "other_comments": "Updated comments after speaking with the patient."
}
```

**Response (Success):**
```json
{
  "id": "a1b2c3d4-e5f6-7890-abcd-1234567890ab",
  "title": "Updated Medication Error Feedback",
  "reference_number": "FB-20240520-1234",
  "practice": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
  "practice_name": "Auckland Medical Center",
  "form_date": "2024-05-20",
  "submitter": "c3d4e5f6-a7b8-9012-cdef-456789abcde0",
  "submitter_name": "John Smith",
  "group": "Nursing",
  "email": "john.smith@example.com",
  "date_received": "2024-05-20",
  "feedback_method": "d4e5f6a7-b8c9-0123-defg-56789abcdef1",
  "feedback_method_name": "Email",
  "patient_nhi": "ABC1234",
  "feedback_details": "Patient reported receiving incorrect medication dosage instructions.",
  "other_comments": "Updated comments after speaking with the patient.",
  "management_owner": "e5f6a7b8-c9d0-1234-efgh-6789abcdef12",
  "management_owner_name": "Sarah Johnson",
  "review_requested_by": null,
  "review_requested_by_name": null,
  "status": "In Progress",
  "created_at": "2024-05-20T14:30:45Z",
  "updated_at": "2024-05-20T15:45:30Z",
  "attachments": [
    {
      "id": "f6a7b8c9-d0e1-2345-fghi-789abcdef123",
      "file_name": "medication_instructions.pdf",
      "uploaded_at": "2024-05-20T14:30:45Z"
    }
  ]
}
```

### Delete Feedback

Delete a feedback entry by ID.

**Endpoint:** `DELETE /api/feedback/{id}/`

**Request:**
```http
DELETE /api/feedback/a1b2c3d4-e5f6-7890-abcd-1234567890ab/ HTTP/1.1
```

**Response (Success):**
```
204 No Content
```

### Add Attachment to Feedback

Add a file attachment to an existing feedback entry.

**Endpoint:** `POST /api/feedback/{id}/add_attachment/`

**Request:**
```http
POST /api/feedback/a1b2c3d4-e5f6-7890-abcd-1234567890ab/add_attachment/ HTTP/1.1
Content-Type: multipart/form-data

{
  "file": [binary file content]
}
```

**Response (Success):**
```json
{
  "id": "g7b8c9d0-e1f2-3456-hijk-9abcdef12345",
  "file_name": "additional_notes.docx",
  "uploaded_at": "2024-05-20T16:30:45Z"
}
```

**Response (Error):**
```json
{
  "error": "No file provided"
}
```

### Remove Attachment from Feedback

Remove a file attachment from a feedback entry.

**Endpoint:** `DELETE /api/feedback/{id}/remove_attachment/?attachment_id={attachment_id}`

**Request:**
```http
DELETE /api/feedback/a1b2c3d4-e5f6-7890-abcd-1234567890ab/remove_attachment/?attachment_id=f6a7b8c9-d0e1-2345-fghi-789abcdef123 HTTP/1.1
```

**Response (Success):**
```
204 No Content
```

**Response (Error):**
```json
{
  "error": "attachment_id parameter is required"
}
```

### Download Feedback Attachment

Download a feedback attachment file.

**Endpoint:** `GET /api/feedback-attachments/{attachment_id}/download/`

**Request:**
```http
GET /api/feedback-attachments/f6a7b8c9-d0e1-2345-fghi-789abcdef123/download/ HTTP/1.1
```

**Response (Success):**
```
Binary file content with appropriate Content-Type and Content-Disposition headers
```

**Response (Error):**
```json
{
  "error": "Attachment with ID f6a7b8c9-d0e1-2345-fghi-789abcdef123 not found."
}
```

## Practice Management API

The Practice Management API allows you to manage medical practices.

### List Practices

Retrieve a list of all practices.

**Endpoint:** `GET /api/practices/`

**Query Parameters:**
- `name` (optional): Filter by practice name
- `is_active` (optional): Filter by active status
- `search` (optional): Search in name, address, and email

**Request:**
```http
GET /api/practices/ HTTP/1.1
```

**Response (Success):**
```json
[
  {
    "id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
    "name": "Auckland Medical Center",
    "address": "123 Healthcare St, Auckland",
    "contact_number": "+64 9 123 4567",
    "email": "info@aucklandmedical.co.nz",
    "created_at": "2024-01-15T10:30:45Z",
    "updated_at": "2024-01-15T10:30:45Z",
    "is_active": true
  },
  {
    "id": "g58bd21c-69dd-5483-b678-1f13c3d4e580",
    "name": "Wellington Health Clinic",
    "address": "456 Wellness Ave, Wellington",
    "contact_number": "+64 4 987 6543",
    "email": "contact@wellingtonhealth.co.nz",
    "created_at": "2024-02-20T14:15:30Z",
    "updated_at": "2024-02-20T14:15:30Z",
    "is_active": true
  }
]
```

### Get Practice

Retrieve a specific practice by ID.

**Endpoint:** `GET /api/practices/{id}/`

**Request:**
```http
GET /api/practices/f47ac10b-58cc-4372-a567-0e02b2c3d479/ HTTP/1.1
```

**Response (Success):**
```json
{
  "id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
  "name": "Auckland Medical Center",
  "address": "123 Healthcare St, Auckland",
  "contact_number": "+64 9 123 4567",
  "email": "info@aucklandmedical.co.nz",
  "created_at": "2024-01-15T10:30:45Z",
  "updated_at": "2024-01-15T10:30:45Z",
  "is_active": true
}
```

**Response (Error):**
```json
{
  "detail": "Not found."
}
```
