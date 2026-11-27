// Category ids are kebab-case; the review page has no labels for them, so it
// spells them out.
export function categoryName(id: string) {
  return id.replaceAll("-", " ");
}
