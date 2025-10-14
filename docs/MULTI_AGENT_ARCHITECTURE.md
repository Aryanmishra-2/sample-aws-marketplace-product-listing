# Multi-Agent Architecture for AWS Marketplace Listing Creation

## Overview

The system uses a **Master-Subordinate** multi-agent architecture with one orchestrator and 8 specialized sub-agents, each responsible for a specific stage of the SaaS listing creation workflow.

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                     USER INTERFACE                               │
│                  (Streamlit / CLI / API)                         │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                  MASTER ORCHESTRATOR                             │
│                                                                  │
│  Responsibilities:                                               │
│  - Workflow state management                                     │
│  - Stage sequencing and transitions                              │
│  - Progress tracking (1-8 stages)                                │
│  - Data aggregation across stages                                │
│  - Routing to appropriate sub-agent                              │
│  - Context maintenance                                           │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
              ┌──────────────┴──────────────┐
              │                             │
              ▼                             ▼
┌─────────────────────────┐   ┌─────────────────────────┐
│  Stage 1: Product Info  │   │  Stage 2: Fulfillment   │
│  ProductInformationAgent│   │  FulfillmentAgent       │
│                         │   │                         │
│  - Title, descriptions  │   │  - Fulfillment URL      │
│  - Logo, highlights     │   │  - Quick Launch         │
│  - Support, categories  │   │                         │
└─────────────────────────┘   └─────────────────────────┘
              │                             │
              ▼                             ▼
┌─────────────────────────┐   ┌─────────────────────────┐
│  Stage 3: Pricing Config│   │  Stage 4: Price Review  │
│  PricingConfigAgent     │   │  PriceReviewAgent       │
│                         │   │                         │
│  - Pricing model        │   │  - Purchasing options   │
│  - Dimensions           │   │  - Contract durations   │
│  - API identifiers      │   │  - Test pricing         │
└─────────────────────────┘   └─────────────────────────┘
              │                             │
              ▼                             ▼
┌─────────────────────────┐   ┌─────────────────────────┐
│  Stage 5: Refund Policy │   │  Stage 6: EULA Config   │
│  RefundPolicyAgent      │   │  EULAConfigAgent        │
│                         │   │                         │
│  - Refund terms         │   │  - SCMP vs Custom       │
│  - Policy text          │   │  - Custom EULA URL      │
└─────────────────────────┘   └─────────────────────────┘
              │                             │
              ▼                             ▼
┌─────────────────────────┐   ┌─────────────────────────┐
│  Stage 7: Availability  │   │  Stage 8: Allowlist     │
│  OfferAvailabilityAgent │   │  AllowlistAgent         │
│                         │   │                         │
│  - Geographic scope     │   │  - Account IDs          │
│  - Country restrictions │   │  - (Optional)           │
└─────────────────────────┘   └─────────────────────────┘
              │                             │
              └──────────────┬──────────────┘
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    DATA AGGREGATION                              │
│                                                                  │
│  All stage data combined into complete listing specification    │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│              AWS MARKETPLACE CATALOG API                         │
│                                                                  │
│  - CreateProduct + CreateOffer                                   │
│  - UpdateInformation                                             │
│  - AddDeliveryOptions                                            │
│  - UpdatePricingTerms                                            │
│  - Configure EULA, Refund Policy, Availability                   │
└─────────────────────────────────────────────────────────────────┘
```

## Component Details

### Master Orchestrator

**File:** `agent/orchestrator.py`

**Responsibilities:**
- Maintains workflow state (current stage, completed stages)
- Routes user messages to appropriate sub-agent
- Manages stage transitions
- Tracks progress (percentage, stage count)
- Aggregates data from all stages
- Provides workflow summary

**Key Methods:**
```python
process_message(user_message, context) -> response
get_current_agent() -> SubAgent
get_progress_percentage() -> int
get_workflow_summary() -> str
skip_stage(stage) -> bool
go_to_stage(stage) -> bool
reset_workflow()
export_data() -> dict
import_data(data) -> bool
```

**State Management:**
```python
{
    "current_stage": WorkflowStage.PRODUCT_INFO,
    "completed_stages": {Stage1, Stage2, ...},
    "all_data": {
        "PRODUCT_INFO": {...},
        "FULFILLMENT": {...},
        ...
    }
}
```

### Base Sub-Agent

**File:** `agent/sub_agents/base_agent.py`

**Abstract Base Class** for all sub-agents providing:
- Field validation framework
- Progress tracking
- Common utilities
- Standardized interface

**Required Methods (implemented by each sub-agent):**
```python
get_required_fields() -> List[str]
get_optional_fields() -> List[str]
get_field_validations() -> Dict[str, Dict]
get_stage_instructions() -> str
process_stage(user_input, context) -> Dict
```

**Validation Framework:**
- Type validation (string, integer, array, boolean)
- Length validation (min/max)
- Pattern validation (regex)
- Array size validation
- Custom validation rules

### Sub-Agents

#### 1. ProductInformationAgent
**Stage:** 1  
**Required Fields:** 9 (title, logo, descriptions, support, categories, keywords)  
**Optional Fields:** 8 (SKU, video, additional highlights, resources)  
**Complexity:** High (most fields)  
**Estimated Time:** 5-10 minutes

#### 2. FulfillmentAgent
**Stage:** 2  
**Required Fields:** 1 (fulfillment_url)  
**Optional Fields:** 2 (quick_launch, launch_url)  
**Complexity:** Low  
**Estimated Time:** 2-3 minutes

#### 3. PricingConfigAgent
**Stage:** 3  
**Required Fields:** 2 (pricing_model, dimensions)  
**Optional Fields:** 1 (free_trial_days)  
**Complexity:** High (dimension creation)  
**Estimated Time:** 5-10 minutes  
**Special Features:**
- Explains pricing models
- Helps create dimensions
- Auto-generates API IDs from display names
- Validates dimension uniqueness

#### 4. PriceReviewAgent
**Stage:** 4  
**Required Fields:** 2 (purchasing_option, contract_durations)  
**Optional Fields:** 0  
**Complexity:** Medium  
**Estimated Time:** 3-5 minutes  
**Note:** Sets test pricing at $0.001

#### 5. RefundPolicyAgent
**Stage:** 5  
**Required Fields:** 1 (refund_policy)  
**Optional Fields:** 0  
**Complexity:** Low  
**Estimated Time:** 2-3 minutes

#### 6. EULAConfigAgent
**Stage:** 6  
**Required Fields:** 1 (eula_type)  
**Optional Fields:** 1 (custom_eula_s3_url)  
**Complexity:** Low  
**Estimated Time:** 2-3 minutes  
**Special Features:**
- Explains SCMP vs Custom EULA
- Validates S3 URL for custom EULA

#### 7. OfferAvailabilityAgent
**Stage:** 7  
**Required Fields:** 1 (availability_type)  
**Optional Fields:** 2 (excluded_countries, allowed_countries)  
**Complexity:** Medium  
**Estimated Time:** 2-3 minutes  
**Special Features:**
- Explains geographic options
- Validates country codes (ISO 3166-1 alpha-2)

#### 8. AllowlistAgent
**Stage:** 8  
**Required Fields:** 0 (fully optional)  
**Optional Fields:** 1 (allowlist_account_ids)  
**Complexity:** Low  
**Estimated Time:** 1-2 minutes  
**Note:** Can be skipped entirely

## Workflow Flow

### Sequential Processing

```
User starts → Orchestrator initializes → Stage 1

