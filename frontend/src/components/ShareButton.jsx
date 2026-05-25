import { useState } from "react";

const SHARE_TEXT = "Found a free tool that searches government contracts set aside for veteran-owned businesses — filters by SDVOSB, VOSB, 8(a), and more. Built specifically for veterans. Worth bookmarking:";
const SHARE_TITLE = "Horizon Search — Federal Contracts for Veteran Businesses";

export default function ShareButton({ url }) {
  const [copied, setCopied] = useState(false);
  const shareUrl = url || window.location.href;

  async function handleShare() {
    // Web Share API — works on mobile and modern desktop browsers
    if (navigator.share) {
      try {
        await navigator.share({ title: SHARE_TITLE, text: SHARE_TEXT, url: shareUrl });
        return;
      } catch {
        // User cancelled share sheet — fall through to copy
      }
    }
    // Fallback: copy link to clipboard
    try {
      await navigator.clipboard.writeText(shareUrl);
      setCopied(true);
      setTimeout(() => setCopied(false), 2500);
    } catch {
      // Clipboard blocked — last resort: select a temp input
      const input = document.createElement("input");
      input.value = shareUrl;
      document.body.appendChild(input);
      input.select();
      document.execCommand("copy");
      document.body.removeChild(input);
      setCopied(true);
      setTimeout(() => setCopied(false), 2500);
    }
  }

  return (
    <button
      type="button"
      onClick={handleShare}
      className={`inline-flex items-center gap-2 text-xs font-bold px-3 py-2 rounded-full
                  border transition ${
                    copied
                      ? "bg-green-500/20 border-green-400/40 text-green-200"
                      : "bg-white/10 border-white/20 text-white/80 hover:bg-white/20 hover:text-white"
                  }`}
    >
      {copied ? (
        <>
          <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
          </svg>
          Link copied!
        </>
      ) : (
        <>
          <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
              d="M8.684 13.342C8.886 12.938 9 12.482 9 12c0-.482-.114-.938-.316-1.342m0 2.684a3 3 0 110-2.684m0 2.684l6.632 3.316m-6.632-6l6.632-3.316m0 0a3 3 0 105.367-2.684 3 3 0 00-5.367 2.684zm0 9.316a3 3 0 105.368 2.684 3 3 0 00-5.368-2.684z" />
          </svg>
          Share with a fellow veteran
        </>
      )}
    </button>
  );
}
