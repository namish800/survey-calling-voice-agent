
# Universal Agent Configuration API - Requirements Document

## 📋 **Project Overview**

**Purpose:** Create a standalone REST API service for managing Universal Agent configurations with database persistence. The Universal Agent system will fetch configurations from this API via remote calls.

## 🎯 **Core Requirements**

### **1. Authentication & Security**
- **API Key Authentication:** `Authorization: Bearer <api-key>`
- **Multi-tenant Support:** `X-Tenant-ID: <tenant-id>` header
- **Rate Limiting:** 1000 requests/hour per API key
- **Input Validation:** All payloads must be validated
- **HTTPS Only:** All endpoints must use HTTPS

### **2. Database Requirements**
- **Primary Storage:** Agent configurations as JSON documents
- **Indexing:** Efficient queries by `agent_id`, `tenant_id`, `agent_type`
- **Timestamps:** `created_at`, `updated_at` for all records
- **Soft Deletes:** Mark as deleted rather than hard delete
- **Version History:** Optional audit trail of configuration changes

### **3. Core Functionality**
- **CRUD Operations:** Full Create, Read, Update, Delete for agent configs
- **Configuration Validation:** Validate agent config structure before saving
- **Provider Availability:** Check if configured AI providers are available
- **Bulk Operations:** Support for batch operations (future requirement)

## 🚀 **API Specification**

### **Base Configuration**
- **Base URL:** `https://api.yourdomain.com/v1`
- **Content-Type:** `application/json`
- **API Version:** v1 (versioned in URL path)

### **Authentication Headers**
```http
Authorization: Bearer <api-key>
X-Tenant-ID: <tenant-id>  # Optional for multi-tenancy
Content-Type: application/json
```

## 📋 **Detailed API Endpoints**

### **1. Agent Management**

#### **Create Agent**
```http
POST /api/v1/agents
```

**Request Body:**
```json
{
  "agent_id": "customer_support_v1",
  "name": "Customer Support Assistant",
  "description": "AI assistant for customer support",
  "agent_type": "assistant",
  "version": "1.0",
  
  "first_message": "Hello! How can I help you today?",
  "greeting_instructions": "Greet the user warmly",
  "system_instructions": "You are a helpful customer support assistant...",
  "guardrails": "Always be polite and professional...",
  "initial_context": "Customer support context...",
  
  "llm_config": {
    "provider": "openai",
    "model": "gpt-4o",
    "temperature": 0.7,
    "max_tokens": 1000,
    "api_key": "sk-...",
    "base_url": null,
    "custom_params": {}
  },
  
  "tts_config": {
    "provider": "elevenlabs",
    "voice_id": "21m00Tcm4TlvDq8ikWAM",
    "model": null,
    "language": "en",
    "speed": 1.0,
    "api_key": "your-elevenlabs-key",
    "custom_params": {}
  },
  
  "stt_config": {
    "provider": "deepgram",
    "language": "en",
    "model": "nova-2",
    "api_key": "your-deepgram-key",
    "custom_params": {}
  },
  
  "vad_config": {},
  "turn_detection_config": {},
  
  "rag_config": {
    "enabled": true,
    "namespace": "customer_docs"
  },
  
  "memory_config": {
    "enabled": true,
    "type": "user",
    "max_history": 50,
    "summarize_threshold": 100,
    "provider": null,
    "custom_params": {}
  },
  
  "tools": [
    {
      "id": "ticket_lookup",
      "name": "Ticket Lookup",
      "enabled": true,
      "async_execution": false,
      "description": "Look up customer support tickets",
      "type": "webhook",
      "api_spec": {
        "url": "https://api.yourcompany.com/tickets",
        "method": "POST",
        "headers": {
          "Authorization": "Bearer internal-token"
        },
        "body": null
      }
    }
  ],
  
  "evaluation_criteria": [
    {
      "name": "Helpfulness",
      "description": "How helpful was the response"
    }
  ],
  
  "evaluation_webhook": {
    "url": "https://your-webhook.com/evaluation",
    "headers": {},
    "timeout": 30,
    "retry_count": 3,
    "retry_delay": 1.0,
    "enabled": true
  },
  
  "metrics_webhook": {
    "url": "https://your-webhook.com/metrics",
    "headers": {},
    "timeout": 30,
    "retry_count": 3,
    "retry_delay": 1.0,
    "enabled": true
  },
  
  "completion_webhook": {
    "url": "https://your-webhook.com/completion",
    "headers": {},
    "timeout": 30,
    "retry_count": 3,
    "retry_delay": 1.0,
    "enabled": true
  },
  
  "max_conversation_duration": 1800,
  "silence_timeout": 30,
  "interruption_handling": true,
  "noise_cancellation": "BVC",
  
  "metadata": {
    "department": "customer_service",
    "region": "us-east"
  }
}
```

**Success Response (201):**
```json
{
  "success": true,
  "data": {
    "agent_id": "customer_support_v1",
    "message": "Agent created successfully",
    "created_at": "2024-01-15T10:30:00Z"
  }
}
```

