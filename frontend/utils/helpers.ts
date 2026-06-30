// Render helpers and string formatting utilities

export function formatDate(dateString: string): string {
  if (!dateString) return "";
  const date = new Date(dateString);
  return date.toLocaleDateString("en-IN", {
    day: "2-digit",
    month: "short",
    year: "numeric",
  });
}

export function truncateText(text: string, maxLength: number = 60): string {
  if (!text) return "";
  if (text.length <= maxLength) return text;
  return `${text.slice(0, maxLength)}...`;
}
