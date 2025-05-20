from __future__ import annotations

import logging

from mcp.shared.session import RequestResponder
from mcp.server.session import ServerSession
import mcp.types as types

logger = logging.getLogger(__name__)


class PatchedServerSession(ServerSession):
    """ServerSession that gracefully handles unsupported requests."""

    async def _receive_loop(self) -> None:  # noqa: C901 - lengthy but matches base
        async with (
            self._read_stream,
            self._write_stream,
        ):
            async for message in self._read_stream:
                if isinstance(message, Exception):
                    await self._handle_incoming(message)
                elif isinstance(message.message.root, types.JSONRPCRequest):
                    raw = message.message.root
                    try:
                        validated_request = self._receive_request_type.model_validate(
                            raw.model_dump(by_alias=True, mode="json", exclude_none=True)
                        )
                    except Exception:
                        method = raw.method
                        if method in {"models/load", "contexts/switch"}:
                            await self._send_response(
                                raw.id,
                                types.ErrorData(
                                    code=types.METHOD_NOT_FOUND,
                                    message=f"{method} not supported",
                                ),
                            )
                        else:
                            await self._send_response(
                                raw.id,
                                types.ErrorData(code=types.METHOD_NOT_FOUND, message="Method not found"),
                            )
                        continue
                    responder = RequestResponder(
                        request_id=raw.id,
                        request_meta=validated_request.root.params.meta
                        if validated_request.root.params
                        else None,
                        request=validated_request,
                        session=self,
                        on_complete=lambda r: self._in_flight.pop(r.request_id, None),
                    )

                    self._in_flight[responder.request_id] = responder
                    await self._received_request(responder)

                    if not responder._completed:
                        await self._handle_incoming(responder)
                elif isinstance(message.message.root, types.JSONRPCNotification):
                    try:
                        notification = self._receive_notification_type.model_validate(
                            message.message.root.model_dump(by_alias=True, mode="json", exclude_none=True)
                        )
                        if isinstance(notification.root, types.CancelledNotification):
                            cancelled_id = notification.root.params.requestId
                            if cancelled_id in self._in_flight:
                                await self._in_flight[cancelled_id].cancel()
                        else:
                            if isinstance(notification.root, types.ProgressNotification):
                                progress_token = notification.root.params.progressToken
                                if progress_token in self._progress_callbacks:
                                    callback = self._progress_callbacks[progress_token]
                                    await callback(
                                        notification.root.params.progress,
                                        notification.root.params.total,
                                        notification.root.params.message,
                                    )
                            await self._received_notification(notification)
                            await self._handle_incoming(notification)
                    except Exception as e:  # pragma: no cover - unexpected
                        logger.warning(
                            "Failed to validate notification: %s. Message was: %s",
                            e,
                            message.message.root,
                        )
                else:
                    stream = self._response_streams.pop(message.message.root.id, None)
                    if stream:
                        await stream.send(message.message.root)
                    else:
                        await self._handle_incoming(
                            RuntimeError(
                                "Received response with an unknown request ID: %s" % message,
                            )
                        )
