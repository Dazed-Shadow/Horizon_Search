// Bookmark / watch list: persist user-selected contracts across browser sessions without requiring auth.
// Read/write a versioned localStorage key; store contract snapshots so bookmarks remain renderable after deadlines pass.
import { useState, useCallback } from "react";

const STORAGE_KEY = "horizon_search.bookmarks.v1";

function readStorage() {
  try {
    return JSON.parse(localStorage.getItem(STORAGE_KEY) || "[]");
  } catch {
    return [];
  }
}

function writeStorage(bookmarks) {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(bookmarks));
  } catch {}
}

export function useBookmarks() {
  const [bookmarks, setBookmarks] = useState(() => readStorage());

  const isBookmarked = useCallback((noticeId) =>
    bookmarks.some(b => b.notice_id === noticeId), [bookmarks]);

  const toggleBookmark = useCallback((contract) => {
    setBookmarks(prev => {
      const exists = prev.some(b => b.notice_id === contract.notice_id);
      const next = exists
        ? prev.filter(b => b.notice_id !== contract.notice_id)
        : [{ notice_id: contract.notice_id, bookmarked_at: new Date().toISOString(), contract }, ...prev];
      writeStorage(next);
      return next;
    });
  }, []);

  const removeBookmark = useCallback((noticeId) => {
    setBookmarks(prev => {
      const next = prev.filter(b => b.notice_id !== noticeId);
      writeStorage(next);
      return next;
    });
  }, []);

  return { bookmarks, isBookmarked, toggleBookmark, removeBookmark, count: bookmarks.length };
}
