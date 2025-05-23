# Medical Assistant API Documentation

This document provides details about the available API endpoints, including sample requests and responses.

## Document Management API

### Upload Document

Upload medical documents (PDF, DOCX) for processing and storage.

**Endpoint:** `POST /api/upload/`

**Request:**
```http
POST /api/upload/ HTTP/1.1
Content-Type: multipart/form-data

{
  "file": [binary file content],
  "document_type_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479"
}
```

**Response (Success):**
```json
{
  "id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
  "file_name": "diabetes_management.pdf",
  "document_type": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
  "uploaded_at": "2024-05-10T14:30:45Z",
  "metadata": null
}
```

**Response (Error):**
```json
{
  "error": "Standard type with ID f47ac10b-58cc-4372-a567-0e02b2c3d479 not found."
}
```

### List Documents

Retrieve a list of all uploaded documents.

**Endpoint:** `GET /api/documents/`

**Request:**
```http
GET /api/documents/ HTTP/1.1
```

**Response (Success):**
```json
[
  {
    "id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
    "file_name": "diabetes_management.pdf",
    "document_type_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
    "document_type_name": "Policy",
    "uploaded_at": "2024-05-10T14:30:45Z",
    "document_extension_type": "pdf"
  },
  {
    "id": "a1b2c3d4-e5f6-7890-abcd-1234567890ab",
    "file_name": "hypertension_protocol.docx",
    "document_type_id": "g47ac10b-58cc-4372-a567-0e02b2c3d482",
    "document_type_name": "Protocol",
    "uploaded_at": "2024-05-09T11:20:15Z",
    "document_extension_type": "docx"
  }
]
```

**Response (Error):**
```json
{
  "error": "Failed to retrieve documents: Database connection error"
}
```

### Get Document

Retrieve metadata for a specific document by ID.

**Endpoint:** `GET /api/documents/{document_id}/`

**Request:**
```http
GET /api/documents/f47ac10b-58cc-4372-a567-0e02b2c3d479/ HTTP/1.1
```

**Response (Success):**
```json
{
  "id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
  "file_name": "diabetes_management.pdf",
  "document_type_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
  "document_type_name": "Policy",
  "uploaded_at": "2024-05-10T14:30:45Z",
  "document_extension_type": "pdf"
}
```

**Response (Error):**
```json
{
  "error": "Document with ID f47ac10b-58cc-4372-a567-0e02b2c3d479 not found."
}
```

### Download Document

Download a document file by ID.

**Endpoint:** `GET /api/documents/{document_id}/download/`

**Request:**
```http
GET /api/documents/f47ac10b-58cc-4372-a567-0e02b2c3d479/download/ HTTP/1.1
```

**Response (Success):**
```
Binary file content with appropriate Content-Type and Content-Disposition headers
```

**Response (Error):**
```json
{
  "error": "Document with ID f47ac10b-58cc-4372-a567-0e02b2c3d479 not found."
}
```

### Delete Document

Delete a document by ID, including its file in storage and related chunks.

**Endpoint:** `DELETE /api/documents/{document_id}/`

**Request:**
```http
DELETE /api/documents/f47ac10b-58cc-4372-a567-0e02b2c3d479/ HTTP/1.1
```

**Response (Success):**
```
204 No Content
```

**Response (Error):**
```json
{
  "error": "Document with ID f47ac10b-58cc-4372-a567-0e02b2c3d479 not found."
}
```

## Content Generation API

Generate content based on a topic using the RAG system.

**Endpoint:** `POST /api/generate/`

**Request:**
```json
{
  "topic": "Diabetes Management Protocol",
  "content_type": "Policy",
  "model_name": "llama3-8b-instruct"
}
```

