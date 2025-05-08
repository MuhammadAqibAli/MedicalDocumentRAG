# Medical Assistant API Documentation

This document provides details about the available API endpoints, including sample requests and responses.

## Document Upload API

Upload medical documents (PDF, DOCX) for processing and storage.

**Endpoint:** `POST /api/upload/`

**Request:**
```http
POST /api/upload/ HTTP/1.1
Content-Type: multipart/form-data

{
  "file": [binary file content],
  "document_type": "Policy"
}
```

**Response (Success):**
```json
{
  "id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
  "file_name": "diabetes_management.pdf",
  "document_type": "Policy",
  "uploaded_at": "2024-05-10T14:30:45Z",
  "metadata": null
}
```

**Response (Error):**
```json
{
  "error": "Unsupported file type '.txt'. Only PDF and DOCX allowed."
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

