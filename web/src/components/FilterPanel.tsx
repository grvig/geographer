import type { Category } from "../data/clueSchema";
import type { Filters } from "../lib/filterDetections";

type Props = {
  // The categories found in the current image.
  categories: Category[];
  filters: Filters;
  onChange: (filters: Filters) => void;
};

export default function FilterPanel({ categories, filters, onChange }: Props) {
  function toggleCategory(id: string, shown: boolean) {
    let hiddenCategories = filters.hiddenCategories.filter(
      (other) => other !== id,
    );
    if (!shown) {
      hiddenCategories = [...hiddenCategories, id];
    }
    onChange({ ...filters, hiddenCategories });
  }

  const percent = Math.round(filters.minConfidence * 100);
  return (
    <fieldset className="space-y-2 text-sm">
      <legend className="mb-1 font-semibold">Filters</legend>
      {categories.map((category) => (
        <label key={category.id} className="flex items-center gap-2">
          <input
            type="checkbox"
            checked={!filters.hiddenCategories.includes(category.id)}
            onChange={(event) =>
              toggleCategory(category.id, event.target.checked)
            }
            className="accent-accent"
          />
          <span
            aria-hidden="true"
            className="size-2.5 rounded-full"
            style={{ background: category.overlay_colour }}
          />
          {category.label}
        </label>
      ))}
      <label className="block">
        Minimum confidence: {percent}%
        <input
          type="range"
          min={0}
          max={100}
          step={5}
          value={percent}
          onChange={(event) =>
            onChange({
              ...filters,
              minConfidence: Number(event.target.value) / 100,
            })
          }
          className="block w-full accent-accent"
        />
      </label>
      <label className="flex items-center gap-2">
        <input
          type="checkbox"
          checked={filters.verifiedOnly}
          onChange={(event) =>
            onChange({ ...filters, verifiedOnly: event.target.checked })
          }
          className="accent-accent"
        />
        Checked by hand only
      </label>
    </fieldset>
  );
}
