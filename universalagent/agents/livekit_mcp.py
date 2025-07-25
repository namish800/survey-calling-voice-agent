from contextlib import AbstractAsyncContextManager
from typing import Any
from urllib.parse import urlparse
from livekit.agents import mcp
from anyio.streams.memory import MemoryObjectReceiveStream, MemoryObjectSendStream
from datetime import timedelta


class CustomMCPServerHTTP(mcp.MCPServer):
    """
    HTTP-based MCP server to detect transport type based on URL path.

    - URLs ending with 'sse' use Server-Sent Events (SSE) transport
    - URLs ending with 'mcp' use streamable HTTP transport
    - For other URLs, defaults to SSE transport for backward compatibility

    Note: SSE transport is being deprecated in favor of streamable HTTP transport.
    See: https://github.com/modelcontextprotocol/modelcontextprotocol/pull/206
    """

    def __init__(
        self,
        url: str,
        headers: dict[str, Any] | None = None,
        timeout: float = 5,
        sse_read_timeout: float = 60 * 5,
        client_session_timeout_seconds: float = 5,
    ) -> None:
        super().__init__(client_session_timeout_seconds=client_session_timeout_seconds)
        self.url = url
        self.headers = headers
        self._timeout = timeout
        self._sse_read_timeout = sse_read_timeout
        self._use_streamable_http = self._should_use_streamable_http(url)

    def _should_use_streamable_http(self, url: str) -> bool:
        """
        Determine transport type based on URL path.

        Returns True for streamable HTTP if URL ends with 'mcp',
        False for SSE if URL ends with 'sse' or for backward compatibility.
        """
        parsed_url = urlparse(url)
        path_lower = parsed_url.path.lower().rstrip("/")
        return path_lower.endswith("mcp") or path_lower.endswith("mcp/stream")

    def client_streams(
        self,
    ) -> AbstractAsyncContextManager[
        tuple[
            MemoryObjectReceiveStream[mcp.SessionMessage | Exception],
            MemoryObjectSendStream[mcp.SessionMessage],
        ]
        | tuple[
            MemoryObjectReceiveStream[mcp.SessionMessage | Exception],
            MemoryObjectSendStream[mcp.SessionMessage],
            mcp.GetSessionIdCallback,
        ]
    ]:
        if self._use_streamable_http:
            return mcp.streamablehttp_client(  # type: ignore[no-any-return]
                url=self.url,
                headers=self.headers,
                timeout=timedelta(seconds=self._timeout),
                sse_read_timeout=timedelta(seconds=self._sse_read_timeout),
            )
        else:
            return mcp.sse_client(  # type: ignore[no-any-return]
                url=self.url,
                headers=self.headers,
                timeout=self._timeout,
                sse_read_timeout=self._sse_read_timeout,
            )

    def __repr__(self) -> str:
        transport_type = "streamable_http" if self._use_streamable_http else "sse"
        return f"CustomMCPServerHTTP(url={self.url}, transport={transport_type})"
