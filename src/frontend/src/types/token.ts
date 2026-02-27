export interface Token {
  index: number
  name: string
  daily_limit: number
  credential: string
  _cached_expire?: string
  _cached_days?: number
}

export interface TokenStats {
  total_requests: number
  total_tokens: number
  total_cost: number
  requests_today: number
  tokens_today: number
  cost_today: number
  daily_limit: number
  remaining_days: number
  expire_date: string
}

export interface TokenDetail {
  date: string
  requests: number
  tokens: number
  cost: number
}
