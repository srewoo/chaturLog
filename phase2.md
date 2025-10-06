# Phase 2: Third-Party Log Provider Integration 🔌

## Overview
Integrate ChaturLog with popular log aggregation and monitoring platforms to enable direct log analysis without manual file uploads. Users can connect their logging infrastructure and analyze logs in real-time.

---

## 🎯 Goals

1. **Seamless Integration**: Connect to enterprise logging platforms
2. **Zero File Management**: No manual downloads/uploads required
3. **Real-time Analysis**: Query logs directly from source
4. **Multi-Provider Support**: Support major logging platforms
5. **Secure Authentication**: Safe handling of API credentials
6. **Flexible Querying**: Time-based and service-based filtering

---

## 📊 Supported Platforms (Priority Order)

### **1. Datadog** (High Priority)
- **Why**: Most popular APM/logging platform, excellent API
- **API**: REST API with comprehensive log query capabilities
- **Auth**: API Key + App Key
- **Features**:
  - Query logs by service, environment, timestamp
  - Filter by severity, status, tags
  - Support for log indexes
  - Real-time log streaming

### **2. Splunk** (High Priority)
- **Why**: Enterprise standard for log management
- **API**: REST API with powerful search capabilities
- **Auth**: Bearer Token or Username/Password
- **Features**:
  - SPL (Search Processing Language) queries
  - Index-based searching
  - Time range filtering
  - Field extraction

### **3. Grafana Loki** (Medium Priority)
- **Why**: Open-source, growing adoption, simple API
- **API**: LogQL queries via HTTP API
- **Auth**: Basic Auth or API Key
- **Features**:
  - Label-based log queries
  - Time range selection
  - Stream filtering
  - Regex pattern matching

### **4. Elasticsearch/ELK** (Medium Priority)
- **Why**: Widely used for log storage and analysis
- **API**: Elasticsearch Query DSL
- **Auth**: API Key or Basic Auth
- **Features**:
  - Full-text search
  - Complex aggregations
  - Index pattern matching
  - Time-based queries

### **5. AWS CloudWatch Logs** (Medium Priority)
- **Why**: Standard for AWS infrastructure
- **API**: AWS SDK / CloudWatch Logs API
- **Auth**: AWS Access Key + Secret Key
- **Features**:
  - Log group and stream queries
  - Filter pattern matching
  - Time range filtering
  - Cross-account access

### **6. Azure Monitor Logs** (Low Priority)
- **Why**: Standard for Azure infrastructure
- **API**: Kusto Query Language (KQL) via REST
- **Auth**: Azure AD credentials or API key
- **Features**:
  - Workspace-based queries
  - KQL query support
  - Resource-based filtering

---

## 🏗️ Technical Architecture

### **Database Schema Changes**

```sql
-- Log Provider Credentials Table
CREATE TABLE IF NOT EXISTS log_providers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    provider_type TEXT NOT NULL,  -- 'datadog', 'splunk', 'loki', etc.
    provider_name TEXT NOT NULL,  -- User-defined name (e.g., "Production Datadog")
    api_key TEXT NOT NULL,        -- Encrypted
    additional_config JSON,        -- Provider-specific config (app_key, region, etc.)
    is_active BOOLEAN DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- Log Provider Query History
CREATE TABLE IF NOT EXISTS provider_queries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    analysis_id INTEGER NOT NULL,
    provider_id INTEGER NOT NULL,
    service_name TEXT,
    start_time TIMESTAMP,
    end_time TIMESTAMP,
    query_params JSON,
    logs_fetched INTEGER,
    FOREIGN KEY (analysis_id) REFERENCES analyses(id),
    FOREIGN KEY (provider_id) REFERENCES log_providers(id)
);
```

### **Backend Services Structure**

```
backend/services/providers/
├── __init__.py
├── base_provider.py          # Abstract base class
├── datadog_provider.py       # Datadog implementation
├── splunk_provider.py        # Splunk implementation
├── loki_provider.py          # Loki implementation
├── elasticsearch_provider.py # Elasticsearch implementation
├── cloudwatch_provider.py    # AWS CloudWatch implementation
└── azure_monitor_provider.py # Azure Monitor implementation
```

---

## 🎨 User Experience Flow

### **Step 1: Configure Provider (Settings)**

**Settings → Log Providers Tab**

