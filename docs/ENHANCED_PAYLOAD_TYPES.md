# Agent Payload Field Types Enhancement

## Overview
The Agent Mesh now supports enhanced payload field types for more diverse data handling including multimedia and document types.

## Supported Field Types

### Basic Data Types
- **string**: Text strings
- **number**: Numeric values (integers, floats)
- **boolean**: True/false values
- **object**: JSON objects/dictionaries
- **array**: Lists/arrays of values

### Media Types
- **audio**: Audio files (MP3, WAV, OGG, etc.)
- **image**: Image files (JPG, PNG, GIF, SVG, etc.)
- **video**: Video files (MP4, AVI, MOV, etc.)
- **text**: Plain text content
- **document**: General document files
- **file**: Generic file type
- **binary**: Binary data

### Structured Data Types
- **json**: JSON formatted data
- **xml**: XML formatted data
- **csv**: CSV formatted data
- **pdf**: PDF documents

### Flexible Type
- **any**: Accepts any data type (use with caution)

## Usage Examples

### Text Processing Agent
```json
{
  "name": "process_text",
  "type": "text",
  "description": "Input text to process",
  "required": true,
  "example": "Hello, world!"
}
```

### Image Analysis Agent
```json
{
  "name": "input_image",
  "type": "image",
  "description": "Image file to analyze",
  "required": true,
  "example": "base64_encoded_image_data"
}
```

### Audio Transcription Agent
```json
{
  "name": "audio_file",
  "type": "audio",
  "description": "Audio file to transcribe",
  "required": true,
  "example": "audio_file.mp3"
}
```

### Document Processing Agent
```json
{
  "name": "document",
  "type": "pdf",
  "description": "PDF document to process",
  "required": true,
  "example": "document.pdf"
}
```

### Multi-Modal Agent
```json
{
  "name": "mixed_input",
  "type": "any",
  "description": "Accepts any type of input",
  "required": false,
  "example": "Can be text, image, audio, etc."
}
```

## Best Practices

1. **Use Specific Types**: Choose the most specific type that matches your data (e.g., use `image` instead of `file` for images)
2. **Validation**: Always validate input data matches the expected type
3. **Examples**: Provide clear examples for each field type
4. **Documentation**: Document expected formats and file types
5. **Security**: Validate file uploads and content types for security

## Migration Guide

### From Basic Types
If you previously used:
- `string` for text content → Consider using `text` for better clarity
- `string` for file paths → Use appropriate media types (`image`, `audio`, `video`)
- `object` for structured data → Use `json` or `xml` for better typing

### Updating Existing Agents
1. Review current payload specifications
2. Update field types to more specific types where appropriate
3. Test with new validation rules
4. Update documentation and examples

## API Changes

The following endpoints now support enhanced payload types:
- `POST /api/v1/agents` - Create agent with enhanced payload specs
- `PUT /api/v1/agents/{id}` - Update agent payload specifications
- `POST /api/v1/agents/{id}/payload` - Update payload specs directly

## Validation Rules

- All types are validated against the pattern: `^(string|number|boolean|object|array|text|audio|image|video|document|file|binary|json|xml|csv|pdf|any)$`
- Media types should include appropriate metadata (MIME type, size, etc.)
- Binary data should be base64 encoded in JSON payloads
- File references should include proper URIs or paths
