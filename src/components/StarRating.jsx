import { Star } from 'lucide-react';

export default function StarRating({ rating = 0, size = 16, interactive = false, onChange }) {
  return (
    <div className="flex items-center gap-0.5">
      {[1, 2, 3, 4, 5].map((star) => (
        <button
          key={star}
          type="button"
          disabled={!interactive}
          onClick={() => interactive && onChange?.(star)}
          className={interactive ? 'cursor-pointer' : 'cursor-default'}
        >
          <Star
            style={{ width: size, height: size }}
            className={star <= rating ? 'fill-primary text-primary' : 'text-muted-foreground/40'}
          />
        </button>
      ))}
    </div>
  );
}