import React from 'react';
import ReactMarkdown, { Components } from 'react-markdown';
import remarkGfm from 'remark-gfm';

/**
 * Renders AI answers as real markdown (bold, bullet lists, tables, links...)
 * instead of showing raw `**asterisks**` in the chat bubble.
 *
 * Styling is done per-element here so we don't need the tailwind typography plugin.
 */
const components: Components = {
  p: ({ node, ...props }) => (
    // whitespace-pre-line keeps the single line-breaks the agent writes between emoji headings
    <p className="mb-3 last:mb-0 whitespace-pre-line" {...props} />
  ),
  strong: ({ node, ...props }) => <strong className="font-bold text-slate-900" {...props} />,
  em: ({ node, ...props }) => <em className="italic" {...props} />,
  ul: ({ node, ...props }) => (
    <ul className="mb-3 last:mb-0 space-y-1.5 pl-5 list-disc marker:text-blue-500" {...props} />
  ),
  ol: ({ node, ...props }) => (
    <ol className="mb-3 last:mb-0 space-y-1.5 pl-5 list-decimal marker:text-blue-500 marker:font-semibold" {...props} />
  ),
  li: ({ node, ...props }) => <li className="pl-1 leading-relaxed" {...props} />,
  h1: ({ node, ...props }) => <h1 className="text-lg font-extrabold text-slate-900 mt-4 mb-2 first:mt-0" {...props} />,
  h2: ({ node, ...props }) => <h2 className="text-base font-extrabold text-slate-900 mt-4 mb-2 first:mt-0" {...props} />,
  h3: ({ node, ...props }) => <h3 className="text-[15px] font-bold text-slate-900 mt-3 mb-1.5 first:mt-0" {...props} />,
  a: ({ node, ...props }) => (
    <a
      className="text-blue-600 font-medium underline underline-offset-2 hover:text-blue-700"
      target="_blank"
      rel="noopener noreferrer"
      {...props}
    />
  ),
  blockquote: ({ node, ...props }) => (
    <blockquote className="mb-3 last:mb-0 border-l-4 border-blue-200 bg-blue-50/60 pl-3 pr-2 py-1.5 rounded-r-lg text-slate-700" {...props} />
  ),
  hr: ({ node, ...props }) => <hr className="my-4 border-slate-200" {...props} />,
  code: ({ node, ...props }) => (
    <code className="px-1.5 py-0.5 rounded-md bg-slate-200/70 text-[13px] font-mono text-slate-800" {...props} />
  ),
  pre: ({ node, ...props }) => (
    <pre className="mb-3 last:mb-0 p-3 rounded-xl bg-slate-900 text-slate-100 text-xs overflow-x-auto" {...props} />
  ),
  table: ({ node, ...props }) => (
    <div className="mb-3 last:mb-0 overflow-x-auto rounded-xl border border-slate-200 bg-white">
      <table className="w-full text-left text-xs md:text-sm border-collapse" {...props} />
    </div>
  ),
  thead: ({ node, ...props }) => <thead className="bg-slate-50" {...props} />,
  th: ({ node, ...props }) => (
    <th className="px-3 py-2 font-bold text-slate-700 border-b border-slate-200 whitespace-nowrap" {...props} />
  ),
  td: ({ node, ...props }) => <td className="px-3 py-2 border-b border-slate-100 align-top" {...props} />,
};

interface MarkdownMessageProps {
  text: string;
}

export const MarkdownMessage: React.FC<MarkdownMessageProps> = ({ text }) => (
  <div className="break-words">
    <ReactMarkdown remarkPlugins={[remarkGfm]} components={components}>
      {text}
    </ReactMarkdown>
  </div>
);

export default MarkdownMessage;
