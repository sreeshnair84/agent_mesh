import React, { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Badge } from '@/components/ui/badge';
import { Trash2, Plus, Copy, Eye } from 'lucide-react';

interface PayloadField {
  name: string;
  type: 'string' | 'number' | 'boolean' | 'array' | 'object';
  description: string;
  required: boolean;
  example?: any;
  enum?: string[];
}

interface PayloadSchema {
  name: string;
  description: string;
  fields: PayloadField[];
  examples: any[];
}

interface AgentPayloadFormProps {
  inputPayload?: PayloadSchema;
  outputPayload?: PayloadSchema;
  onPayloadChange: (type: 'input' | 'output', payload: PayloadSchema) => void;
}

const AgentPayloadForm: React.FC<AgentPayloadFormProps> = ({
  inputPayload,
  outputPayload,
  onPayloadChange
}) => {
  const [activeTab, setActiveTab] = useState<'input' | 'output'>('input');
  const [showExamples, setShowExamples] = useState(false);

  const emptyPayload: PayloadSchema = {
    name: '',
    description: '',
    fields: [],
    examples: []
  };

  const currentPayload = activeTab === 'input' 
    ? inputPayload || emptyPayload 
    : outputPayload || emptyPayload;

  const updatePayload = (updates: Partial<PayloadSchema>) => {
    const updatedPayload = { ...currentPayload, ...updates };
    onPayloadChange(activeTab, updatedPayload);
  };

  const addField = () => {
    const newField: PayloadField = {
      name: '',
      type: 'string',
      description: '',
      required: false
    };
    updatePayload({
      fields: [...currentPayload.fields, newField]
    });
  };

  const updateField = (index: number, updates: Partial<PayloadField>) => {
    const updatedFields = [...currentPayload.fields];
    updatedFields[index] = { ...updatedFields[index], ...updates };
    updatePayload({ fields: updatedFields });
  };

  const removeField = (index: number) => {
    const updatedFields = currentPayload.fields.filter((_, i) => i !== index);
    updatePayload({ fields: updatedFields });
  };

  const addExample = () => {
    const newExample = {};
    updatePayload({
      examples: [...currentPayload.examples, newExample]
    });
  };

  const updateExample = (index: number, value: string) => {
    try {
      const parsedValue = JSON.parse(value);
      const updatedExamples = [...currentPayload.examples];
      updatedExamples[index] = parsedValue;
      updatePayload({ examples: updatedExamples });
    } catch (error) {
      console.error('Invalid JSON:', error);
    }
  };

  const removeExample = (index: number) => {
    const updatedExamples = currentPayload.examples.filter((_, i) => i !== index);
    updatePayload({ examples: updatedExamples });
  };

  const generateExample = () => {
    const example: any = {};
    currentPayload.fields.forEach(field => {
      if (field.example !== undefined) {
        example[field.name] = field.example;
      } else {
        switch (field.type) {
          case 'string':
            example[field.name] = field.enum ? field.enum[0] : 'example string';
            break;
          case 'number':
            example[field.name] = 42;
            break;
          case 'boolean':
            example[field.name] = true;
            break;
          case 'array':
            example[field.name] = [];
            break;
          case 'object':
            example[field.name] = {};
            break;
        }
      }
    });
    return example;
  };

  const copyExampleToClipboard = (example: any) => {
    navigator.clipboard.writeText(JSON.stringify(example, null, 2));
  };

  return (
    <div className="space-y-6">
      {/* Tab Navigation */}
      <div className="flex space-x-4 border-b">
        <button
          onClick={() => setActiveTab('input')}
          className={`px-4 py-2 font-medium ${
            activeTab === 'input' 
              ? 'border-b-2 border-blue-500 text-blue-600' 
              : 'text-gray-600 hover:text-gray-900'
          }`}
        >
          Input Payload
        </button>
        <button
          onClick={() => setActiveTab('output')}
          className={`px-4 py-2 font-medium ${
            activeTab === 'output' 
              ? 'border-b-2 border-blue-500 text-blue-600' 
              : 'text-gray-600 hover:text-gray-900'
          }`}
        >
          Output Payload
        </button>
      </div>

      {/* Basic Information */}
      <Card>
        <CardHeader>
          <CardTitle>
            {activeTab === 'input' ? 'Input' : 'Output'} Payload Schema
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div>
            <Label htmlFor="payload-name">Schema Name</Label>
            <Input
              id="payload-name"
              value={currentPayload.name}
              onChange={(e) => updatePayload({ name: e.target.value })}
              placeholder={`${activeTab} schema name`}
            />
          </div>
          <div>
            <Label htmlFor="payload-description">Description</Label>
            <Textarea
              id="payload-description"
              value={currentPayload.description}
              onChange={(e) => updatePayload({ description: e.target.value })}
              placeholder={`Describe the ${activeTab} payload structure`}
              rows={3}
            />
          </div>
        </CardContent>
      </Card>

      {/* Fields */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center justify-between">
            Schema Fields
            <Button onClick={addField} size="sm">
              <Plus className="w-4 h-4 mr-2" />
              Add Field
            </Button>
          </CardTitle>
        </CardHeader>
        <CardContent>
          {currentPayload.fields.length === 0 ? (
            <p className="text-gray-500 text-center py-8">
              No fields defined. Click "Add Field" to get started.
            </p>
          ) : (
            <div className="space-y-4">
              {currentPayload.fields.map((field, index) => (
                <div key={index} className="border rounded-lg p-4 space-y-4">
                  <div className="flex items-center justify-between">
                    <h4 className="font-medium">Field {index + 1}</h4>
                    <Button
                      onClick={() => removeField(index)}
                      size="sm"
                      variant="outline"
                    >
                      <Trash2 className="w-4 h-4" />
                    </Button>
                  </div>
                  
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <Label>Field Name</Label>
                      <Input
                        value={field.name}
                        onChange={(e) => updateField(index, { name: e.target.value })}
                        placeholder="field_name"
                      />
                    </div>
                    <div>
                      <Label>Type</Label>
                      <Select
                        value={field.type}
                        onValueChange={(value) => updateField(index, { type: value as PayloadField['type'] })}
                      >
                        <SelectTrigger>
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="string">String</SelectItem>
                          <SelectItem value="number">Number</SelectItem>
                          <SelectItem value="boolean">Boolean</SelectItem>
                          <SelectItem value="array">Array</SelectItem>
                          <SelectItem value="object">Object</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                  </div>

                  <div>
                    <Label>Description</Label>
                    <Textarea
                      value={field.description}
                      onChange={(e) => updateField(index, { description: e.target.value })}
                      placeholder="Describe this field"
                      rows={2}
                    />
                  </div>

                  <div className="flex items-center space-x-4">
                    <div className="flex items-center space-x-2">
                      <input
                        type="checkbox"
                        id={`required-${index}`}
                        checked={field.required}
                        onChange={(e) => updateField(index, { required: e.target.checked })}
                      />
                      <Label htmlFor={`required-${index}`}>Required</Label>
                    </div>
                    {field.required && (
                      <Badge variant="secondary">Required</Badge>
                    )}
                  </div>

                  <div>
                    <Label>Example Value</Label>
                    <Input
                      value={field.example ? JSON.stringify(field.example) : ''}
                      onChange={(e) => {
                        try {
                          const value = e.target.value ? JSON.parse(e.target.value) : undefined;
                          updateField(index, { example: value });
                        } catch {
                          // Keep the current value if parsing fails
                        }
                      }}
                      placeholder="Example value (JSON format)"
                    />
                  </div>

                  {field.type === 'string' && (
                    <div>
                      <Label>Allowed Values (Optional)</Label>
                      <Input
                        value={field.enum ? field.enum.join(', ') : ''}
                        onChange={(e) => {
                          const values = e.target.value.split(',').map(v => v.trim()).filter(v => v);
                          updateField(index, { enum: values.length > 0 ? values : undefined });
                        }}
                        placeholder="value1, value2, value3"
                      />
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Examples */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center justify-between">
            Example Payloads
            <div className="flex space-x-2">
              <Button
                onClick={() => {
                  const example = generateExample();
                  updatePayload({
                    examples: [...currentPayload.examples, example]
                  });
                }}
                size="sm"
                variant="outline"
              >
                Generate Example
              </Button>
              <Button
                onClick={() => setShowExamples(!showExamples)}
                size="sm"
                variant="outline"
              >
                <Eye className="w-4 h-4 mr-2" />
                {showExamples ? 'Hide' : 'Show'} Examples
              </Button>
            </div>
          </CardTitle>
        </CardHeader>
        {showExamples && (
          <CardContent>
            {currentPayload.examples.length === 0 ? (
              <p className="text-gray-500 text-center py-8">
                No examples defined. Click "Generate Example" to create one.
              </p>
            ) : (
              <div className="space-y-4">
                {currentPayload.examples.map((example, index) => (
                  <div key={index} className="border rounded-lg p-4">
                    <div className="flex items-center justify-between mb-2">
                      <h4 className="font-medium">Example {index + 1}</h4>
                      <div className="flex space-x-2">
                        <Button
                          onClick={() => copyExampleToClipboard(example)}
                          size="sm"
                          variant="outline"
                        >
                          <Copy className="w-4 h-4" />
                        </Button>
                        <Button
                          onClick={() => removeExample(index)}
                          size="sm"
                          variant="outline"
                        >
                          <Trash2 className="w-4 h-4" />
                        </Button>
                      </div>
                    </div>
                    <Textarea
                      value={JSON.stringify(example, null, 2)}
                      onChange={(e) => updateExample(index, e.target.value)}
                      rows={6}
                      className="font-mono text-sm"
                    />
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        )}
      </Card>

      {/* Schema Preview */}
      <Card>
        <CardHeader>
          <CardTitle>Schema Preview</CardTitle>
        </CardHeader>
        <CardContent>
          <pre className="bg-gray-100 p-4 rounded-lg text-sm overflow-x-auto">
            {JSON.stringify(currentPayload, null, 2)}
          </pre>
        </CardContent>
      </Card>
    </div>
  );
};

export default AgentPayloadForm;
