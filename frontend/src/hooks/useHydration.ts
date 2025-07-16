import { useEffect, useState } from 'react'

/**
 * Custom hook to handle hydration state
 * This prevents hydration mismatches by only rendering client-side content after hydration
 */
export function useHydration() {
  const [isHydrated, setIsHydrated] = useState(false)

  useEffect(() => {
    setIsHydrated(true)
  }, [])

  return isHydrated
}