```
┌─────────────────────────────────────────┐
│ 🔌 Log Provider Integrations            │
├─────────────────────────────────────────┤
│                                          │
│ [+ Add New Provider]                    │
│                                          │
│ Connected Providers:                    │
│                                          │
│ ┌──────────────────────────────────┐   │
│ │ 📊 Production Datadog             │   │
│ │ Status: ✅ Connected              │   │
│ │ Services: 12 discovered           │   │
│ │ [Edit] [Test] [Remove]            │   │
│ └──────────────────────────────────┘   │
│                                          │
│ ┌──────────────────────────────────┐   │
│ │ 🔍 Staging Splunk                 │   │
│ │ Status: ✅ Connected              │   │
│ │ Indexes: 5 available              │   │
│ │ [Edit] [Test] [Remove]            │   │
│ └──────────────────────────────────┘   │
└─────────────────────────────────────────┘
```

**Provider Configuration Form:**

```
┌─────────────────────────────────────────┐
│ Add Datadog Provider                     │
├─────────────────────────────────────────┤
│                                          │
│ Provider Name: [Production Datadog    ] │
│                                          │
│ API Key: [••••••••••••••••••••••••••••] │
│                                          │
│ App Key: [••••••••••••••••••••••••••••] │
│                                          │
│ Region: [US1 ▼]                         │
│  Options: US1, US3, US5, EU1, AP1       │
│                                          │
│ [Test Connection]  [Cancel]  [Save]     │
└─────────────────────────────────────────┘
```

### **Step 2: Query Logs (Dashboard)**

**Dashboard → New "Provider Logs" Tab**

```
┌─────────────────────────────────────────────────┐
│ 📡 Query Logs from Provider                      │
├─────────────────────────────────────────────────┤
│                                                   │
│ Provider: [Production Datadog ▼]                │
│                                                   │
│ Service: [api-gateway ▼]                         │
│  • api-gateway (12,453 logs/hour)                │
│  • user-service (8,234 logs/hour)                │
│  • payment-service (5,123 logs/hour)             │
│                                                   │
│ Time Range:                                      │
│  ○ Last 1 hour     ○ Last 6 hours               │
│  ○ Last 24 hours   ● Custom Range               │
│                                                   │
│  From: [2025-10-06 10:00] To: [2025-10-06 14:00]│
│                                                   │
│ Environment: [production ▼] (optional)           │
│                                                   │
│ Severity Filter: [All ▼]                        │
│  Options: All, ERROR, WARN, INFO                 │
│                                                   │
│ Advanced:                                        │
│  Additional Query: [status:error AND ...     ]  │
│                                                   │
│ [Fetch & Analyze Logs] 🚀                       │
└─────────────────────────────────────────────────┘
```

### **Step 3: Analysis Results**

Same as current analysis flow, but with metadata showing:
- Provider: Datadog
- Service: api-gateway
- Time Range: 2025-10-06 10:00 - 14:00
- Logs Analyzed: 1,234 entries

---

## 🔧 Implementation Details

### **Phase 2.1: Foundation (Week 1)**

**Backend:**
1. Create database tables for log providers
2. Implement `BaseLogProvider` abstract class
3. Add encryption for API keys (Fernet/AES)
4. Create Settings API endpoints:
   - `POST /api/providers` - Add provider
   - `GET /api/providers` - List providers
   - `PUT /api/providers/{id}` - Update provider
   - `DELETE /api/providers/{id}` - Delete provider
   - `POST /api/providers/{id}/test` - Test connection

**Frontend:**
1. Create "Log Providers" tab in Settings
2. Add provider configuration form
3. Display connected providers list

### **Phase 2.2: Datadog Integration (Week 2)**

**Backend:**
1. Install `datadog-api-client` package
2. Implement `DatadogProvider` class:
   ```python
   class DatadogProvider(BaseLogProvider):
       def fetch_logs(self, service, start_time, end_time, filters):
           # Query logs from Datadog API
           # Return standardized log format
       
       def list_services(self):
           # Discover available services
       
       def test_connection(self):
           # Validate credentials
   ```
3. Add provider query endpoint:
   - `POST /api/providers/{id}/query` - Fetch logs

**Frontend:**
1. Add "Provider Logs" tab to Dashboard
2. Implement query form with:
   - Provider selection
   - Service dropdown (fetched from provider)
   - Time range picker
   - Environment/tag filters
3. Show fetched logs count and estimated time

### **Phase 2.3: Additional Providers (Week 3-4)**

**Splunk Integration:**
```python
class SplunkProvider(BaseLogProvider):
    def fetch_logs(self, index, search_query, start_time, end_time):
        # Use Splunk REST API
        # Convert SPL results to standard format
```

**Loki Integration:**
```python
class LokiProvider(BaseLogProvider):
    def fetch_logs(self, label_query, start_time, end_time):
        # Use LogQL query API
        # Stream and aggregate results
```

