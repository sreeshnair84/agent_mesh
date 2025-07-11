import { apiClient } from '@/lib/api-client';

export interface PayloadField {
  name: string;
  type: 'string' | 'number' | 'boolean' | 'array' | 'object';
  description: string;
  required: boolean;
  example?: any;
  enum?: string[];
}

export interface PayloadSchema {
  name: string;
  description: string;
  fields: PayloadField[];
  examples: any[];
}

export interface AgentPayload {
  agent_id: string;
  input_payload?: PayloadSchema;
  output_payload?: PayloadSchema;
}

export interface ValidationResult {
  valid: boolean;
  errors: string[];
  payload_type: string;
  agent_id: string;
}

export const payloadService = {
  // Get agent payload specifications
  async getAgentPayload(agentId: string): Promise<AgentPayload> {
    const response = await apiClient.get(`/agents/${agentId}/payload`);
    return response.data;
  },

  // Update agent payload specifications
  async updateAgentPayload(
    agentId: string,
    payload: {
      input_payload?: PayloadSchema;
      output_payload?: PayloadSchema;
    }
  ): Promise<void> {
    await apiClient.put(`/agents/${agentId}/payload`, payload);
  },

  // Validate data against payload schema
  async validatePayload(
    agentId: string,
    payloadData: any,
    payloadType: 'input' | 'output'
  ): Promise<ValidationResult> {
    const response = await apiClient.post(`/agents/${agentId}/payload/validate`, {
      payload_data: payloadData,
      payload_type: payloadType
    });
    return response.data;
  },

  // Get example payloads for an agent
  async getPayloadExamples(agentId: string): Promise<{
    input_examples: any[];
    output_examples: any[];
  }> {
    const response = await apiClient.get(`/agents/${agentId}/payload/examples`);
    return response.data;
  },

  // Helper function to generate schema from payload
  generateJsonSchema(payload: PayloadSchema): any {
    const schema: any = {
      type: 'object',
      title: payload.name,
      description: payload.description,
      properties: {},
      required: []
    };

    payload.fields.forEach(field => {
      schema.properties[field.name] = {
        type: field.type,
        description: field.description
      };

      if (field.example !== undefined) {
        schema.properties[field.name].example = field.example;
      }

      if (field.enum && field.enum.length > 0) {
        schema.properties[field.name].enum = field.enum;
      }

      if (field.required) {
        schema.required.push(field.name);
      }
    });

    if (payload.examples && payload.examples.length > 0) {
      schema.examples = payload.examples;
    }

    return schema;
  },

  // Helper function to create payload from JSON schema
  createPayloadFromSchema(schema: any): PayloadSchema {
    const payload: PayloadSchema = {
      name: schema.title || 'Unnamed Schema',
      description: schema.description || '',
      fields: [],
      examples: schema.examples || []
    };

    const properties = schema.properties || {};
    const required = schema.required || [];

    Object.entries(properties).forEach(([fieldName, fieldSchema]: [string, any]) => {
      const field: PayloadField = {
        name: fieldName,
        type: fieldSchema.type || 'string',
        description: fieldSchema.description || '',
        required: required.includes(fieldName),
      };

      if (fieldSchema.example !== undefined) {
        field.example = fieldSchema.example;
      }

      if (fieldSchema.enum && Array.isArray(fieldSchema.enum)) {
        field.enum = fieldSchema.enum;
      }

      payload.fields.push(field);
    });

    return payload;
  },

  // Validate payload structure
  validatePayloadStructure(payload: PayloadSchema): {
    valid: boolean;
    errors: string[];
  } {
    const errors: string[] = [];

    if (!payload.name || payload.name.trim() === '') {
      errors.push('Payload name is required');
    }

    if (!payload.description || payload.description.trim() === '') {
      errors.push('Payload description is required');
    }

    if (!payload.fields || payload.fields.length === 0) {
      errors.push('At least one field is required');
    }

    payload.fields.forEach((field, index) => {
      if (!field.name || field.name.trim() === '') {
        errors.push(`Field ${index + 1}: Name is required`);
      }

      if (!field.type) {
        errors.push(`Field ${index + 1}: Type is required`);
      }

      if (!field.description || field.description.trim() === '') {
        errors.push(`Field ${index + 1}: Description is required`);
      }

      // Check for duplicate field names
      const duplicateFields = payload.fields.filter(f => f.name === field.name);
      if (duplicateFields.length > 1) {
        errors.push(`Field ${index + 1}: Duplicate field name "${field.name}"`);
      }
    });

    return {
      valid: errors.length === 0,
      errors
    };
  }
};

export default payloadService;
