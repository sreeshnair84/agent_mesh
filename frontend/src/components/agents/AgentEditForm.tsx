import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Badge } from '@/components/ui/Badge';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Save, TestTube, Eye, CheckCircle, XCircle } from 'lucide-react';
import AgentPayloadForm from './AgentPayloadForm';
import payloadService, { PayloadSchema, ValidationResult } from '@/lib/services/payload-service';

interface Agent {
  id: string;
  name: string;
  description: string;
  system_prompt: string;
  model_name: string;
  temperature: number;
  max_tokens: number;
  status: string;
  input_payload?: PayloadSchema;
  output_payload?: PayloadSchema;
}

interface AgentEditFormProps {
  agent?: Agent;
  onSave: (agent: Partial<Agent>) => void;
  onCancel: () => void;
  loading?: boolean;
}

const AgentEditForm: React.FC<AgentEditFormProps> = ({
  agent,
  onSave,
  onCancel,
  loading = false
}) => {
  const [formData, setFormData] = useState<Partial<Agent>>({
    name: '',
    description: '',
    system_prompt: '',
    model_name: 'gpt-4',
    temperature: 0.7,
    max_tokens: 4000,
    status: 'draft',
    input_payload: undefined,
    output_payload: undefined
  });

  const [validationResults, setValidationResults] = useState<{
    input?: ValidationResult;
    output?: ValidationResult;
  }>({});

  const [testData, setTestData] = useState({
    input: '',
    output: ''
  });

  const [showValidation, setShowValidation] = useState(false);

  useEffect(() => {
    if (agent) {
      setFormData(agent);
    }
  }, [agent]);

  const handleInputChange = (field: keyof Agent, value: any) => {
    setFormData(prev => ({
      ...prev,
      [field]: value
    }));
  };

  const handlePayloadChange = (type: 'input' | 'output', payload: PayloadSchema) => {
    const fieldName = type === 'input' ? 'input_payload' : 'output_payload';
    setFormData(prev => ({
      ...prev,
      [fieldName]: payload
    }));
  };

  const handleSave = async () => {
    try {
      // Validate payload schemas before saving
      const errors: string[] = [];

      if (formData.input_payload) {
        const inputValidation = payloadService.validatePayloadStructure(formData.input_payload);
        if (!inputValidation.valid) {
          errors.push(...inputValidation.errors.map(e => `Input payload: ${e}`));
        }
      }

      if (formData.output_payload) {
        const outputValidation = payloadService.validatePayloadStructure(formData.output_payload);
        if (!outputValidation.valid) {
          errors.push(...outputValidation.errors.map(e => `Output payload: ${e}`));
        }
      }

      if (errors.length > 0) {
        alert('Please fix the following errors:\n' + errors.join('\n'));
        return;
      }

      await onSave(formData);
    } catch (error) {
      console.error('Error saving agent:', error);
      alert('Failed to save agent. Please try again.');
    }
  };

  const handleValidatePayload = async (type: 'input' | 'output') => {
    if (!agent?.id) {
      alert('Please save the agent first before validating payloads');
      return;
    }

    try {
      const data = testData[type];
      if (!data) {
        alert(`Please enter ${type} data to validate`);
        return;
      }

      const parsedData = JSON.parse(data);
      const result = await payloadService.validatePayload(agent.id, parsedData, type);
      
      setValidationResults(prev => ({
        ...prev,
        [type]: result
      }));
      
      setShowValidation(true);
    } catch (error) {
      console.error('Validation error:', error);
      alert('Invalid JSON data or validation failed');
    }
  };

  const generateExamplePayload = (type: 'input' | 'output') => {
    const payload = type === 'input' ? formData.input_payload : formData.output_payload;
    if (!payload) return;

    const example: any = {};
    payload.fields.forEach(field => {
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

    setTestData(prev => ({
      ...prev,
      [type]: JSON.stringify(example, null, 2)
    }));
  };

  return (
    <div className="max-w-4xl mx-auto p-6 space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">
          {agent ? 'Edit Agent' : 'Create New Agent'}
        </h1>
        <div className="flex space-x-2">
          <Button onClick={onCancel} variant="outline">
            Cancel
          </Button>
          <Button onClick={handleSave} disabled={loading}>
            <Save className="w-4 h-4 mr-2" />
            {loading ? 'Saving...' : 'Save'}
          </Button>
        </div>
      </div>

      <Tabs defaultValue="basic" className="w-full">
        <TabsList className="grid w-full grid-cols-4">
          <TabsTrigger value="basic">Basic Info</TabsTrigger>
          <TabsTrigger value="configuration">Configuration</TabsTrigger>
          <TabsTrigger value="payload">Input/Output</TabsTrigger>
          <TabsTrigger value="testing">Testing</TabsTrigger>
        </TabsList>

        <TabsContent value="basic" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Basic Information</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <Label htmlFor="name">Agent Name</Label>
                <Input
                  id="name"
                  value={formData.name}
                  onChange={(e) => handleInputChange('name', e.target.value)}
                  placeholder="Enter agent name"
                />
              </div>
              <div>
                <Label htmlFor="description">Description</Label>
                <Textarea
                  id="description"
                  value={formData.description}
                  onChange={(e) => handleInputChange('description', e.target.value)}
                  placeholder="Describe what this agent does"
                  rows={3}
                />
              </div>
              <div>
                <Label htmlFor="system_prompt">System Prompt</Label>
                <Textarea
                  id="system_prompt"
                  value={formData.system_prompt}
                  onChange={(e) => handleInputChange('system_prompt', e.target.value)}
                  placeholder="Enter the system prompt for this agent"
                  rows={6}
                />
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="configuration" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Model Configuration</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <Label htmlFor="model_name">Model</Label>
                <Input
                  id="model_name"
                  value={formData.model_name}
                  onChange={(e) => handleInputChange('model_name', e.target.value)}
                  placeholder="gpt-4"
                />
              </div>
              <div>
                <Label htmlFor="temperature">Temperature</Label>
                <Input
                  id="temperature"
                  type="number"
                  min="0"
                  max="2"
                  step="0.1"
                  value={formData.temperature}
                  onChange={(e) => handleInputChange('temperature', parseFloat(e.target.value))}
                />
              </div>
              <div>
                <Label htmlFor="max_tokens">Max Tokens</Label>
                <Input
                  id="max_tokens"
                  type="number"
                  min="1"
                  max="32000"
                  value={formData.max_tokens}
                  onChange={(e) => handleInputChange('max_tokens', parseInt(e.target.value))}
                />
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="payload" className="space-y-4">
          <AgentPayloadForm
            inputPayload={formData.input_payload}
            outputPayload={formData.output_payload}
            onPayloadChange={handlePayloadChange}
          />
        </TabsContent>

        <TabsContent value="testing" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Payload Testing</CardTitle>
            </CardHeader>
            <CardContent className="space-y-6">
              {/* Input Testing */}
              <div>
                <div className="flex items-center justify-between mb-2">
                  <Label>Input Payload Testing</Label>
                  <div className="flex space-x-2">
                    <Button
                      onClick={() => generateExamplePayload('input')}
                      size="sm"
                      variant="outline"
                    >
                      Generate Example
                    </Button>
                    <Button
                      onClick={() => handleValidatePayload('input')}
                      size="sm"
                    >
                      <TestTube className="w-4 h-4 mr-2" />
                      Validate
                    </Button>
                  </div>
                </div>
                <Textarea
                  value={testData.input}
                  onChange={(e) => setTestData(prev => ({ ...prev, input: e.target.value }))}
                  placeholder="Enter JSON input data to test"
                  rows={8}
                  className="font-mono"
                />
                {validationResults.input && showValidation && (
                  <Alert className={validationResults.input.valid ? 'border-green-500' : 'border-red-500'}>
                    <div className="flex items-center">
                      {validationResults.input.valid ? (
                        <CheckCircle className="w-4 h-4 text-green-500" />
                      ) : (
                        <XCircle className="w-4 h-4 text-red-500" />
                      )}
                      <AlertDescription className="ml-2">
                        {validationResults.input.valid ? (
                          'Input payload is valid!'
                        ) : (
                          <div>
                            <p className="font-medium">Validation errors:</p>
                            <ul className="list-disc list-inside mt-1">
                              {validationResults.input.errors.map((error, index) => (
                                <li key={index}>{error}</li>
                              ))}
                            </ul>
                          </div>
                        )}
                      </AlertDescription>
                    </div>
                  </Alert>
                )}
              </div>

              {/* Output Testing */}
              <div>
                <div className="flex items-center justify-between mb-2">
                  <Label>Output Payload Testing</Label>
                  <div className="flex space-x-2">
                    <Button
                      onClick={() => generateExamplePayload('output')}
                      size="sm"
                      variant="outline"
                    >
                      Generate Example
                    </Button>
                    <Button
                      onClick={() => handleValidatePayload('output')}
                      size="sm"
                    >
                      <TestTube className="w-4 h-4 mr-2" />
                      Validate
                    </Button>
                  </div>
                </div>
                <Textarea
                  value={testData.output}
                  onChange={(e) => setTestData(prev => ({ ...prev, output: e.target.value }))}
                  placeholder="Enter JSON output data to test"
                  rows={8}
                  className="font-mono"
                />
                {validationResults.output && showValidation && (
                  <Alert className={validationResults.output.valid ? 'border-green-500' : 'border-red-500'}>
                    <div className="flex items-center">
                      {validationResults.output.valid ? (
                        <CheckCircle className="w-4 h-4 text-green-500" />
                      ) : (
                        <XCircle className="w-4 h-4 text-red-500" />
                      )}
                      <AlertDescription className="ml-2">
                        {validationResults.output.valid ? (
                          'Output payload is valid!'
                        ) : (
                          <div>
                            <p className="font-medium">Validation errors:</p>
                            <ul className="list-disc list-inside mt-1">
                              {validationResults.output.errors.map((error, index) => (
                                <li key={index}>{error}</li>
                              ))}
                            </ul>
                          </div>
                        )}
                      </AlertDescription>
                    </div>
                  </Alert>
                )}
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default AgentEditForm;