**Response (Success):**
```json
{
  "id": "a1b2c3d4-e5f6-7890-abcd-1234567890ab",
  "topic": "Diabetes Management Protocol",
  "content_type": "Policy",
  "generated_text": "# Diabetes Management Protocol\n\nThis policy outlines the standard procedures for managing patients with diabetes in accordance with New Zealand healthcare guidelines...",
  "llm_model_used": "llama3-8b-instruct",
  "source_chunk_ids": ["uuid1", "uuid2", "uuid3"],
  "validation_results": {
    "consistency": true,
    "clinical_relevance": true,
    "language_tone": true,
    "potential_issues": ["Consider adding more specific guidance on insulin dosing"]
  },
  "created_at": "2024-05-10T15:20:30Z"
}
```

**Response (Error):**
```json
{
  "error": "Generation service error: Knowledge base search failed"
}
```

## Generated Content List API

Retrieve a list of previously generated content with optional filtering.

**Endpoint:** `GET /api/generated-content/`

**Request:**
```http
GET /api/generated-content/?content_type=Policy&llm_model_used=llama3-8b-instruct&created_after=2024-01-01 HTTP/1.1
```

**Response:**
```json
{
  "count": 2,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": "a1b2c3d4-e5f6-7890-abcd-1234567890ab",
      "topic": "Diabetes Management Protocol",
      "content_type": "Policy",
      "generated_text": "# Diabetes Management Protocol\n\nThis policy outlines...",
      "llm_model_used": "llama3-8b-instruct",
      "source_chunk_ids": ["uuid1", "uuid2", "uuid3"],
      "validation_results": {
        "consistency": true,
        "clinical_relevance": true,
        "language_tone": true,
        "potential_issues": ["Consider adding more specific guidance on insulin dosing"]
      },
      "created_at": "2024-05-10T15:20:30Z"
    },
    {
      "id": "b2c3d4e5-f6a7-8901-bcde-23456789abcd",
      "topic": "Hypertension Management",
      "content_type": "Policy",
      "generated_text": "# Hypertension Management\n\nThis policy provides guidelines...",
      "llm_model_used": "llama3-8b-instruct",
      "source_chunk_ids": ["uuid4", "uuid5"],
      "validation_results": {
        "consistency": true,
        "clinical_relevance": true,
        "language_tone": true,
        "potential_issues": []
      },
      "created_at": "2024-05-09T10:15:20Z"
    }
  ]
}
```

## Generated Content Detail API

Retrieve details of a specific generated content by ID.

**Endpoint:** `GET /api/generated-content/{id}/`

**Request:**
```http
GET /api/generated-content/a1b2c3d4-e5f6-7890-abcd-1234567890ab/ HTTP/1.1
```

**Response:**
```json
{
  "id": "a1b2c3d4-e5f6-7890-abcd-1234567890ab",
  "topic": "Diabetes Management Protocol",
  "content_type": "Policy",
  "generated_text": "# Diabetes Management Protocol\n\nThis policy outlines the standard procedures for managing patients with diabetes in accordance with New Zealand healthcare guidelines...",
  "llm_model_used": "llama3-8b-instruct",
  "source_chunk_ids": ["uuid1", "uuid2", "uuid3"],
  "validation_results": {
    "consistency": true,
    "clinical_relevance": true,
    "language_tone": true,
    "potential_issues": ["Consider adding more specific guidance on insulin dosing"]
  },
  "created_at": "2024-05-10T15:20:30Z"
}
```

## Medical Standards API

### Create Standard

Create a new medical standard.

**Endpoint:** `POST /api/standards/`

**Request:**
```json
{
  "standard_title": "Diabetes Management Standard",
  "standard_type": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
  "content": "This standard outlines the procedures for managing diabetes in accordance with NZ healthcare guidelines...",
  "version": "1.0",
  "generated_content": null
}
```

**Response (Success):**
```json
{
  "id": "e47ac10b-58cc-4372-a567-0e02b2c3d480",
  "standard_title": "Diabetes Management Standard",
  "standard_type": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
  "standard_type_name": "Clinical Procedure",
  "content": "This standard outlines the procedures for managing diabetes in accordance with NZ healthcare guidelines...",
  "version": "1.0",
  "generated_content": null,
  "llm_model_used": null,
  "is_ai_generated": false,
  "created_at": "2024-05-15T10:30:45Z",
  "updated_at": "2024-05-15T10:30:45Z"
}
```