**Elasticsearch Integration:**
```python
class ElasticsearchProvider(BaseLogProvider):
    def fetch_logs(self, index_pattern, query_dsl, start_time, end_time):
        # Use Elasticsearch client
        # Handle pagination for large result sets
```

### **Phase 2.4: Enhanced Features (Week 5)**

1. **Auto-refresh**: Periodic log fetching for monitoring
2. **Saved Queries**: Save frequently used queries
3. **Scheduled Analysis**: Automatically analyze logs at intervals
4. **Alerts**: Notify when critical patterns detected
5. **Service Discovery**: Auto-detect services from providers
6. **Multi-Service Analysis**: Analyze logs from multiple services

---

## 🔐 Security Considerations

### **API Key Storage**
- Encrypt all API keys using Fernet (symmetric encryption)
- Store encryption key in environment variable
- Never expose keys in API responses (show masked versions)

### **Connection Security**
- Use HTTPS for all provider API calls
- Validate SSL certificates
- Implement request timeouts
- Rate limiting for API calls

### **Access Control**
- Provider configurations are user-specific
- Cannot access other users' provider configs
- Audit log for provider access

---

## 📈 Benefits

### **For Users**
- ✅ No manual log downloads
- ✅ Real-time log analysis
- ✅ Centralized log intelligence
- ✅ Historical trend analysis
- ✅ Multi-environment support

### **For Teams**
- ✅ Standardized test generation across services
- ✅ Faster incident response
- ✅ Better visibility into production issues
- ✅ Automated quality assurance

---

## 🧪 Testing Strategy

### **Provider Integration Tests**
```python
# tests/test_providers.py

def test_datadog_connection():
    provider = DatadogProvider(api_key="test", app_key="test")
    assert provider.test_connection() == True

def test_datadog_fetch_logs():
    provider = DatadogProvider(...)
    logs = provider.fetch_logs(
        service="api-gateway",
        start_time="2025-10-06T10:00:00Z",
        end_time="2025-10-06T14:00:00Z"
    )
    assert len(logs) > 0
    assert logs[0].has_key('timestamp')
    assert logs[0].has_key('message')

def test_splunk_search():
    provider = SplunkProvider(...)
    logs = provider.fetch_logs(
        index="main",
        search_query="error",
        start_time="-1h"
    )
    assert logs is not None
```

### **Integration Test Plan**
1. Mock provider APIs for unit tests
2. Use test credentials for integration tests
3. Test rate limiting and error handling
4. Verify log format standardization
5. Test large result set pagination

---

## 📊 API Examples

### **Datadog Query**
```python
POST /api/providers/1/query
{
  "service": "api-gateway",
  "start_time": "2025-10-06T10:00:00Z",
  "end_time": "2025-10-06T14:00:00Z",
  "environment": "production",
  "severity": "error",
  "limit": 1000
}

Response:
{
  "success": true,
  "provider": "datadog",
  "logs_count": 234,
  "analysis_id": 45,
  "message": "Logs fetched and queued for analysis"
}
```

### **Splunk Query**
```python
POST /api/providers/2/query
{
  "index": "main",
  "search": "error status=500",
  "earliest_time": "-24h",
  "latest_time": "now",
  "limit": 500
}
```

---

## 🚀 Rollout Plan

### **Week 1-2: Foundation + Datadog**
- Core infrastructure
- Datadog integration
- Basic UI

### **Week 3: Splunk + Loki**
- Splunk implementation
- Loki implementation
- Enhanced UI

### **Week 4: Testing + Polish**
- Comprehensive testing
- Documentation
- Error handling improvements

### **Week 5: Additional Features**
- Scheduled analysis
- Saved queries
- Service discovery

---

## 💡 Future Enhancements

1. **Real-time Monitoring**: WebSocket-based live log streaming
2. **Anomaly Detection**: ML-based pattern detection
3. **Cross-Provider Analysis**: Compare logs across multiple providers
4. **Custom Dashboards**: User-defined monitoring dashboards
5. **Slack/Teams Integration**: Send alerts to team channels
6. **CI/CD Integration**: Analyze logs from deployment pipelines
7. **Log Correlation**: Link related logs across services

---

## 📝 Notes

- Start with Datadog (most requested, best API)
- Keep provider implementations modular
- Design for extensibility (easy to add new providers)
- Consider rate limits for each provider
- Implement caching for service/index lists
- Add progress indicators for long queries
- Support pagination for large result sets

---

**Estimated Total Effort**: 4-5 weeks for core implementation
**Priority**: High (enterprise feature request)
**Dependencies**: Phase 1 completion, secure credential storage