**Error Response (400):**
```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Agent configuration is invalid",
    "details": [
      "llm_config.api_key is required",
      "system_instructions cannot be empty"
    ]
  }
}
```

#### **Get Agent by ID**
```http
GET /api/v1/agents/{agent_id}
```

**Success Response (200):**
```json
{
  "success": true,
  "data": {
    "agent_id": "customer_support_v1",
    "name": "Customer Support Assistant",
    "status": "active",
    "created_at": "2024-01-15T10:30:00Z",
    "updated_at": "2024-01-15T10:30:00Z",
    
    // Full configuration object (same structure as create request)
    "llm_config": { ... },
    "tts_config": { ... },
    // ... all configuration fields
  }
}
```

#### **List Agents**
```http
GET /api/v1/agents?limit=20&offset=0&type=assistant&status=active
```

**Query Parameters:**
- `limit` (optional): Number of results (default: 20, max: 100)
- `offset` (optional): Pagination offset (default: 0)
- `type` (optional): Filter by agent_type
- `status` (optional): Filter by status (active, inactive, deleted)
- `search` (optional): Search in name/description

**Success Response (200):**
```json
{
  "success": true,
  "data": {
    "agents": [
      {
        "agent_id": "customer_support_v1",
        "name": "Customer Support Assistant",
        "description": "AI assistant for customer support",
        "agent_type": "assistant",
        "status": "active",
        "created_at": "2024-01-15T10:30:00Z",
        "updated_at": "2024-01-15T10:30:00Z",
        "version": "1.0"
      }
    ],
    "pagination": {
      "total": 1,
      "limit": 20,
      "offset": 0,
      "has_more": false
    }
  }
}
```

#### **Update Agent**
```http
PUT /api/v1/agents/{agent_id}
```

**Request Body:** Same structure as create (full configuration object)

**Success Response (200):**
```json
{
  "success": true,
  "data": {
    "agent_id": "customer_support_v1",
    "message": "Agent updated successfully",
    "updated_at": "2024-01-15T11:30:00Z"
  }
}
```

#### **Delete Agent**
```http
DELETE /api/v1/agents/{agent_id}
```

**Success Response (200):**
```json
{
  "success": true,
  "data": {
    "agent_id": "customer_support_v1",
    "message": "Agent deleted successfully",
    "deleted_at": "2024-01-15T12:30:00Z"
  }
}
```

### **2. Agent Operations**

#### **Validate Agent Configuration**
```http
POST /api/v1/agents/{agent_id}/validate
```

**Success Response (200):**
```json
{
  "success": true,
  "data": {
    "validation": {
      "valid": true,
      "errors": [],
      "warnings": [
        "TTS voice_id not verified with provider"
      ]
    },
    "provider_checks": {
      "llm": {
        "provider": "openai",
        "available": true,
        "model_exists": true
      },
      "tts": {
        "provider": "elevenlabs",
        "available": true,
        "voice_exists": false
      },
      "stt": {
        "provider": "deepgram",
        "available": true
      }
    }
  }
}
```

#### **Clone Agent**
```http
POST /api/v1/agents/{agent_id}/clone
```

**Request Body:**
```json
{
  "new_agent_id": "customer_support_v2",
  "name": "Customer Support V2",
  "modifications": {
    "llm_config.model": "gpt-4o-mini",
    "first_message": "Hi there! How can I assist you?"
  }
}
```

### **3. System Endpoints**

#### **Provider Information**
```http
GET /api/v1/providers
```

**Success Response (200):**
```json
{
  "success": true,
  "data": {
    "providers": {
      "llm": {
        "openai": {
          "available": true,
          "models": ["gpt-4o", "gpt-4", "gpt-3.5-turbo"],
          "configured": true
        },
        "anthropic": {
          "available": false,
          "reason": "API key not configured",
          "configured": false
        }
      },
      "tts": {
        "elevenlabs": {
          "available": true,
          "configured": true
        },
        "cartesia": {
          "available": true,
          "configured": true
        }
      },
      "stt": {
        "deepgram": {
          "available": true,
          "configured": true
        }
      }
    }
  }
}
```

#### **Health Check**
```http
GET /api/v1/health
```

**Success Response (200):**
```json
{
  "success": true,
  "data": {
    "status": "healthy",
    "timestamp": "2024-01-15T10:30:00Z",
    "version": "1.0.0",
    "database": {
      "status": "connected",
      "response_time_ms": 15
    },
    "providers": {
      "checked": 5,
      "available": 3,
      "unavailable": 2
    }
  }
}
```

## 🗄️ **Database Schema Requirements**

### **Primary Table: agents**
```sql
CREATE TABLE agents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    agent_id VARCHAR(255) NOT NULL,
    tenant_id VARCHAR(255),
    name VARCHAR(500) NOT NULL,
    description TEXT,
    agent_type VARCHAR(100) DEFAULT 'assistant',
    version VARCHAR(50) DEFAULT '1.0',
    status VARCHAR(50) DEFAULT 'active',
    configuration JSONB NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    deleted_at TIMESTAMP WITH TIME ZONE NULL,
    
    UNIQUE(agent_id, tenant_id),
    INDEX idx_agents_tenant_id (tenant_id),
    INDEX idx_agents_agent_type (agent_type),
    INDEX idx_agents_status (status),
    INDEX idx_agents_created_at (created_at)
);
```

