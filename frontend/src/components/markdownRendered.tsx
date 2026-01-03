import React from 'react';
import ReactMarkdown from 'react-markdown';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { vscDarkPlus } from 'react-syntax-highlighter/dist/cjs/styles/prism';
import remarkGfm from 'remark-gfm';
import { Copy, Check } from 'lucide-react';

interface MessageContentProps {
  content: string;
  role: 'user' | 'assistant';
}

export default function MessageContent({ content, role }: MessageContentProps) {
  const [copiedCode, setCopiedCode] = React.useState<string | null>(null);

  const handleCopyCode = async (code: string, language: string) => {
    await navigator.clipboard.writeText(code);
    setCopiedCode(`${code}-${language}`);
    setTimeout(() => setCopiedCode(null), 2000);
  };

  return (
    <div className={`prose prose-invert max-w-none ${
      role === 'user' ? 'prose-blue' : 'prose-green'
    }`}>
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        components={{
          // Code blocks with syntax highlighting
          code({ node, inline, className, children, ...props }) {
            const match = /language-(\w+)/.exec(className || '');
            const language = match ? match[1] : '';
            const codeString = String(children).replace(/\n$/, '');
            const codeId = `${codeString}-${language}`;

            return !inline && match ? (
              <div className="relative group my-4">
                {/* Language badge */}
                <div className="absolute top-0 left-0 right-0 flex items-center justify-between px-4 py-2 bg-[#1e1e1e] border-b border-gray-700 rounded-t-lg">
                  <span className="text-xs text-gray-400 font-mono uppercase">
                    {language}
                  </span>
                  <button
                    onClick={() => handleCopyCode(codeString, language)}
                    className="flex items-center gap-1 px-2 py-1 text-xs text-gray-400 hover:text-white bg-gray-800 hover:bg-gray-700 rounded transition-all"
                  >
                    {copiedCode === codeId ? (
                      <>
                        <Check className="w-3 h-3" />
                        Copied!
                      </>
                    ) : (
                      <>
                        <Copy className="w-3 h-3" />
                        Copy
                      </>
                    )}
                  </button>
                </div>
                
                {/* Code block */}
                <div className="mt-10">
                  <SyntaxHighlighter
                    style={vscDarkPlus}
                    language={language}
                    PreTag="div"
                    customStyle={{
                      margin: 0,
                      borderRadius: '0 0 0.5rem 0.5rem',
                      fontSize: '0.875rem',
                      padding: '1rem',
                    }}
                    {...props}
                  >
                    {codeString}
                  </SyntaxHighlighter>
                </div>
              </div>
            ) : (
              <code
                className="px-1.5 py-0.5 bg-gray-800 text-pink-400 rounded text-sm font-mono"
                {...props}
              >
                {children}
              </code>
            );
          },

          // Links
          a({ node, children, href, ...props }) {
            return (
              <a
                href={href}
                target="_blank"
                rel="noopener noreferrer"
                className="text-blue-400 hover:text-blue-300 underline decoration-blue-500/30 hover:decoration-blue-400 transition-colors"
                {...props}
              >
                {children}
              </a>
            );
          },

          // Headings
          h1({ node, children, ...props }) {
            return (
              <h1 className="text-2xl font-bold mt-6 mb-4 text-white border-b border-gray-700 pb-2" {...props}>
                {children}
              </h1>
            );
          },
          h2({ node, children, ...props }) {
            return (
              <h2 className="text-xl font-bold mt-5 mb-3 text-white" {...props}>
                {children}
              </h2>
            );
          },
          h3({ node, children, ...props }) {
            return (
              <h3 className="text-lg font-semibold mt-4 mb-2 text-gray-200" {...props}>
                {children}
              </h3>
            );
          },

          // Lists
          ul({ node, children, ...props }) {
            return (
              <ul className="list-disc list-inside space-y-1 my-3 text-gray-300" {...props}>
                {children}
              </ul>
            );
          },
          ol({ node, children, ...props }) {
            return (
              <ol className="list-decimal list-inside space-y-1 my-3 text-gray-300" {...props}>
                {children}
              </ol>
            );
          },
          li({ node, children, ...props }) {
            return (
              <li className="text-gray-300 leading-relaxed" {...props}>
                {children}
              </li>
            );
          },

          // Blockquotes
          blockquote({ node, children, ...props }) {
            return (
              <blockquote
                className="border-l-4 border-blue-500 pl-4 py-2 my-4 bg-blue-500/10 rounded-r text-gray-300 italic"
                {...props}
              >
                {children}
              </blockquote>
            );
          },

          // Tables
          table({ node, children, ...props }) {
            return (
              <div className="overflow-x-auto my-4">
                <table className="min-w-full border border-gray-700 rounded-lg" {...props}>
                  {children}
                </table>
              </div>
            );
          },
          thead({ node, children, ...props }) {
            return (
              <thead className="bg-gray-800" {...props}>
                {children}
              </thead>
            );
          },
          th({ node, children, ...props }) {
            return (
              <th className="px-4 py-2 text-left text-sm font-semibold text-gray-200 border-b border-gray-700" {...props}>
                {children}
              </th>
            );
          },
          td({ node, children, ...props }) {
            return (
              <td className="px-4 py-2 text-sm text-gray-300 border-b border-gray-700" {...props}>
                {children}
              </td>
            );
          },

          // Paragraphs
          p({ node, children, ...props }) {
            return (
              <p className="text-gray-300 leading-relaxed my-3" {...props}>
                {children}
              </p>
            );
          },

          // Horizontal rule
          hr({ node, ...props }) {
            return <hr className="my-6 border-gray-700" {...props} />;
          },

          // Strong/Bold
          strong({ node, children, ...props }) {
            return (
              <strong className="font-bold text-white" {...props}>
                {children}
              </strong>
            );
          },

          // Emphasis/Italic
          em({ node, children, ...props }) {
            return (
              <em className="italic text-gray-200" {...props}>
                {children}
              </em>
            );
          },
        }}
      >
        {content}
      </ReactMarkdown>
    </div>
  );
}