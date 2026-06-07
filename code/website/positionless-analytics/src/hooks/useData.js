// This code was written by Claude in accordance with our course's AI use policy.

import { useState, useEffect } from 'react'

const FILES = {
  playersIndexTable: '/data/players_index_table.json',
  playerTrajectories: '/data/player_trajectories.json',
  dashboardAggregates: '/data/dashboard_aggregates.json',
}

export default function useData() {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    async function load() {
      try {
        const results = await Promise.all(
          Object.entries(FILES).map(async ([key, path]) => {
            const response = await fetch(path)

            if (!response.ok) {
              throw new Error(`Failed to load ${path}`)
            }

            return [key, await response.json()]
          })
        )

        setData(Object.fromEntries(results))
      } catch (err) {
        console.error(err)
        setError(err.message)
      } finally {
        setLoading(false)
      }
    }

    load()
  }, [])

  return {
    data,
    loading,
    error,
  }
}