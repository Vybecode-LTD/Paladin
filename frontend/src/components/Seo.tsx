import { useEffect } from "react";

const SITE_URL = "https://ashfordbriggs.com";

const DEFAULT_TITLE =
  "Paladin — Real-Time AI Intelligence for Recruiting Calls | Ashford & Briggs";
const DEFAULT_DESCRIPTION =
  "Paladin by Ashford & Briggs gives recruiters real-time intelligence during live candidate calls — skills gaps, live prompts, and instant context. Through your existing phone. No app required.";

interface SeoProps {
  title: string;
  description: string;
  path: string;
  jsonLd?: object;
}

export default function Seo({ title, description, path, jsonLd }: SeoProps) {
  useEffect(() => {
    document.title = title;

    let descriptionTag = document.querySelector<HTMLMetaElement>(
      'meta[name="description"]',
    );
    if (!descriptionTag) {
      descriptionTag = document.createElement("meta");
      descriptionTag.setAttribute("name", "description");
      document.head.appendChild(descriptionTag);
    }
    descriptionTag.setAttribute("content", description);

    let canonicalTag = document.querySelector<HTMLLinkElement>(
      'link[rel="canonical"]',
    );
    if (!canonicalTag) {
      canonicalTag = document.createElement("link");
      canonicalTag.setAttribute("rel", "canonical");
      document.head.appendChild(canonicalTag);
    }
    canonicalTag.setAttribute("href", `${SITE_URL}${path}`);

    let jsonLdScript: HTMLScriptElement | null = null;
    if (jsonLd) {
      jsonLdScript = document.createElement("script");
      jsonLdScript.type = "application/ld+json";
      jsonLdScript.textContent = JSON.stringify(jsonLd);
      document.head.appendChild(jsonLdScript);
    }

    return () => {
      document.title = DEFAULT_TITLE;
      if (descriptionTag) {
        descriptionTag.setAttribute("content", DEFAULT_DESCRIPTION);
      }
      if (jsonLdScript) {
        jsonLdScript.remove();
      }
    };
  }, [title, description, path, jsonLd]);

  return null;
}
