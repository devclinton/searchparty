# Security Considerations

## OWASP Top 10 Checklist

### 1. Injection
- All database queries use parameterized SQL via asyncpg
- No string interpolation in SQL queries
- Input validated via Pydantic models before reaching DB layer

### 2. Broken Authentication
- JWT tokens with short expiry (30 min access, 7 day refresh)
- bcrypt password hashing with random salt
- Rate limiting on auth endpoints (10/min login, 5/5min register)
- OAuth for third-party authentication (no password storage for OAuth users)

### 3. Sensitive Data Exposure
- Subject personal data encrypted at rest (database-level encryption)
- Auto-purge of subject data after configurable retention period
- HTTPS required for all API communication
- No sensitive data in URL parameters

### 4. XML External Entities (XXE)
- No XML parsing in the application
- GPX export generates XML, does not parse external XML

### 5. Broken Access Control
- ICS role-based access control on all endpoints
- Role verification per incident via team_members table
- Incident Commander-only operations for status changes

### 6. Security Misconfiguration
- Production secret key must be changed from default
- CORS restricted to known origins
- Debug mode disabled in production
- Security headers via reverse proxy

### 7. Cross-Site Scripting (XSS)
- React auto-escapes rendered content
- No dangerouslySetInnerHTML usage
- Content Security Policy headers recommended

### 8. Insecure Deserialization
- Pydantic models validate all input types
- No pickle or unsafe deserialization

### 9. Using Components with Known Vulnerabilities
- Automated dependency scanning via GitHub Dependabot
- Regular dependency updates

### 10. Insufficient Logging & Monitoring
- Structured logging on all API endpoints
- Failed authentication attempts logged
- Health check endpoint for monitoring

## Data Privacy

### Subject Data
- Subject personal information (name, medical needs, clothing) is sensitive
- Role-based access: only incident participants can view subject data
- Auto-purge after incident closure + retention period
- GPS tracks of searchers may be discoverable in litigation

### GDPR Compliance
- Account deletion endpoint (soft delete)
- Data export endpoint
- Consent tracked at registration

### HIPAA Considerations
- If medical information is stored, ensure database encryption at rest
- Access logging for medical fields
- Consider separate storage for medical data with stricter access controls
