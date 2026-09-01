export default function ErrorDisplay({ message, onRetry }) {
  return (
    <div className="flex flex-col items-center justify-center h-[60vh] gap-4">
      <div className="w-16 h-16 rounded-full bg-red-50 flex items-center justify-center">
        <svg className="w-8 h-8 text-red-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L4.082 16.5c-.77.833.192 2.5 1.732 2.5z" />
        </svg>
      </div>
      <h3 className="text-lg font-semibold text-gray-900">Something went wrong</h3>
      <p className="text-sm text-gray-500 max-w-md text-center">{message}</p>
      {onRetry && (
        <button onClick={onRetry} className="btn-primary mt-2">
          Try Again
        </button>
      )}
    </div>
  );
}
