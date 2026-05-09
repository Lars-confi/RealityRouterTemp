# Test Plan: Sentiment Analysis & Feedback integration

## Overview
This plan outlines the tests required to cover the new sentiment analysis logic added to `reality-router/src/router/core.py`. We identified `test_mcp_routing.py` is the main suite to append to.

## Identified Test Gaps in `test_mcp_routing.py`
Currently, there is no explicit test coverage for the `assess_user_sentiment` method, nor is there coverage for the `/feedback` posting mechanism in Reality Check integration within `route_request`.

## Proposed Tests to Add

### 1. `test_assess_user_sentiment_insufficient_messages`
- **Objective**: Ensure the system gracefully skips sentiment assessment when there's no conversation history context.
- **Scenario**: Provide 1 or 0 messages in the `parameters["messages"]` list.
- **Expected Outcome**: `assess_user_sentiment` immediately returns `None` without invoking any LLM adapters.

### 2. `test_assess_user_sentiment_standard_flow` (Exactly 2 messages)
- **Objective**: Verify standard back-and-forth user follow-up triggers the specific "old-style" prompt.
- **Scenario**: 2 messages (Previous: Assistant, Current: User). Mock the LLM adapter response to securely return `"happy"`.
- **Expected Outcome**: Returns `"happy"`.

### 3. `test_assess_user_sentiment_agent_led_flow` (New Logic)
- **Objective**: Verify the new general-purpose sentiment logic for agent-led configurations (e.g. User asking questions to a Tool/System, or Agent asking User).
- **Scenario**: 2 messages where roles are not strictly (Assistant -> User), for example, (User -> Assistant). Mock the LLM adapter response to return `"unhappy"`. 
- **Expected Outcome**: Returns `"unhappy"` and executes through the new general style assessment block.

### 4. `test_assess_user_sentiment_fallback_indeterminate`
- **Objective**: Check that undefined or unrecognized model responses fallback to a safe `"indeterminate"` state.
- **Scenario**: Standard message flow. Mock LLM adapter to return random jargon (e.g., `"sure I will do that"`).
- **Expected Outcome**: System parses and identifies lack of clear happy/unhappy output, resulting in `"indeterminate"`.

### 5. `test_integration_reality_check_feedback_loop`
- **Objective**: Test the end-to-end integration mapping the outcome of `assess_user_sentiment` to a Database Reality Check update and outbound REST API trigger.
- **Scenario**: Call `route_request` with an interaction that returns a clear `happy` sentiment. Mock the Database session such that a previous `RoutingLog` with a `reality_check_id` exists. Mock `httpx.AsyncClient().post`.
- **Expected Outcome**: Verify the log entry updates its `user_sentiment` column correctly, and verify `httpx.AsyncClient().post` is successfully triggered calling the `/feedback` endpoint with a `feedback` payload of `1` (for happy) or `0` (for unhappy).

## Execution Strategy
- These test cases will be appended to `reality-router/tests/test_mcp_routing.py` using standard `pytest.mark.asyncio` and `unittest.mock` patching.
- We'll leverage the existing `mock_router` fixture.
