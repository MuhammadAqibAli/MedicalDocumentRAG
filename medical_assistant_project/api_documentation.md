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

## Audit Questions API

The Audit Questions API allows you to generate, retrieve, update, and delete audit questions based on specific policies.

### List Audit Questions

Retrieve a list of all audit questions with optional filtering by policy name.

**Endpoint:** `GET /api/audit-questions/`

**Query Parameters:**
- `policy_name` (optional): Filter questions by policy name (case-insensitive, partial match)

**Request:**
```http
GET /api/audit-questions/?policy_name=Privacy HTTP/1.1
```

**Response (Success):**
```json
[
  {
    "id": "a1b2c3d4-e5f6-7890-abcd-1234567890ab",
    "question_text": "Does the organization have a documented process for handling data breaches?",
    "policy_name": "Data Privacy Policy",
    "ai_model": "gpt-4o",
    "options": ["Compliant", "Partial Compliant", "Non Compliant"],
    "created_at": "2024-05-20T14:30:45Z",
    "updated_at": "2024-05-20T14:30:45Z"
  },
  {
    "id": "b2c3d4e5-f6a7-8901-bcde-23456789abcd",
    "question_text": "Are all staff members required to complete privacy training annually?",
    "policy_name": "Data Privacy Policy",
    "ai_model": "gpt-4o",
    "options": ["Compliant", "Partial Compliant", "Non Compliant"],
    "created_at": "2024-05-20T14:30:45Z",
    "updated_at": "2024-05-20T14:30:45Z"
  }
]
```

**Response (Empty):**
```json
[]
```

### Generate Audit Questions

Generate audit questions based on a specific policy using an AI model.

**Endpoint:** `POST /api/audit-questions/generate/`

**Request:**
```json
{
  "ai_model": "gpt-4o",
  "policy_name": "Data Privacy Policy",
  "number_of_questions": 5
}
```

**Request Parameters:**
- `ai_model` (string, required): The AI model to use from OpenRouter (e.g., "gpt-4o", "gpt-4.1", "gemini-2.5-pro-preview")
- `policy_name` (string, required): The name of the policy to generate questions about
- `number_of_questions` (integer, required): The total number of questions to generate (1-50)

**Response (Success):**
```json
[
  {
    "id": "a1b2c3d4-e5f6-7890-abcd-1234567890ab",
    "question_text": "Does the organization have a documented process for handling data breaches?",
    "policy_name": "Data Privacy Policy",
    "ai_model": "gpt-4o",
    "options": ["Compliant", "Partial Compliant", "Non Compliant"],
    "created_at": "2024-05-20T14:30:45Z",
    "updated_at": "2024-05-20T14:30:45Z"
  },
  {
    "id": "b2c3d4e5-f6a7-8901-bcde-23456789abcd",
    "question_text": "Are all staff members required to complete privacy training annually?",
    "policy_name": "Data Privacy Policy",
    "ai_model": "gpt-4o",
    "options": ["Compliant", "Partial Compliant", "Non Compliant"],
    "created_at": "2024-05-20T14:30:45Z",
    "updated_at": "2024-05-20T14:30:45Z"
  },
  {
    "id": "c3d4e5f6-a7b8-9012-cdef-456789abcde0",
    "question_text": "Is there a designated Data Protection Officer responsible for privacy compliance?",
    "policy_name": "Data Privacy Policy",
    "ai_model": "gpt-4o",
    "options": ["Compliant", "Partial Compliant", "Non Compliant"],
    "created_at": "2024-05-20T14:30:45Z",
    "updated_at": "2024-05-20T14:30:45Z"
  },
  {
    "id": "d4e5f6a7-b8c9-0123-defg-56789abcdef1",
    "question_text": "Does the organization maintain a register of all personal data processing activities?",
    "policy_name": "Data Privacy Policy",
    "ai_model": "gpt-4o",
    "options": ["Compliant", "Partial Compliant", "Non Compliant"],
    "created_at": "2024-05-20T14:30:45Z",
    "updated_at": "2024-05-20T14:30:45Z"
  },
  {
    "id": "e5f6a7b8-c9d0-1234-efgh-6789abcdef12",
    "question_text": "Are data protection impact assessments conducted for high-risk processing activities?",
    "policy_name": "Data Privacy Policy",
    "ai_model": "gpt-4o",
    "options": ["Compliant", "Partial Compliant", "Non Compliant"],
    "created_at": "2024-05-20T14:30:45Z",
    "updated_at": "2024-05-20T14:30:45Z"
  }
]
```

**Response (Error):**
```json
{
  "error": "Failed to parse generated content as JSON"
}
```

### Update Audit Question

Update a specific audit question by its ID.

**Endpoint:** `PUT /api/audit-questions/{question_id}/`

**Request:**
```json
{
  "question_text": "Updated question text: Does the organization have a documented process for handling and reporting data breaches within 72 hours?",
  "options": ["Compliant", "Partial Compliant", "Non Compliant", "Not Applicable"]
}
```

**Request Parameters:**
- `question_text` (string, optional): The updated text of the audit question
- `policy_name` (string, optional): The updated policy name
- `options` (array, optional): The updated list of options for the question

**Response (Success):**
```json
{
  "id": "a1b2c3d4-e5f6-7890-abcd-1234567890ab",
  "question_text": "Updated question text: Does the organization have a documented process for handling and reporting data breaches within 72 hours?",
  "policy_name": "Data Privacy Policy",
  "ai_model": "gpt-4o",
  "options": ["Compliant", "Partial Compliant", "Non Compliant", "Not Applicable"],
  "created_at": "2024-05-20T14:30:45Z",
  "updated_at": "2024-05-20T15:45:30Z"
}
```

**Response (Error):**
```json
{
  "error": "Audit question not found"
}
```

### Delete Audit Question

Delete a specific audit question by its ID.

**Endpoint:** `DELETE /api/audit-questions/{question_id}/delete/`

**Request:**
```http
DELETE /api/audit-questions/a1b2c3d4-e5f6-7890-abcd-1234567890ab/delete/ HTTP/1.1
```

**Response (Success):**
```
204 No Content
```

**Response (Error):**
```json
{
  "error": "Audit question not found"
}
```

## Additional API Documentation

For detailed documentation on the Feedback Management API, please refer to the following files:

1. [Feedback API Documentation - Part 1](feedback_api_documentation.md)
2. [Feedback API Documentation - Part 2](feedback_api_documentation_part2.md)
3. [Feedback API Documentation - Part 3](feedback_api_documentation_part3.md)
