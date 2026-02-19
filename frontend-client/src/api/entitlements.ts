import { apiFetch } from './client'

export interface TVODPurchaseResponse {
  entitlement_id: string
  title_id: string
  offer_type: 'rent' | 'buy'
  expires_at: string | null
  price_cents: number
  currency: string
}

export function purchaseTitle(
  titleId: string,
  offerType: 'rent' | 'buy',
): Promise<TVODPurchaseResponse> {
  return apiFetch<TVODPurchaseResponse>(`/catalog/titles/${titleId}/purchase`, {
    method: 'POST',
    body: JSON.stringify({ offer_type: offerType }),
  })
}
