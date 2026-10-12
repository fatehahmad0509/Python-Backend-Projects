import { Suspense, lazy } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

const CodeBlock = lazy(() => import("./CodeBlock"));

export default function Markdown({ content }: { content: string }) {
  return (
    <div className="markdown-body">
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        components={{
          a: ({ ...props }) => (
            <a {...props} target="_blank" rel="noopener noreferrer" />
          ),
          code(props) {
            const { children, className, ...rest } = props as {
              children?: React.ReactNode;
              className?: string;
              inline?: boolean;
            };
            const match = /language-(\w+)/.exec(className || "");
            const isInline = (props as { inline?: boolean }).inline;
            const code = String(children).replace(/\n$/, "");

            if (!isInline && match) {
              return (
                <Suspense
                  fallback={
                    <pre>
                      <code>{code}</code>
                    </pre>
                  }
                >
                  <CodeBlock language={match[1]} code={code} />
                </Suspense>
              );
            }
            return (
              <code {...rest} className={className}>
                {children}
              </code>
            );
          },
        }}
      >
        {content}
      </ReactMarkdown>
    </div>
  );
}
