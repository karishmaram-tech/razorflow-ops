export default function Loading({ message = 'Loading...' }) {
  return (
    <div className="flex flex-col items-center justify-center h-[60vh] gap-4">
      <div className="spinner" />
      <p className="text-sm text-gray-500">{message}</p>
    </div>
  );
}
