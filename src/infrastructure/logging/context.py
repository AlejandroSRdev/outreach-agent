from contextvars import ContextVar

request_id_var: ContextVar[str | None] = ContextVar("request_id", default=None)
batch_id_var:   ContextVar[str | None] = ContextVar("batch_id",   default=None)
lead_id_var:    ContextVar[int | None] = ContextVar("lead_id",    default=None)
