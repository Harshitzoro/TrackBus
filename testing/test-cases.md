# Test Cases

| ID | Scenario | Expected result |
| --- | --- | --- |
| TC-001 | Backend health endpoint is requested | Service returns a healthy response |
| TC-002 | GPS update has out-of-range coordinates | Request is rejected |
| TC-003 | Bus location is stale | Client does not present it as live |
| TC-004 | Bus is outside configured route tolerance | Deviation is reported |