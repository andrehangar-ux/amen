import { ScrollViewStyleReset } from 'expo-router/html';
import { type PropsWithChildren } from 'react';

/**
 * This file is web-only and used to configure the root HTML for every web page during static rendering.
 * The contents of this function only run in Node.js environments and do not have access to the DOM or browser APIs.
 */
export default function Root({ children }: PropsWithChildren) {
  return (
    <html lang="it">
      <head>
        <meta charSet="utf-8" />
        <meta httpEquiv="X-UA-Compatible" content="IE=edge" />
        <meta name="viewport" content="width=device-width, initial-scale=1, shrink-to-fit=no" />
        
        {/* PWA meta tags */}
        <meta name="theme-color" content="#6B7F5B" />
        <meta name="apple-mobile-web-app-capable" content="yes" />
        <meta name="apple-mobile-web-app-status-bar-style" content="default" />
        <meta name="apple-mobile-web-app-title" content="Amen!" />
        <meta name="description" content="La tua app spirituale cristiana quotidiana" />

        {/* Load Ionicons CSS from CDN */}
        <link 
          rel="stylesheet" 
          href="https://unpkg.com/ionicons@7.2.1/dist/css/ionicons.min.css"
        />

        <ScrollViewStyleReset />

        {/* Using raw CSS styles as an escape hatch to ensure the background color never flickers in dark-mode. */}
        <style dangerouslySetInnerHTML={{ __html: responsiveBackground }} />
        
        {/* Add any additional <head> elements that you want globally available on web... */}
      </head>
      <body>{children}</body>
    </html>
  );
}

const responsiveBackground = `
body {
  background-color: #FAFAF8;
}
@media (prefers-color-scheme: dark) {
  body {
    background-color: #FAFAF8;
  }
}
`;