Stage 1 (Product Info):
  ├─ Collect required fields (9)
  ├─ Validate each field
  ├─ Offer optional fields (8)
  ├─ Final validation
  └─ Mark complete → Transition to Stage 2

Stage 2 (Fulfillment):
  ├─ Collect fulfillment URL
  ├─ Validate URL format
  ├─ Offer Quick Launch
  └─ Mark complete → Transition to Stage 3

Stage 3 (Pricing Config):
  ├─ Choose pricing model
  ├─ Create dimensions (1-24)
  │   ├─ Select dimension type
  │   ├─ Generate/provide API ID
  │   ├─ Provide display name
  │   └─ Provide description
  ├─ Validate all dimensions
  └─ Mark complete → Transition to Stage 4

Stage 4 (Price Review):
  ├─ Choose purchasing option
  ├─ Select contract durations
  ├─ Set test pricing ($0.001)
  └─ Mark complete → Transition to Stage 5

Stage 5 (Refund Policy):
  ├─ Collect refund policy text
  ├─ Validate length (50-5000 chars)
  └─ Mark complete → Transition to Stage 6

Stage 6 (EULA Config):
  ├─ Choose EULA type (SCMP/Custom)
  ├─ If Custom: collect S3 URL
  ├─ Validate URL if provided
  └─ Mark complete → Transition to Stage 7

Stage 7 (Offer Availability):
  ├─ Choose availability type
  ├─ If exclusions: collect country codes
  ├─ If allowlist: collect country codes
  ├─ Validate country codes
  └─ Mark complete → Transition to Stage 8

Stage 8 (Allowlist):
  ├─ Ask if allowlist needed
  ├─ If yes: collect account IDs
  ├─ Validate account IDs
  └─ Mark complete → Workflow Complete

Workflow Complete:
  ├─ Aggregate all data
  ├─ Generate summary
  ├─ Create AWS Marketplace listing
  └─ Provide confirmation
```

### State Transitions

```python
class WorkflowStage(Enum):
    PRODUCT_INFO = 1
    FULFILLMENT = 2
    PRICING_CONFIG = 3
    PRICE_REVIEW = 4
    REFUND_POLICY = 5
    EULA_CONFIG = 6
    OFFER_AVAILABILITY = 7
    ALLOWLIST = 8
    COMPLETE = 9
```

**Transition Rules:**
- Sequential progression (1 → 2 → 3 → ... → 8 → Complete)
- Can go back to previous stages
- Cannot skip required stages
- Can skip optional stages (Stage 8)
- Transition only when stage validation passes

## Data Flow

### Input Processing

```
User Message
    ↓
