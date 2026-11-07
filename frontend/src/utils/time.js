export function parseServerDate(value) {
    if (!value) return null;
    const text = String(value);
    const hasZone = /[zZ]$|[+-]\d\d:?\d\d$/.test(text);
    const date = new Date(hasZone ? text : `${text}Z`);
    return Number.isNaN(date.getTime()) ? null : date;
}

export function timeAgo(value) {
    const date = parseServerDate(value);
    if (!date) return "";

    const seconds = Math.max(0, (Date.now() - date.getTime()) / 1000);

    if (seconds < 60) return "just now";
    if (seconds < 3600) return `${Math.floor(seconds / 60)} min ago`;
    if (seconds < 86400) return `${Math.floor(seconds / 3600)} h ago`;
    if (seconds < 86400 * 2) return "yesterday";
    if (seconds < 86400 * 7) return `${Math.floor(seconds / 86400)} days ago`;

    return date.toLocaleDateString(undefined, { day: "numeric", month: "short" });
}

export function clockTime(value) {
    const date = parseServerDate(value);
    if (!date) return "";
    return date.toLocaleTimeString(undefined, { hour: "numeric", minute: "2-digit" });
}
