// src/hooks/useRealtime.js

import {
  useEffect,
} from "react";

export default function useRealtime(
  url,
  onMessage
) {

  useEffect(() => {

    if (!url)
      return;

    const ws =
      new WebSocket(
        url
      );

    ws.onopen =
      () => {

        console.log(
          "WebSocket connected"
        );

      };

    ws.onmessage =
      (event) => {

        const data =
          JSON.parse(
            event.data
          );

        onMessage(
          data
        );

      };

    ws.onerror =
      (error) => {

        console.error(
          error
        );

      };

    ws.onclose =
      () => {

        console.log(
          "WebSocket closed"
        );

      };

    return () => {

      ws.close();

    };

  }, [
    url,
    onMessage,
  ]);
}