### Update Standard

Update an existing medical standard.

**Endpoint:** `PUT /api/standards/{id}/`

**Request:**
```json
{
  "standard_title": "Updated Diabetes Management Standard",
  "version": "1.1"
}
```

**Response (Success):**
```json
{
  "id": "e47ac10b-58cc-4372-a567-0e02b2c3d480",
  "standard_title": "Updated Diabetes Management Standard",
  "standard_type": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
  "standard_type_name": "Clinical Procedure",
  "content": "This standard outlines the procedures for managing diabetes in accordance with NZ healthcare guidelines...",
  "version": "1.1",
  "generated_content": null,
  "llm_model_used": null,
  "is_ai_generated": false,
  "created_at": "2024-05-15T10:30:45Z",
  "updated_at": "2024-05-15T11:15:20Z"
}
```

### Delete Standard

Soft delete a medical standard.

**Endpoint:** `DELETE /api/standards/{id}/`

**Response (Success):**
```
204 No Content
```

### Get Standard

Retrieve a specific medical standard by ID.

**Endpoint:** `GET /api/standards/{id}/`

**Response:**
```json
{
  "id": "e47ac10b-58cc-4372-a567-0e02b2c3d480",
  "standard_title": "Diabetes Management Standard",
  "standard_type": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
  "standard_type_name": "Clinical Procedure",
  "content": "This standard outlines the procedures for managing diabetes in accordance with NZ healthcare guidelines...",
  "version": "1.0",
  "generated_content": "a1b2c3d4-e5f6-7890-abcd-1234567890ab",
  "llm_model_used": "llama3-8b-instruct",
  "is_ai_generated": true,
  "created_at": "2024-05-15T10:30:45Z",
  "updated_at": "2024-05-15T10:30:45Z"
}
```

### List Standards

Retrieve a list of all medical standards with optional filtering by standard type.

**Endpoint:** `GET /api/standards/`

**Request with filter:**
```
GET /api/standards/?standard_type_id=f47ac10b-58cc-4372-a567-0e02b2c3d479
```

**Response:**
```json
[
  {
    "id": "e47ac10b-58cc-4372-a567-0e02b2c3d480",
    "standard_title": "Diabetes Management Standard",
    "standard_type": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
    "standard_type_name": "Clinical Procedure",
    "content": "This standard outlines the procedures...",
    "version": "1.0",
    "generated_content": "a1b2c3d4-e5f6-7890-abcd-1234567890ab",
    "llm_model_used": "llama3-8b-instruct",
    "is_ai_generated": true,
    "created_at": "2024-05-15T10:30:45Z",
    "updated_at": "2024-05-15T10:30:45Z"
  }
]
```

**Request without filter (returns all standards):**
```
GET /api/standards/
```

### Search Standards

Search for standards by type or title.

**Endpoint:** `GET /api/standards/search/?standard_type_id={id}&standard_title={title}`

**Request:**
```
GET /api/standards/search/?standard_title=Diabetes
```

**Response:**
```json
[
  {
    "id": "e47ac10b-58cc-4372-a567-0e02b2c3d480",
    "standard_title": "Diabetes Management Standard",
    "standard_type": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
    "standard_type_name": "Clinical Procedure",
    "content": "This standard outlines the procedures...",
    "version": "1.0",
    "generated_content": "a1b2c3d4-e5f6-7890-abcd-1234567890ab",
    "llm_model_used": "llama3-8b-instruct",
    "is_ai_generated": true,
    "created_at": "2024-05-15T10:30:45Z",
    "updated_at": "2024-05-15T10:30:45Z"
  }
]
```

### List Standard Types

Retrieve a list of all standard types.

**Endpoint:** `GET /api/standard-types/`

