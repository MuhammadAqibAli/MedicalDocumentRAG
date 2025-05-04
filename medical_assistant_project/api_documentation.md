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