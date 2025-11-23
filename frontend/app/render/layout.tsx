import Script from 'next/script';

export default function RenderLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <head>
        <script crossOrigin="anonymous" src="https://unpkg.com/react@18/umd/react.production.min.js" />
        <script crossOrigin="anonymous" src="https://unpkg.com/react-dom@18/umd/react-dom.production.min.js" />
        <script src="https://unpkg.com/@babel/standalone/babel.min.js" />
        <script src="https://cdn.tailwindcss.com" />
      </head>
      <body style={{ margin: 0, padding: 0 }}>
        {children}
      </body>
    </html>
  );
}