**Response:**
```json
[
  {
    "id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
    "name": "Clinical Procedure"
  },
  {
    "id": "g47ac10b-58cc-4372-a567-0e02b2c3d482",
    "name": "Clinical Protocol"
  },
  {
    "id": "h47ac10b-58cc-4372-a567-0e02b2c3d483",
    "name": "Policy"
  }
]
```

## Complaint Management API

### List Complaints

Retrieve a list of all complaints.

**Endpoint:** `GET /api/complaints/`

**Request:**
```http
GET /api/complaints/ HTTP/1.1
```

**Response (Success):**
```json
[
  {
    "id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
    "title": "Medication Error",
    "reference_number": "COMP-2024-001",
    "practice": "Auckland Medical Center",
    "form_date": "2024-05-15",
    "reporter_name": "Jane Smith",
    "group": "Nursing",
    "email": "jane.smith@example.com",
    "patient_name": "John Doe",
    "patient_nhi": "ABC1234",
    "patient_dob": "1980-01-15",
    "patient_email": "john.doe@example.com",
    "patient_phone": "+64 21 123 4567",
    "is_acknowledged": true,
    "received_date": "2024-05-10",
    "complaint_method": "Email",
    "complaint_severity": "Medium",
    "complaint_owner": "Dr. Robert Johnson",
    "complaint_details": "Patient received incorrect medication dosage",
    "action_taken": "Immediate correction of medication and patient monitoring",
    "is_notified_external": false,
    "other_comments": "Patient was satisfied with the quick response",
    "file_upload_path": "complaints/uuid_document.pdf",
    "request_review_by": "Medical Director",
    "complaint_reason": "Medication error during hospital stay",
    "is_resolved": true,
    "identified_issues": "Pharmacy verification process needs improvement",
    "staff_skill_issues": "Additional training needed for new staff",
    "policy_impact": "Current medication verification policy was not followed",
    "is_disclosure_required": true,
    "is_followup_required": true,
    "is_event_analysis_required": true,
    "is_training_required": true,
    "is_visible_to_users": true,
    "disable_editing": false,
    "created_at": "2024-05-10T14:30:45Z",
    "updated_at": "2024-05-15T09:20:30Z"
  }
]
```

### Get Complaint

Retrieve a specific complaint by ID.

**Endpoint:** `GET /api/complaints/{complaint_id}/`

**Request:**
```http
GET /api/complaints/f47ac10b-58cc-4372-a567-0e02b2c3d479/ HTTP/1.1
```

**Response (Success):**
```json
{
  "id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
  "title": "Medication Error",
  "reference_number": "COMP-2024-001",
  "practice": "Auckland Medical Center",
  "form_date": "2024-05-15",
  "reporter_name": "Jane Smith",
  "group": "Nursing",
  "email": "jane.smith@example.com",
  "patient_name": "John Doe",
  "patient_nhi": "ABC1234",
  "patient_dob": "1980-01-15",
  "patient_email": "john.doe@example.com",
  "patient_phone": "+64 21 123 4567",
  "is_acknowledged": true,
  "received_date": "2024-05-10",
  "complaint_method": "Email",
  "complaint_severity": "Medium",
  "complaint_owner": "Dr. Robert Johnson",
  "complaint_details": "Patient received incorrect medication dosage",
  "action_taken": "Immediate correction of medication and patient monitoring",
  "is_notified_external": false,
  "other_comments": "Patient was satisfied with the quick response",
  "file_upload_path": "complaints/uuid_document.pdf",
  "request_review_by": "Medical Director",
  "complaint_reason": "Medication error during hospital stay",
  "is_resolved": true,
  "identified_issues": "Pharmacy verification process needs improvement",
  "staff_skill_issues": "Additional training needed for new staff",
  "policy_impact": "Current medication verification policy was not followed",
  "is_disclosure_required": true,
  "is_followup_required": true,
  "is_event_analysis_required": true,
  "is_training_required": true,
  "is_visible_to_users": true,
  "disable_editing": false,
  "created_at": "2024-05-10T14:30:45Z",
  "updated_at": "2024-05-15T09:20:30Z"
}
```

