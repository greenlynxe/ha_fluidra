# 0.1.3

Reliability update to reduce pressure on the Fluidra cloud API and the Z250iQ.

## Included in this version

- changed the default fallback REST polling interval from 2 minutes to 15 minutes
- allowed configuring fallback polling from 5 to 120 minutes
- stopped doing an immediate full refresh after every write
- delayed the post-write confirmation refresh to 30 seconds
- added REST request spacing to avoid short API bursts
- added progressive WebSocket reconnect backoff instead of retrying every 5 seconds

## Why this matters

The integration now treats WebSocket push as the primary update path and keeps REST polling as a conservative safety net. This should reduce the risk of overwhelming fragile Fluidra cloud/device endpoints.
