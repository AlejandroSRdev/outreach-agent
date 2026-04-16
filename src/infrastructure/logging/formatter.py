import json
import logging

from src.infrastructure.logging.context import request_id_var, batch_id_var, lead_id_var

_STANDARD_LOG_RECORD_FIELDS = frozenset(logging.LogRecord(
    "", 0, "", 0, "", (), None
).__dict__.keys()) | {"message", "asctime"}


class JSONFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        record.message = record.getMessage()
        log = {
            "timestamp":  self.formatTime(record, self.datefmt),
            "level":      record.levelname,
            "logger":     record.name,
            "event":      record.message,
            "request_id": request_id_var.get(),
            "batch_id":   batch_id_var.get(),
            "lead_id":    lead_id_var.get(),
        }
        # Merge extra fields not present in the standard LogRecord
        for key, value in record.__dict__.items():
            if key not in _STANDARD_LOG_RECORD_FIELDS:
                log[key] = value

        if record.exc_info:
            log["exc_info"] = self.formatException(record.exc_info)

        return json.dumps(log, default=str)