**Response (Error):**
```json
{
  "error": "Complaint with ID f47ac10b-58cc-4372-a567-0e02b2c3d479 not found."
}
```

### Create Complaint

Create a new complaint.

**Endpoint:** `POST /api/complaints/`

**Request:**
```http
POST /api/complaints/ HTTP/1.1
Content-Type: multipart/form-data

{
  "title": "Medication Error",
  "reference_number": "COMP-2024-001",
  "practice": "Auckland Medical Center",
  "form_date": "2024-05-15",
  "reporter_name": "Jane Smith",
  "group": "Nursing",
  "email": "jane.smith@example.com",
  "patient_name": "John Doe",
  "patient_nhi": "ABC1234",
  "patient_dob": "1980-01-15",
  "patient_email": "john.doe@example.com",
  "patient_phone": "+64 21 123 4567",
  "is_acknowledged": true,
  "received_date": "2024-05-10",
  "complaint_method": "Email",
  "complaint_severity": "Medium",
  "complaint_owner": "Dr. Robert Johnson",
  "complaint_details": "Patient received incorrect medication dosage",
  "action_taken": "Immediate correction of medication and patient monitoring",
  "is_notified_external": false,
  "other_comments": "Patient was satisfied with the quick response",
  "file_upload": [binary file content],
  "request_review_by": "Medical Director",
  "complaint_reason": "Medication error during hospital stay",
  "is_resolved": true,
  "identified_issues": "Pharmacy verification process needs improvement",
  "staff_skill_issues": "Additional training needed for new staff",
  "policy_impact": "Current medication verification policy was not followed",
  "is_disclosure_required": true,
  "is_followup_required": true,
  "is_event_analysis_required": true,
  "is_training_required": true,
  "is_visible_to_users": true,
  "disable_editing": false
}
```

**Response (Success):**
```json
{
  "id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
  "title": "Medication Error",
  "reference_number": "COMP-2024-001",
  "practice": "Auckland Medical Center",
  "form_date": "2024-05-15",
  "reporter_name": "Jane Smith",
  "group": "Nursing",
  "email": "jane.smith@example.com",
  "patient_name": "John Doe",
  "patient_nhi": "ABC1234",
  "patient_dob": "1980-01-15",
  "patient_email": "john.doe@example.com",
  "patient_phone": "+64 21 123 4567",
  "is_acknowledged": true,
  "received_date": "2024-05-10",
  "complaint_method": "Email",
  "complaint_severity": "Medium",
  "complaint_owner": "Dr. Robert Johnson",
  "complaint_details": "Patient received incorrect medication dosage",
  "action_taken": "Immediate correction of medication and patient monitoring",
  "is_notified_external": false,
  "other_comments": "Patient was satisfied with the quick response",
  "file_upload_path": "complaints/uuid_document.pdf",
  "request_review_by": "Medical Director",
  "complaint_reason": "Medication error during hospital stay",
  "is_resolved": true,
  "identified_issues": "Pharmacy verification process needs improvement",
  "staff_skill_issues": "Additional training needed for new staff",
  "policy_impact": "Current medication verification policy was not followed",
  "is_disclosure_required": true,
  "is_followup_required": true,
  "is_event_analysis_required": true,
  "is_training_required": true,
  "is_visible_to_users": true,
  "disable_editing": false,
  "created_at": "2024-05-10T14:30:45Z",
  "updated_at": "2024-05-10T14:30:45Z"
}
```

### Update Complaint

Update an existing complaint.

**Endpoint:** `PATCH /api/complaints/{complaint_id}/`

**Request:**
```http
PATCH /api/complaints/f47ac10b-58cc-4372-a567-0e02b2c3d479/ HTTP/1.1
Content-Type: multipart/form-data

{
  "is_resolved": true,
  "identified_issues": "Updated: Pharmacy verification process needs improvement and staff training required",
  "file_upload": [binary file content]
}
```