### **Secondary Table: api_keys**
```sql
CREATE TABLE api_keys (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    key_hash VARCHAR(255) NOT NULL UNIQUE,
    tenant_id VARCHAR(255),
    name VARCHAR(255),
    permissions JSONB DEFAULT '[]',
    rate_limit_per_hour INTEGER DEFAULT 1000,
    is_active BOOLEAN DEFAULT TRUE,
    last_used_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    expires_at TIMESTAMP WITH TIME ZONE,
    
    INDEX idx_api_keys_tenant_id (tenant_id),
    INDEX idx_api_keys_active (is_active)
);
```

## 🔒 **Security Requirements**

### **Authentication**
1. **API Key Format:** `ua_<environment>_<random_string>` (e.g., `ua_prod_7x9k2m8n5q1w3e4r`)
2. **Key Storage:** Hash API keys using bcrypt or similar
3. **Key Validation:** Validate on every request
4. **Key Expiration:** Support optional expiration dates

### **Authorization**
1. **Tenant Isolation:** Strict tenant data separation
2. **Permission Model:** Role-based permissions (read, write, delete)
3. **Rate Limiting:** Per API key rate limiting
4. **Audit Logging:** Log all API operations

### **Input Validation**
1. **Schema Validation:** Validate all JSON payloads against schema
2. **SQL Injection Prevention:** Use parameterized queries
3. **XSS Prevention:** Sanitize string inputs
4. **Size Limits:** Max payload size of 10MB

## 🚀 **Technical Requirements**

### **Performance**
- **Response Time:** < 200ms for GET requests, < 500ms for POST/PUT
- **Throughput:** Handle 1000 requests/second minimum
- **Database:** Connection pooling and query optimization
- **Caching:** Redis cache for frequently accessed configs

### **Reliability**
- **Uptime:** 99.9% uptime requirement
- **Error Handling:** Graceful error handling with proper HTTP codes
- **Database Transactions:** Atomic operations for data consistency
- **Backup Strategy:** Daily database backups with point-in-time recovery

### **Monitoring**
- **Logging:** Structured logging (JSON format)
- **Metrics:** API response times, error rates, throughput
- **Health Checks:** Database connectivity, external provider checks
- **Alerting:** Alert on high error rates or downtime

## 🔗 **Integration with Universal Agent**

### **Remote Configuration Loading**
The Universal Agent system will call this API to fetch configurations:

```python
# In Universal Agent - config_loader.py
async def load_config_from_remote(agent_id: str, tenant_id: str = None) -> Optional[AgentConfig]:
    headers = {
        "Authorization": f"Bearer {os.getenv('CONFIG_API_KEY')}",
        "Content-Type": "application/json"
    }
    
    if tenant_id:
        headers["X-Tenant-ID"] = tenant_id
    
    async with aiohttp.ClientSession() as session:
        async with session.get(
            f"{CONFIG_API_BASE_URL}/api/v1/agents/{agent_id}",
            headers=headers
        ) as response:
            if response.status == 200:
                data = await response.json()
                return AgentConfig.from_dict(data["data"])
            return None
```

### **Configuration Sync**
- **Real-time Updates:** Universal Agent polls for config changes
- **Webhook Notifications:** Optional webhooks when configs change
- **Caching Strategy:** Universal Agent caches configs locally with TTL

## 📦 **Implementation Technology Stack**

### **Recommended Stack**
- **Framework:** FastAPI (Python) or Express.js (Node.js)
- **Database:** PostgreSQL with JSONB support
- **Cache:** Redis for configuration caching
- **Authentication:** JWT or API key middleware
- **Validation:** Pydantic (Python) or Joi (Node.js)
- **Documentation:** Auto-generated OpenAPI/Swagger docs

### **Deployment**
- **Containerization:** Docker containers
- **Orchestration:** Kubernetes or Docker Compose
- **Load Balancer:** NGINX or cloud load balancer
- **SSL:** Let's Encrypt or cloud SSL certificates

## ✅ **Success Criteria**

1. **Functional:** All CRUD operations work correctly
2. **Performance:** API responds within SLA requirements
3. **Security:** Authentication and authorization working
4. **Integration:** Universal Agent can fetch configs successfully
5. **Reliability:** API maintains 99.9% uptime
6. **Documentation:** Complete API documentation available

## 📋 **Implementation Phases**

### **Phase 1: MVP (Week 1-2)**
- Basic CRUD endpoints
- Database setup
- API key authentication
- Basic validation

### **Phase 2: Enhancement (Week 3)**
- Multi-tenancy support
- Provider availability checks
- Enhanced error handling
- Rate limiting

### **Phase 3: Production Ready (Week 4)**
- Monitoring and logging
- Performance optimization
- Security hardening
- Documentation completion

---

**This document provides the complete specification for implementing the Universal Agent Configuration API. The development team can use this to build a production-ready service that integrates seamlessly with your Universal Agent system.**
