import { create } from 'zustand';

export interface StockToBuy {
  symbol: string;
  companyName: string;
  price: number;
  change?: string;
  currency?: string;
  exchange?: string;
}

interface StockModalState {
  isOpen: boolean;
  selectedStock: StockToBuy | null;
  openBuyModal: (stock: StockToBuy) => void;
  closeBuyModal: () => void;
  // Callback when a stock is bought to trigger dashboard/portfolio re-fetch
  lastPurchasedStock: { symbol: string; timestamp: number } | null;
  notifyPurchaseSuccess: (symbol: string) => void;
}

export const useStockModalStore = create<StockModalState>((set) => ({
  isOpen: false,
  selectedStock: null,
  lastPurchasedStock: null,

  openBuyModal: (stock: StockToBuy) =>
    set({
      isOpen: true,
      selectedStock: stock,
    }),

  closeBuyModal: () =>
    set({
      isOpen: false,
      selectedStock: null,
    }),

  notifyPurchaseSuccess: (symbol: string) =>
    set({
      lastPurchasedStock: { symbol, timestamp: Date.now() },
    }),
}));
