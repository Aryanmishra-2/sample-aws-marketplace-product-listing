# Seller Registration Agent Refactoring Plan

## Current State
- Seller registration has embedded UI screens in streamlit app
- SellerRegistrationAgent exists but isn't fully integrated
- Registration logic is mixed with UI presentation

## Completed Changes
✅ Updated SellerRegistrationAgent to accept AWS credentials in __init__
✅ Added update_credentials() method to SellerRegistrationAgent
✅ Updated streamlit app to pass credentials to the agent when validated

## Remaining Work

### 1. Integrate with Workflow Orchestrator
- [ ] Add SellerRegistrationAgent to WorkflowOrchestrator
- [ ] Create workflow step for seller registration
- [ ] Define inputs/outputs for the registration step

### 2. Simplify Streamlit UI
- [ ] Remove embedded registration screens:
  - `seller_registration_screen()`
  - `registration_portal_screen()`
  - `registration_details_screen()`
- [ ] Replace with simple agent invocation
- [ ] Show agent progress/status in UI

### 3. Agent Communication
- [ ] Define clear interface for agent responses
- [ ] Handle agent errors gracefully in UI
- [ ] Display agent progress updates

### 4. Workflow Integration
```python
# Example workflow flow:
1. credentials_input_screen() -> Validate credentials
2. Call SellerRegistrationAgent.check_seller_status()
3. If NOT_REGISTERED:
   - Call SellerRegistrationAgent.process_stage() with user input
   - Display agent responses
   - Collect required information through agent
4. If APPROVED:
   - Proceed to product listing creation
```

### 5. Benefits of This Approach
- Separation of concerns (UI vs business logic)
- Reusable agent for other interfaces (CLI, API, etc.)
- Easier testing and maintenance
- Consistent with other agents in the system

## Implementation Steps

### Step 1: Create Agent Wrapper Function
```python
def run_seller_registration_agent(user_message: str) -> Dict[str, Any]:
    """
    Run seller registration agent with user input
    Returns agent response with status and next steps
    """
    agent = st.session_state.seller_registration_agent
    context = st.session_state.get('registration_context', {})
    
    response = agent.process_stage(user_message, context)
    
    # Update context
    st.session_state.registration_context = response.get('data', {})
    
    return response
```

### Step 2: Create Simple Registration UI
```python
def seller_registration_agent_screen():
    """Simple UI that interacts with seller registration agent"""
    st.title("🏢 Seller Registration")
    
    # Check status
    status = st.session_state.seller_registration_agent.check_seller_status()
    
    if status['seller_status'] == 'APPROVED':
        st.success("✅ Already registered!")
        # Proceed to next step
    else:
        # Show agent instructions
        instructions = st.session_state.seller_registration_agent.get_stage_instructions()
        st.info(instructions)
        
        # Chat interface with agent
        user_input = st.text_area("Provide your business information:")
        
        if st.button("Submit"):
            response = run_seller_registration_agent(user_input)
            
            if response['status'] == 'complete':
                st.success(response['message'])
                # Proceed to next step
            elif response['status'] == 'collecting':
                st.info(response['message'])
                st.write(response['next_question'])
            elif response['status'] == 'error':
                st.error(response['message'])
```

### Step 3: Update Main Flow
```python
def main():
    current_step = st.session_state.current_step
    
    if current_step == "credentials":
        credentials_input_screen()
    elif current_step == "seller_registration":
        seller_registration_agent_screen()  # New simplified screen
    elif current_step == "welcome":
        welcome_screen()
    # ... rest of flow
```

## Testing Plan
1. Test credential passing to agent
2. Test agent status checking
3. Test information collection flow
4. Test error handling
5. Test integration with rest of workflow

## Migration Strategy
1. Keep old screens temporarily with feature flag
2. Implement new agent-based flow
3. Test thoroughly
4. Remove old screens once validated
5. Update documentation
