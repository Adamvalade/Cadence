import { useEffect } from "react";

export function useTitle(title: string | undefined) {
  useEffect(() => {
    if (title) {
      document.title = `${title} | Cadence`;
    }
  }, [title]);
}