**Response (Success):**
```json
{
  "id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
  "title": "Medication Error",
  "reference_number": "COMP-2024-001",
  "practice": "Auckland Medical Center",
  "form_date": "2024-05-15",
  "reporter_name": "Jane Smith",
  "group": "Nursing",
  "email": "jane.smith@example.com",
  "patient_name": "John Doe",
  "patient_nhi": "ABC1234",
  "patient_dob": "1980-01-15",
  "patient_email": "john.doe@example.com",
  "patient_phone": "+64 21 123 4567",
  "is_acknowledged": true,
  "received_date": "2024-05-10",
  "complaint_method": "Email",
  "complaint_severity": "Medium",
  "complaint_owner": "Dr. Robert Johnson",
  "complaint_details": "Patient received incorrect medication dosage",
  "action_taken": "Immediate correction of medication and patient monitoring",
  "is_notified_external": false,
  "other_comments": "Patient was satisfied with the quick response",
  "file_upload_path": "complaints/new_uuid_document.pdf",
  "request_review_by": "Medical Director",
  "complaint_reason": "Medication error during hospital stay",
  "is_resolved": true,
  "identified_issues": "Updated: Pharmacy verification process needs improvement and staff training required",
  "staff_skill_issues": "Additional training needed for new staff",
  "policy_impact": "Current medication verification policy was not followed",
  "is_disclosure_required": true,
  "is_followup_required": true,
  "is_event_analysis_required": true,
  "is_training_required": true,
  "is_visible_to_users": true,
  "disable_editing": false,
  "created_at": "2024-05-10T14:30:45Z",
  "updated_at": "2024-05-15T09:20:30Z"
}
```

### Delete Complaint

Delete a complaint by ID, including its file in storage.

**Endpoint:** `DELETE /api/complaints/{complaint_id}/`

**Request:**
```http
DELETE /api/complaints/f47ac10b-58cc-4372-a567-0e02b2c3d479/ HTTP/1.1
```

**Response (Success):**
```
204 No Content
```

**Response (Error):**
```json
{
  "error": "Complaint with ID f47ac10b-58cc-4372-a567-0e02b2c3d479 not found."
}
```

### Compare Standards

Compare two standard contents and analyze their differences using LLM.

**Endpoint:** `POST /api/standards/compare/`

**Request:**
```json
{
  "content1": "This standard outlines the procedures for managing diabetes in accordance with NZ healthcare guidelines...",
  "content2": "This updated standard provides comprehensive guidance for diabetes management, including new insulin protocols...",
  "standard_type_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479"
}
```

**Response (Success):**
```json
{
  "valid": true,
  "comparison": {
    "key_differences": [
      {
        "aspect": "Insulin Protocol",
        "document1": "Recommends fixed dosing schedule based on weight",
        "document2": "Introduces sliding scale approach based on blood glucose readings"
      },
      {
        "aspect": "Monitoring Frequency",
        "document1": "Suggests blood glucose monitoring 4 times daily",
        "document2": "Recommends personalized monitoring schedule based on patient risk factors"
      }
    ],
    "recommendation": "Document 2 is better overall as it provides more personalized care approaches and incorporates recent clinical evidence on variable insulin dosing",
    "improvement_suggestions": [
      "Both documents could benefit from clearer emergency protocols for hypoglycemia",
      "Consider adding visual aids or flowcharts for clinical decision-making"
    ]
  }
}
```

**Response (Invalid Content):**
```json
{
  "valid": false,
  "message": "First content is not valid for Clinical Procedure",
  "details": "The content appears to be a general informational text about diabetes rather than a clinical procedure document. It lacks procedural steps, clinical guidance, and the formal structure expected in a procedure document."
}
```

**Response (Error):**
```json
{
  "error": "Missing required parameters. Please provide content1, content2, and standard_type_id."
}
```





