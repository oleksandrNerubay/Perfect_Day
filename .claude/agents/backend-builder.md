# Backend agent — general rules

## Code

- Type hints on every function signature, no exceptions
- No logic inline in route handlers — delegate to module functions
- One responsibility per function; keep functions under 40 lines
- No raw pymongo/SQL calls outside the `db/` layer
- Use `datetime.now(timezone.utc)` — never naive datetimes
- Constants and config values come from `config.py` — no hardcoded strings in logic files
- Never log raw audio bytes, tokens, or API keys

## Error handling

- Wrap all external service calls (ML, ASR, DB) in try/except
- Return `{ "error": str, "code": str }` on failure — no stack traces to client
- Network/timeout errors must not crash WebSocket sessions — catch and emit a typed error frame
- Use safe wrapper functions (e.g. `call_ml_safe()`) for every third-party call

## API design

- Route handlers return typed dicts or call `jsonify()` — no bare strings
- All endpoints validate required fields before processing
- HTTP status codes must be explicit — never rely on Flask defaults for errors
- WebSocket frames are typed JSON objects: always include a `type` field

## Database

- `save_turn()` must be called before any downstream dispatch
- Always use helpers in `db/ops.py` — no ad-hoc queries in routes
- Use `mongomock` in tests — never touch the real DB instance in CI
- Compound indexes defined in `db/schema.py`, run once on startup

## Testing

- Unit tests mock all external services (ASR, ML, DB)
- Each route has at least one happy-path and one error-path test
- No test should depend on another test's state

## Security

- All secrets via environment variables — `.env` is never committed
- Input lengths validated before processing (text, audio size)
- No PII in logs

## Style

- PEP 8, 100-character line limit
- Sentence case in all user-facing strings
- No commented-out code in commits