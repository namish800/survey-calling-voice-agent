# Webhook Tools - Dynamic API Templating

The Universal Agent supports dynamic webhook tools that allow you to define HTTP API calls directly in your agent configuration. These tools support Jinja2 templating with three namespaces for maximum flexibility.

## Overview

Webhook tools enable you to:
- Define HTTP API calls in your agent configuration
- Use templating to inject constants, context data, and LLM-supplied arguments
- Automatically generate function schemas for the LLM
- Handle responses and errors gracefully

## Configuration Schema

### ToolConfig for Webhooks

```json
{
  "id": "unique-tool-id",
  "name": "toolFunctionName",
  "description": "Description of what this tool does",
  "type": "webhook",
  "enabled": true,
  "consts": {
    "api_key": "your-api-key",
    "base_url": "https://api.example.com"
  },
  "api_spec": {
    "url": "{{const.base_url}}/users/{{ctx.customer_id}}/orders",
    "method": "POST",
    "headers": {
      "Authorization": "Bearer {{const.api_key}}",
      "Content-Type": "application/json"
    },
    "query": {
      "include": "details"
    },
    "body": {
      "item": "{{arg.item_name}}",
      "quantity": "{{arg.quantity}}",
      "note": "{{arg.special_instructions}}"
    },
    "llm_vars": [
      {
        "name": "item_name",
        "description": "Name of the item to order",
        "schema": {"type": "string", "minLength": 1},
        "required": true
      },
      {
        "name": "quantity", 
        "description": "Quantity to order",
        "schema": {"type": "integer", "minimum": 1},
        "required": true
      },
      {
        "name": "special_instructions",
        "description": "Special instructions for the order",
        "schema": {"type": "string", "maxLength": 200},
        "required": false
      }
    ]
  },
  "wait_for_result": true
}
```

## Template Namespaces

### 1. Constants (`const`)
Values defined in the `consts` field of the tool configuration.
- **Usage**: `{{const.api_key}}`, `{{const.base_url}}`
- **Purpose**: Store API keys, base URLs, and other static configuration

### 2. Context (`ctx`) 
Runtime context data available during the conversation.
- **Usage**: `{{ctx.customer_id}}`, `{{ctx.session_id}}`
- **Source**: Merged from RunContext.userdata and session data
- **Purpose**: Access conversation-specific data like user IDs, session state

### 3. Arguments (`arg`)
Parameters supplied by the LLM when calling the tool.
- **Usage**: `{{arg.item_name}}`, `{{arg.quantity}}`
- **Source**: LLM function call arguments
- **Purpose**: Dynamic values the LLM determines based on user input

## LLM Variables

The `llm_vars` array defines what parameters the LLM can provide:

```json
{
  "name": "parameter_name",
  "description": "Clear description for the LLM",
  "schema": {
    "type": "string|integer|number|boolean|array|object",
    "minLength": 1,
    "maxLength": 100,
    "minimum": 0,
    "maximum": 1000,
    "pattern": "^[A-Z]{2,3}$"
  },
  "required": true
}
```

The schema follows JSON Schema specification and helps the LLM provide correctly formatted data.

## Example Configurations

### 1. Simple GET Request

```json
{
  "id": "weather-api",
  "name": "getWeather",
  "description": "Get current weather for a city",
  "type": "webhook",
  "consts": {
    "api_key": "${WEATHER_API_KEY}"
  },
  "api_spec": {
    "url": "https://api.openweathermap.org/data/2.5/weather",
    "method": "GET",
    "query": {
      "q": "{{arg.city}}",
      "appid": "{{const.api_key}}",
      "units": "metric"
    },
    "llm_vars": [
      {
        "name": "city",
        "description": "City name to get weather for",
        "schema": {"type": "string", "minLength": 1},
        "required": true
      }
    ]
  }
}
```

### 2. POST with JSON Body

```json
{
  "id": "create-ticket",
  "name": "createSupportTicket", 
  "description": "Create a support ticket",
  "type": "webhook",
  "consts": {
    "api_key": "${SUPPORT_API_KEY}"
  },
  "api_spec": {
    "url": "https://api.support.com/tickets",
    "method": "POST",
    "headers": {
      "Authorization": "Bearer {{const.api_key}}",
      "Content-Type": "application/json"
    },
    "body": {
      "customer_id": "{{ctx.customer_id}}",
      "subject": "{{arg.subject}}",
      "description": "{{arg.description}}",
      "priority": "{{arg.priority}}",
      "created_by": "voice-agent"
    },
    "llm_vars": [
      {
        "name": "subject",
        "description": "Brief subject line for the ticket",
        "schema": {"type": "string", "maxLength": 100},
        "required": true
      },
      {
        "name": "description", 
        "description": "Detailed description of the issue",
        "schema": {"type": "string", "maxLength": 1000},
        "required": true
      },
      {
        "name": "priority",
        "description": "Priority level: low, medium, high, urgent",
        "schema": {
          "type": "string", 
          "enum": ["low", "medium", "high", "urgent"]
        },
        "required": false
      }
    ]
  }
}
```

## Environment Variable Support

Constants support environment variable expansion using `${VAR_NAME}` syntax:

```json
{
  "consts": {
    "api_key": "${EXTERNAL_API_KEY}",
    "base_url": "${API_BASE_URL:-https://api.default.com}"
  }
}
```

## Error Handling

Webhook tools return structured error responses:

```json
{
  "error": "HTTP 404: Resource not found"
}
```

Common error scenarios:
- **Template errors**: Missing variables, invalid syntax
- **HTTP errors**: 4xx/5xx status codes  
- **Network errors**: Timeouts, connection failures
- **Validation errors**: Invalid configuration

## Security

- Sensitive fields (containing `token`, `secret`, `key`, `password`) are automatically masked in logs
- Environment variables allow secure credential management
- Template validation prevents injection attacks

## Validation Rules

1. **No namespace overlap**: `const`, `ctx`, and `llm_vars` cannot share key names
2. **Valid HTTP methods**: Only GET, POST, PUT, PATCH, DELETE allowed
3. **Template syntax**: Must use valid Jinja2 syntax with supported namespaces
4. **Required fields**: URL and method are mandatory

## Usage in Agent Configuration

Add webhook tools to your agent's `tools` array:

```json
{
  "agent_id": "my-agent",
  "name": "My Agent",
  "llm_config": {...},
  "tools": [
    {
      "id": "weather-tool",
      "name": "getWeather",
      "type": "webhook",
      "api_spec": {...}
    },
    {
      "id": "booking-tool", 
      "name": "bookAppointment",
      "type": "webhook",
      "api_spec": {...}
    }
  ]
}
```

The agent will automatically register these tools and make them available to the LLM during conversations. 