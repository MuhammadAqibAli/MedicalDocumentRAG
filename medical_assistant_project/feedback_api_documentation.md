# Feedback Management API Documentation

This document provides details about the Feedback Management API endpoints, including sample requests and responses.

## Feedback Management API

The Feedback Management API allows you to create, retrieve, update, and delete patient feedback entries.

### List Feedback

Retrieve a paginated list of feedback entries with optional filtering.

**Endpoint:** `GET /api/feedback/`

**Query Parameters:**
- `status` (optional): Filter by status (e.g., 'New', 'In Progress', 'Pending Review', 'Resolved', 'Closed')
- `practice` (optional): Filter by practice ID
- `submitter` (optional): Filter by submitter user ID
- `management_owner` (optional): Filter by management owner user ID
- `review_requested_by` (optional): Filter by review requested by user ID
- `form_date` (optional): Filter by form date (exact, greater than or equal, less than or equal)
- `date_received` (optional): Filter by date received (exact, greater than or equal, less than or equal)
- `created_at` (optional): Filter by creation date (exact, greater than or equal, less than or equal)
- `search` (optional): Search in title, reference number, patient NHI, and feedback details

**Request:**
```http
GET /api/feedback/?status=New&practice=f47ac10b-58cc-4372-a567-0e02b2c3d479 HTTP/1.1
```

**Response (Success):**
```json
{
  "count": 2,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": "a1b2c3d4-e5f6-7890-abcd-1234567890ab",
      "title": "Medication Error Feedback",
      "reference_number": "FB-20240520-1234",
      "practice_name": "Auckland Medical Center",
      "form_date": "2024-05-20",
      "submitter_name": "John Smith",
      "patient_nhi": "ABC1234",
      "status": "New",
      "created_at": "2024-05-20T14:30:45Z",
      "updated_at": "2024-05-20T14:30:45Z",
      "attachment_count": 2
    },
    {
      "id": "b2c3d4e5-f6a7-8901-bcde-23456789abcd",
      "title": "Waiting Time Complaint",
      "reference_number": "FB-20240519-5678",
      "practice_name": "Auckland Medical Center",
      "form_date": "2024-05-19",
      "submitter_name": "Jane Doe",
      "patient_nhi": "DEF5678",
      "status": "New",
      "created_at": "2024-05-19T10:15:20Z",
      "updated_at": "2024-05-19T10:15:20Z",
      "attachment_count": 0
    }
  ]
}
```

### Get Feedback

Retrieve a specific feedback entry by ID.

**Endpoint:** `GET /api/feedback/{id}/`

**Request:**
```http
GET /api/feedback/a1b2c3d4-e5f6-7890-abcd-1234567890ab/ HTTP/1.1
```

**Response (Success):**
```json
{
  "id": "a1b2c3d4-e5f6-7890-abcd-1234567890ab",
  "title": "Medication Error Feedback",
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
  "other_comments": "Patient was very understanding about the situation.",
  "management_owner": "e5f6a7b8-c9d0-1234-efgh-6789abcdef12",
  "management_owner_name": "Sarah Johnson",
  "review_requested_by": null,
  "review_requested_by_name": null,
  "status": "New",
  "created_at": "2024-05-20T14:30:45Z",
  "updated_at": "2024-05-20T14:30:45Z",
  "attachments": [
    {
      "id": "f6a7b8c9-d0e1-2345-fghi-789abcdef123",
      "file_name": "medication_instructions.pdf",
      "uploaded_at": "2024-05-20T14:30:45Z"
    },
    {
      "id": "a7b8c9d0-e1f2-3456-ghij-89abcdef1234",
      "file_name": "patient_notes.docx",
      "uploaded_at": "2024-05-20T14:30:45Z"
    }
  ]
}
```

**Response (Error):**
```json
{
  "detail": "Not found."
}
```

### Create Feedback

Create a new feedback entry with optional file attachments.

**Endpoint:** `POST /api/feedback/`

**Request:**
```http
POST /api/feedback/ HTTP/1.1
Content-Type: multipart/form-data

{
  "title": "Medication Error Feedback",
  "practice": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
  "form_date": "2024-05-20",
  "submitter": "c3d4e5f6-a7b8-9012-cdef-456789abcde0",
  "group": "Nursing",
  "email": "john.smith@example.com",
  "date_received": "2024-05-20",
  "feedback_method": "d4e5f6a7-b8c9-0123-defg-56789abcdef1",
  "patient_nhi": "ABC1234",
  "feedback_details": "Patient reported receiving incorrect medication dosage instructions.",
  "other_comments": "Patient was very understanding about the situation.",
  "management_owner": "e5f6a7b8-c9d0-1234-efgh-6789abcdef12",
  "review_requested_by": null,
  "attachments": [binary file content]
}
```

**Response (Success):**
```json
{
  "id": "a1b2c3d4-e5f6-7890-abcd-1234567890ab",
  "title": "Medication Error Feedback",
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
  "other_comments": "Patient was very understanding about the situation.",
  "management_owner": "e5f6a7b8-c9d0-1234-efgh-6789abcdef12",
  "management_owner_name": "Sarah Johnson",
  "review_requested_by": null,
  "review_requested_by_name": null,
  "status": "New",
  "created_at": "2024-05-20T14:30:45Z",
  "updated_at": "2024-05-20T14:30:45Z",
  "attachments": [
    {
      "id": "f6a7b8c9-d0e1-2345-fghi-789abcdef123",
      "file_name": "medication_instructions.pdf",
      "uploaded_at": "2024-05-20T14:30:45Z"
    }
  ]
}
```

**Response (Error):**
```json
{
  "title": ["This field is required."],
  "practice": ["This field is required."],
  "form_date": ["This field is required."],
  "submitter": ["This field is required."],
  "patient_nhi": ["This field is required."],
  "feedback_details": ["This field is required."]
}
```
