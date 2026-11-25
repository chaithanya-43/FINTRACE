import { useEffect, useState } from "react";

export function navigate(path) {
  if (window.location.pathname + window.location.search === path) {
    return;
  }
  window.history.pushState({}, "", path);
  window.dispatchEvent(new PopStateEvent("popstate"));
}

export function usePath() {
  const [path, setPath] = useState(window.location.pathname);

  useEffect(() => {
    const handle = () => setPath(window.location.pathname);
    window.addEventListener("popstate", handle);
    return () => window.removeEventListener("popstate", handle);
  }, []);

  return path;
}

export function matchCaseId(path) {
  const match = path.match(/^\/cases\/([0-9a-fA-F-]{36})(?:\/([a-z-]+))?$/);
  return match ? match[1] : null;
}

export function matchCaseRoute(path) {
  const match = path.match(/^\/cases\/([0-9a-fA-F-]{36})(?:\/([a-z-]+))?$/);
  if (!match) {
    return null;
  }
  return { caseId: match[1], section: match[2] || "overview" };
}

export function Link({ to, children, className, ...rest }) {
  return (
    <a
      href={to}
      className={className}
      onClick={(event) => {
        if (event.metaKey || event.ctrlKey || event.shiftKey || event.button !== 0) {
          return;
        }
        event.preventDefault();
        navigate(to);
      }}
      {...rest}
    >
      {children}
    </a>
  );
}
