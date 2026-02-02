/**
 * Utility functions for formatting values.
 */

/**
 * Format energy in Hartree to a readable string.
 */
export function formatEnergy(energy: number, unit: 'hartree' | 'ev' = 'hartree'): string {
  if (unit === 'ev') {
    return `${(energy * 27.2114).toFixed(4)} eV`;
  }
  return `${energy.toFixed(6)} Ha`;
}

/**
 * Format a timestamp to a readable date string.
 */
export function formatDate(dateString: string): string {
  const date = new Date(dateString);
  return date.toLocaleString();
}

/**
 * Format duration in seconds to readable string.
 */
export function formatDuration(seconds: number): string {
  if (seconds < 60) {
    return `${seconds.toFixed(1)}s`;
  }
  const minutes = Math.floor(seconds / 60);
  const remainingSeconds = seconds % 60;
  return `${minutes}m ${remainingSeconds.toFixed(0)}s`;
}

/**
 * Format job status with proper capitalization.
 */
export function formatStatus(status: string): string {
  return status.charAt(0).toUpperCase() + status.slice(1);
}

/**
 * Get status color for Tailwind CSS.
 */
export function getStatusColor(status: string): string {
  const colors: Record<string, string> = {
    pending: 'text-yellow-600 bg-yellow-100',
    running: 'text-blue-600 bg-blue-100',
    completed: 'text-green-600 bg-green-100',
    failed: 'text-red-600 bg-red-100',
    cancelled: 'text-gray-600 bg-gray-100',
  };
  return colors[status] || 'text-gray-600 bg-gray-100';
}