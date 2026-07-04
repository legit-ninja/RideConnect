import { Compass } from 'lucide-react';

export default function EmptyState({ icon: Icon = Compass, title, description, action }) {
  return (
    <div className="flex flex-col items-center justify-center py-20 px-4 text-center">
      <div className="mb-4 flex h-16 w-16 items-center justify-center rounded-full bg-accent">
        <Icon className="h-7 w-7 text-muted-foreground" />
      </div>
      <h3 className="font-heading text-xl font-semibold">{title}</h3>
      {description && (
        <p className="mt-2 text-sm text-muted-foreground max-w-sm">{description}</p>
      )}
      {action && <div className="mt-6">{action}</div>}
    </div>
  );
}