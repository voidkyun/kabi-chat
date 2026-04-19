import { Children, Component, Suspense, isValidElement, lazy, memo, useMemo } from "react";

import katex from "katex";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import remarkMath from "remark-math";

const MARKDOWN_PLUGINS = [remarkGfm, remarkMath];
const LazyMathJaxFallback = lazy(() => import("./MathJaxFallback"));

function readTextContent(node) {
  if (typeof node === "string" || typeof node === "number") {
    return String(node);
  }
  if (Array.isArray(node)) {
    return node.map((child) => readTextContent(child)).join("");
  }
  if (isValidElement(node)) {
    return readTextContent(node.props.children);
  }
  return "";
}

function trimTrailingNewline(value) {
  return value.replace(/\n$/, "");
}

function renderKatex(value, displayMode) {
  try {
    return katex.renderToString(value, {
      displayMode,
      output: "html",
      strict: "warn",
      throwOnError: true,
    });
  } catch {
    return "";
  }
}

class MathRenderBoundary extends Component {
  constructor(props) {
    super(props);
    this.state = {
      hasError: false,
    };
  }

  static getDerivedStateFromError() {
    return {
      hasError: true,
    };
  }

  render() {
    if (this.state.hasError) {
      return <code className="markdown-math__source">{this.props.expression}</code>;
    }

    return this.props.children;
  }
}

const MarkdownMath = memo(function MarkdownMath({ displayMode, value }) {
  const katexMarkup = useMemo(() => renderKatex(value, displayMode), [displayMode, value]);

  if (katexMarkup) {
    return (
      <span
        className={displayMode ? "markdown-math markdown-math--display" : "markdown-math"}
        dangerouslySetInnerHTML={{ __html: katexMarkup }}
      />
    );
  }

  const expression = displayMode ? `$$${value}$$` : `$${value}$`;

  return (
    <span className={displayMode ? "markdown-math markdown-math--display" : "markdown-math"}>
      <MathRenderBoundary expression={expression}>
        <Suspense fallback={<code className="markdown-math__source">{expression}</code>}>
          <LazyMathJaxFallback displayMode={displayMode} expression={expression} />
        </Suspense>
      </MathRenderBoundary>
    </span>
  );
});

function MarkdownCode({ children, className, ...props }) {
  const value = trimTrailingNewline(readTextContent(children));
  if (typeof className === "string" && className.includes("math-inline")) {
    return <MarkdownMath value={value} displayMode={false} />;
  }
  if (typeof className === "string" && className.includes("math-display")) {
    return (
      <span data-math-display="true">
        <MarkdownMath value={value} displayMode />
      </span>
    );
  }
  return (
    <code className={className} {...props}>
      {children}
    </code>
  );
}

function MarkdownPre({ children, ...props }) {
  if (Children.count(children) === 1) {
    const child = Children.only(children);
    if (
      isValidElement(child) &&
      child.props &&
      child.props["data-math-display"] === "true"
    ) {
      return child.props.children;
    }
  }

  return <pre {...props}>{children}</pre>;
}

export const MessageRenderer = memo(function MessageRenderer({ body }) {
  return (
    <ReactMarkdown
      className="message-markdown"
      components={{
        code: MarkdownCode,
        pre: MarkdownPre,
      }}
      remarkPlugins={MARKDOWN_PLUGINS}
    >
      {body}
    </ReactMarkdown>
  );
});
