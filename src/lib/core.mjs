/** @param {string} base */
export function createPath(base) {
  const prefix = `/${base.split('/').filter(Boolean).join('/')}`;
  /** @param {string} [value] */
  return (value = '') => `${prefix === '/' ? '' : prefix}/${value.replace(/^\/+/, '')}`;
}

/** @param {{draft?: boolean, date: Date | string}} data @param {Date} [now] */
export function isPublished(data, now = new Date()) {
  const time = new Date(data.date).getTime();
  return data.draft === false && Number.isFinite(time) && time <= now.getTime();
}

/** @param {string} value */
export const normalize = (value) => value.normalize('NFKC').toLocaleLowerCase('ko').trim();

/** @param {{title:string, description:string, category:string, tags:string[]}[]} entries @param {string} query */
export function searchEntries(entries, query) {
  const words = normalize(query).split(/\s+/).filter(Boolean);
  return entries.filter((entry) => {
    const text = normalize([entry.title, entry.description, entry.category, ...entry.tags].join(' '));
    return words.every((word) => text.includes(word));
  });
}

/** @param {string} value */
export const escapeXml = (value) => value.replace(/[<>&"']/g, (char) => ({ '<': '&lt;', '>': '&gt;', '&': '&amp;', '"': '&quot;', "'": '&apos;' })[char] || char);