Orchestrator.process_message()
    ↓
Get current sub-agent
    ↓
SubAgent.process_stage(message, context)
    ↓
Extract/validate data
    ↓
Return response with status
    ↓
If complete: save data, transition
    ↓
Return to user with progress
```

### Data Structure

```python
{
    "PRODUCT_INFO": {
        "product_title": "CloudSync Pro",
        "logo_s3_url": "https://...",
        "short_description": "...",
        "long_description": "...",
        "highlight_1": "...",
        "support_email": "support@example.com",
        "support_description": "...",
        "categories": ["Developer Tools", "Storage"],
        "search_keywords": ["sync", "backup", "cloud"]
    },
    "FULFILLMENT": {
        "fulfillment_url": "https://app.example.com/signup"
    },
    "PRICING_CONFIG": {
        "pricing_model": "usage",
        "dimensions": [
            {
                "api_id": "users",
                "display_name": "Number of Users",
                "description": "Active users per month"
            }
        ]
    },
    "PRICE_REVIEW": {
        "purchasing_option": "multiple_dimensions",
        "contract_durations": ["1 month", "12 months"]
    },
    "REFUND_POLICY": {
        "refund_policy": "30-day money-back guarantee..."
    },
    "EULA_CONFIG": {
        "eula_type": "scmp"
    },
    "OFFER_AVAILABILITY": {
        "availability_type": "all_countries"
    },
    "ALLOWLIST": {
        "allowlist_account_ids": []
    }
}
```

## Validation

### Field-Level Validation

Each sub-agent defines validation rules:

```python
{
    "product_title": {
        "type": "string",
        "min_length": 5,
        "max_length": 255,
        "description": "Product name"
    },
    "logo_s3_url": {
        "type": "string",
        "pattern": r"^https://.*\.s3\..*\.amazonaws\.com/.*\.(png|jpg)$",
        "description": "S3 URL to logo"
    },
    "categories": {
        "type": "array",
        "min_items": 1,
        "max_items": 3,
        "description": "Product categories"
    }
}
```

### Stage-Level Validation

Before marking stage complete:
1. Check all required fields present
2. Validate each field individually
3. Check cross-field dependencies
4. Return errors if any validation fails

### Workflow-Level Validation

Before creating listing:
1. Verify all required stages complete
2. Check data consistency across stages
3. Validate against AWS Marketplace rules
4. Generate final validation report

## Benefits of Multi-Agent Architecture

### 1. Separation of Concerns
- Each agent focuses on one stage
- Clear responsibilities
- Easier to maintain and update

### 2. Reduced Complexity
- Smaller, focused agents vs one large agent
- Less prone to iteration loops
- Clearer logic flow

### 3. Better Validation
- Stage-specific validation rules
- Immediate feedback
- Prevents invalid data propagation

### 4. Improved User Experience
- Clear progress tracking
- Focused questions per stage
- Ability to go back and edit
- Resume from saved state

### 5. Maintainability
- Easy to add/remove stages
- Update individual agents independently
- Test stages in isolation
- Clear code organization

### 6. Scalability
- Can parallelize independent stages (future)
- Easy to add new features per stage
- Modular architecture

## Configuration

**File:** `config/multi_agent_config.yaml`

Key settings:
- Model selection (Claude 3.7 Sonnet recommended)
- Iteration limits per agent
- Validation rules
- Feature flags (auto-save, resume, etc.)
- Progress tracking options

## Integration with Existing System

The multi-agent system integrates with:

1. **Agentcore Runtime** - Each sub-agent uses runtime for LLM calls
2. **Agentcore Gateway** - Routes tool calls
3. **Agentcore Memory** - Persists conversation and workflow state
4. **Agentcore Identity** - Manages user sessions
5. **Listing Tools** - Executes AWS Marketplace API calls

## Future Enhancements

1. **Parallel Processing** - Process independent stages concurrently
2. **Smart Defaults** - Learn from previous listings
3. **Template System** - Pre-fill common configurations
4. **Validation Preview** - Show AWS validation before submission
5. **Draft Management** - Save/load multiple drafts
6. **Collaboration** - Multi-user workflow support
7. **Analytics** - Track completion rates, common issues
8. **AI Assistance** - Generate descriptions, suggest categories

## Testing Strategy

### Unit Tests
- Test each sub-agent independently
- Validate field validation logic
- Test state transitions

### Integration Tests
- Test orchestrator with sub-agents
- Test complete workflow
- Test error handling

### End-to-End Tests
- Simulate complete listing creation
- Test with real AWS API (sandbox)
- Verify data integrity

## Monitoring

Track:
- Stage completion rates
- Average time per stage
- Common validation errors
- User drop-off points
- API call success rates

## Summary

The multi-agent architecture provides a robust, maintainable, and user-friendly system for AWS Marketplace SaaS listing creation. By breaking the complex workflow into 8 focused stages, each managed by a specialized agent, we achieve better separation of concerns, clearer validation, and improved user experience.
