import React, { useState, useEffect } from 'react';
import {
  X,
  Plus,
  Minus,
  CheckCircle2,
  ShieldCheck,
  CreditCard,
  Smartphone,
  Wallet,
  ArrowRight,
  TrendingUp,
  AlertCircle,
  Loader2,
  Briefcase,
} from 'lucide-react';
import { useStockModalStore } from '../store/stockModalStore';
import { useChatStore } from '../store/chatStore';
import { useUserStore } from '../store/userStore';

const API_BASE = (import.meta.env.VITE_API_BASE_URL || '').replace(/\/$/, '');

type Step = 'configure' | 'payment' | 'success';
type PaymentMethod = 'groww_upi' | 'gpay' | 'groww_balance' | 'netbanking';

export const StockPurchaseModal: React.FC = () => {
  const { isOpen, selectedStock, closeBuyModal, notifyPurchaseSuccess } = useStockModalStore();
  const { setActiveTab, userId } = useChatStore();
  const { user } = useUserStore();

  const [step, setStep] = useState<Step>('configure');
  const [quantity, setQuantity] = useState<number>(1);
  const [orderType, setOrderType] = useState<'delivery' | 'intraday'>('delivery');
  const [paymentMethod, setPaymentMethod] = useState<PaymentMethod>('groww_upi');
  const [isProcessing, setIsProcessing] = useState<boolean>(false);
  const [orderId, setOrderId] = useState<string>('');
  const [errorMessage, setErrorMessage] = useState<string>('');

  const effectiveUserId = user?.user_id || userId;

  // Reset modal state whenever a new stock is opened
  useEffect(() => {
    if (isOpen) {
      setStep('configure');
      setQuantity(1);
      setOrderType('delivery');
      setPaymentMethod('groww_upi');
      setIsProcessing(false);
      setErrorMessage('');
      setOrderId(`GRW-${Date.now().toString().slice(-6)}-${Math.floor(100 + Math.random() * 900)}`);
    }
  }, [isOpen, selectedStock]);

  if (!isOpen || !selectedStock) return null;

  const unitPrice = selectedStock.price || 0;
  const totalAmount = unitPrice * quantity;
  const currencySymbol = selectedStock.currency === 'USD' ? '$' : '₹';

  const formatMoney = (val: number) => {
    return `${currencySymbol}${val.toLocaleString(undefined, {
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    })}`;
  };

  const handleQuantityChange = (delta: number) => {
    setQuantity((prev) => Math.max(1, prev + delta));
  };

  const handleCustomQuantity = (e: React.ChangeEvent<HTMLInputElement>) => {
    const val = parseInt(e.target.value, 10);
    if (!isNaN(val) && val >= 1) {
      setQuantity(val);
    } else if (e.target.value === '') {
      setQuantity(1);
    }
  };

  // Step 2 Dummy Payment Execution
  const handleExecuteDummyPayment = async () => {
    setIsProcessing(true);
    setErrorMessage('');

    try {
      // 1. Simulate payment network authorization delay
      await new Promise((resolve) => setTimeout(resolve, 1200));

      // 2. Persist real stock holding to MongoDB backend
      const res = await fetch(`${API_BASE}/api/stocks/${effectiveUserId}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          symbol: selectedStock.symbol.toUpperCase(),
          company_name: selectedStock.companyName,
          quantity: quantity,
          buy_price: selectedStock.price,
        }),
      });

      if (!res.ok) {
        const errorData = await res.json().catch(() => null);
        throw new Error(errorData?.detail || 'Failed to record purchase in portfolio database.');
      }

      // 3. Notify app store to trigger dashboard portfolio re-calculation
      notifyPurchaseSuccess(selectedStock.symbol);

      // 4. Advance to success screen
      setIsProcessing(false);
      setStep('success');
    } catch (err: any) {
      console.error('[StockPurchaseModal] Purchase failed:', err);
      setIsProcessing(false);
      setErrorMessage(err.message || 'Payment simulation failed. Please try again.');
    }
  };

  const handleViewPortfolio = () => {
    closeBuyModal();
    setActiveTab('dashboard');
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-xs animate-in fade-in duration-200">
      <div
        className="relative w-full max-w-lg bg-white rounded-3xl shadow-2xl border border-slate-100 overflow-hidden flex flex-col max-h-[90vh]"
        onClick={(e) => e.stopPropagation()}
      >
        {/* ============================================================= */}
        {/* Modal Header */}
        {/* ============================================================= */}
        <div className="px-6 py-4 border-b border-slate-100 flex items-center justify-between bg-gradient-to-r from-slate-50 via-white to-emerald-50/30">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-2xl bg-[#00D09C]/10 border border-[#00D09C]/30 flex items-center justify-center text-[#00A87E] font-black text-sm">
              {selectedStock.symbol.slice(0, 2).toUpperCase()}
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h3 className="text-base font-extrabold text-slate-900">{selectedStock.symbol}</h3>
                <span className="text-[10px] uppercase font-bold px-2 py-0.5 rounded-md bg-slate-100 text-slate-500">
                  {selectedStock.exchange || 'NSE'}
                </span>
                <span className="flex items-center gap-1 text-[11px] font-bold text-emerald-600 bg-emerald-50 px-2 py-0.5 rounded-full">
                  <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse"></span>
                  Live
                </span>
              </div>
              <p className="text-xs text-slate-500 font-medium truncate max-w-[220px]">
                {selectedStock.companyName}
              </p>
            </div>
          </div>

          <button
            type="button"
            onClick={closeBuyModal}
            className="w-8 h-8 rounded-full bg-slate-100 hover:bg-slate-200 flex items-center justify-center text-slate-500 hover:text-slate-800 transition-colors"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* ============================================================= */}
        {/* Step 1: Configure Order (Quantity & Order Type) */}
        {/* ============================================================= */}
        {step === 'configure' && (
          <div className="p-6 overflow-y-auto space-y-6">
            {/* Live Price Row */}
            <div className="flex items-center justify-between p-4 bg-slate-50 rounded-2xl border border-slate-100">
              <div>
                <span className="text-[11px] uppercase font-bold text-slate-400 block">
                  Market Execution Price
                </span>
                <span className="text-xl md:text-2xl font-black text-slate-900">
                  {formatMoney(unitPrice)}
                </span>
              </div>
              {selectedStock.change && (
                <div className="flex items-center gap-1 text-xs font-bold text-emerald-700 bg-emerald-100/80 px-2.5 py-1 rounded-full">
                  <TrendingUp className="w-3.5 h-3.5" />
                  <span>{selectedStock.change}</span>
                </div>
              )}
            </div>

            {/* Order Type Toggle */}
            <div>
              <label className="block text-xs font-bold text-slate-700 mb-2">Order Type</label>
              <div className="grid grid-cols-2 gap-2 p-1 bg-slate-100 rounded-xl">
                <button
                  type="button"
                  onClick={() => setOrderType('delivery')}
                  className={`py-2 text-xs font-bold rounded-lg transition-all ${
                    orderType === 'delivery'
                      ? 'bg-white text-slate-900 shadow-xs'
                      : 'text-slate-500 hover:text-slate-800'
                  }`}
                >
                  Delivery (Long Term)
                </button>
                <button
                  type="button"
                  onClick={() => setOrderType('intraday')}
                  className={`py-2 text-xs font-bold rounded-lg transition-all ${
                    orderType === 'intraday'
                      ? 'bg-white text-slate-900 shadow-xs'
                      : 'text-slate-500 hover:text-slate-800'
                  }`}
                >
                  Intraday (Same Day)
                </button>
              </div>
            </div>

            {/* Quantity Selector */}
            <div>
              <div className="flex items-center justify-between mb-2">
                <label className="text-xs font-bold text-slate-700">Quantity (Shares)</label>
                <span className="text-[11px] text-slate-400 font-medium">Min: 1 share</span>
              </div>

              {/* Stepper Input */}
              <div className="flex items-center gap-3">
                <button
                  type="button"
                  onClick={() => handleQuantityChange(-1)}
                  disabled={quantity <= 1}
                  className="w-11 h-11 rounded-xl border border-slate-200 bg-white hover:bg-slate-50 flex items-center justify-center text-slate-700 disabled:opacity-40 disabled:cursor-not-allowed transition-colors active:scale-95"
                >
                  <Minus className="w-4 h-4" />
                </button>

                <div className="flex-1 relative">
                  <input
                    type="number"
                    min="1"
                    max="10000"
                    value={quantity}
                    onChange={handleCustomQuantity}
                    className="w-full text-center py-2.5 px-3 bg-white border border-slate-200 rounded-xl font-extrabold text-lg text-slate-900 focus:outline-hidden focus:border-emerald-500 focus:ring-2 focus:ring-emerald-100"
                  />
                  <span className="absolute right-3 top-1/2 -translate-y-1/2 text-xs text-slate-400 font-semibold pointer-events-none">
                    shares
                  </span>
                </div>

                <button
                  type="button"
                  onClick={() => handleQuantityChange(1)}
                  className="w-11 h-11 rounded-xl border border-slate-200 bg-white hover:bg-slate-50 flex items-center justify-center text-slate-700 transition-colors active:scale-95"
                >
                  <Plus className="w-4 h-4" />
                </button>
              </div>

              {/* Quick Add Chips */}
              <div className="flex items-center gap-2 mt-2.5">
                {[1, 5, 10, 25, 50].map((addAmount) => (
                  <button
                    key={addAmount}
                    type="button"
                    onClick={() => setQuantity(addAmount)}
                    className={`px-3 py-1 rounded-lg text-xs font-bold border transition-colors ${
                      quantity === addAmount
                        ? 'bg-emerald-50 border-emerald-300 text-emerald-800'
                        : 'bg-white border-slate-200 text-slate-600 hover:bg-slate-50'
                    }`}
                  >
                    {addAmount}
                  </button>
                ))}
              </div>
            </div>

            {/* Cost Breakdown */}
            <div className="p-4 bg-slate-50/80 rounded-2xl border border-slate-100 space-y-2 text-xs">
              <div className="flex justify-between text-slate-600">
                <span>
                  Share Price ({quantity} × {formatMoney(unitPrice)})
                </span>
                <span className="font-semibold text-slate-800">{formatMoney(totalAmount)}</span>
              </div>
              <div className="flex justify-between text-slate-600">
                <span>Brokerage</span>
                <span className="font-semibold text-emerald-600 flex items-center gap-1">
                  <span className="line-through text-slate-400">₹20</span> FREE
                </span>
              </div>
              <div className="flex justify-between text-slate-600">
                <span>Estimated Taxes & Charges</span>
                <span className="font-semibold text-emerald-600">₹0.00</span>
              </div>
              <div className="pt-2 border-t border-slate-200 flex justify-between text-sm font-extrabold text-slate-900">
                <span>Total Payable</span>
                <span className="text-[#00A87E]">{formatMoney(totalAmount)}</span>
              </div>
            </div>

            {/* Action Buttons */}
            <button
              type="button"
              onClick={() => setStep('payment')}
              className="w-full py-3.5 px-4 rounded-2xl bg-[#00D09C] hover:bg-[#00B887] text-white font-extrabold text-sm md:text-base transition-all shadow-md active:scale-98 flex items-center justify-center gap-2"
            >
              <span>Approve Order & Proceed to Pay</span>
              <ArrowRight className="w-4 h-4" />
            </button>
          </div>
        )}

        {/* ============================================================= */}
        {/* Step 2: Dummy Payment Simulation */}
        {/* ============================================================= */}
        {step === 'payment' && (
          <div className="p-6 overflow-y-auto space-y-5">
            {/* Sandbox Notice Banner */}
            <div className="p-3.5 bg-amber-50 border border-amber-200 rounded-2xl flex items-start gap-2.5 text-xs text-amber-900">
              <AlertCircle className="w-4 h-4 text-amber-600 shrink-0 mt-0.5" />
              <div>
                <span className="font-bold block">🧪 Sandbox Mode: Dummy Payment</span>
                <span>
                  This is a simulated transaction. No real money will be charged or deducted from
                  your bank account.
                </span>
              </div>
            </div>

            {/* Order Summary Pill */}
            <div className="p-4 bg-slate-50 rounded-2xl border border-slate-100 flex items-center justify-between">
              <div>
                <span className="text-[11px] font-bold text-slate-400 block uppercase">
                  Order Details
                </span>
                <span className="text-sm font-extrabold text-slate-800">
                  {quantity}x {selectedStock.symbol} ({orderType.toUpperCase()})
                </span>
              </div>
              <div className="text-right">
                <span className="text-[11px] font-bold text-slate-400 block uppercase">
                  Amount Due
                </span>
                <span className="text-lg font-black text-[#00A87E]">
                  {formatMoney(totalAmount)}
                </span>
              </div>
            </div>

            {/* Dummy Payment Methods */}
            <div>
              <label className="block text-xs font-bold text-slate-700 mb-2">
                Select Dummy Payment Method
              </label>
              <div className="space-y-2.5">
                <label
                  onClick={() => setPaymentMethod('groww_upi')}
                  className={`flex items-center justify-between p-3.5 rounded-xl border cursor-pointer transition-all ${
                    paymentMethod === 'groww_upi'
                      ? 'border-emerald-500 bg-emerald-50/50 shadow-xs'
                      : 'border-slate-200 bg-white hover:bg-slate-50'
                  }`}
                >
                  <div className="flex items-center gap-3">
                    <div className="w-8 h-8 rounded-lg bg-emerald-100 text-emerald-700 flex items-center justify-center">
                      <Smartphone className="w-4 h-4" />
                    </div>
                    <div>
                      <span className="text-xs font-bold text-slate-900 block">
                        Groww UPI (Instant 1-Click)
                      </span>
                      <span className="text-[11px] text-slate-500">Fastest sandbox approval</span>
                    </div>
                  </div>
                  <input
                    type="radio"
                    name="dummy_method"
                    checked={paymentMethod === 'groww_upi'}
                    onChange={() => setPaymentMethod('groww_upi')}
                    className="accent-emerald-600"
                  />
                </label>

                <label
                  onClick={() => setPaymentMethod('groww_balance')}
                  className={`flex items-center justify-between p-3.5 rounded-xl border cursor-pointer transition-all ${
                    paymentMethod === 'groww_balance'
                      ? 'border-emerald-500 bg-emerald-50/50 shadow-xs'
                      : 'border-slate-200 bg-white hover:bg-slate-50'
                  }`}
                >
                  <div className="flex items-center gap-3">
                    <div className="w-8 h-8 rounded-lg bg-blue-100 text-blue-700 flex items-center justify-center">
                      <Wallet className="w-4 h-4" />
                    </div>
                    <div>
                      <span className="text-xs font-bold text-slate-900 block">
                        Groww Wallet Balance
                      </span>
                      <span className="text-[11px] text-slate-500">
                        Available Balance: ₹50,000 (Dummy)
                      </span>
                    </div>
                  </div>
                  <input
                    type="radio"
                    name="dummy_method"
                    checked={paymentMethod === 'groww_balance'}
                    onChange={() => setPaymentMethod('groww_balance')}
                    className="accent-emerald-600"
                  />
                </label>

                <label
                  onClick={() => setPaymentMethod('netbanking')}
                  className={`flex items-center justify-between p-3.5 rounded-xl border cursor-pointer transition-all ${
                    paymentMethod === 'netbanking'
                      ? 'border-emerald-500 bg-emerald-50/50 shadow-xs'
                      : 'border-slate-200 bg-white hover:bg-slate-50'
                  }`}
                >
                  <div className="flex items-center gap-3">
                    <div className="w-8 h-8 rounded-lg bg-purple-100 text-purple-700 flex items-center justify-center">
                      <CreditCard className="w-4 h-4" />
                    </div>
                    <div>
                      <span className="text-xs font-bold text-slate-900 block">
                        NetBanking / Cards (Simulated)
                      </span>
                      <span className="text-[11px] text-slate-500">HDFC, ICICI, SBI sandbox</span>
                    </div>
                  </div>
                  <input
                    type="radio"
                    name="dummy_method"
                    checked={paymentMethod === 'netbanking'}
                    onChange={() => setPaymentMethod('netbanking')}
                    className="accent-emerald-600"
                  />
                </label>
              </div>
            </div>

            {errorMessage && (
              <div className="p-3 bg-rose-50 border border-rose-200 rounded-xl text-rose-700 text-xs font-medium">
                {errorMessage}
              </div>
            )}

            {/* Back & Pay CTA */}
            <div className="flex items-center gap-3 pt-2">
              <button
                type="button"
                onClick={() => setStep('configure')}
                disabled={isProcessing}
                className="py-3 px-4 rounded-xl border border-slate-200 text-slate-600 font-bold text-xs hover:bg-slate-50 transition-colors"
              >
                Back
              </button>

              <button
                type="button"
                onClick={handleExecuteDummyPayment}
                disabled={isProcessing}
                className="flex-1 py-3.5 px-4 rounded-xl bg-[#00D09C] hover:bg-[#00B887] text-white font-extrabold text-sm transition-all shadow-md active:scale-98 flex items-center justify-center gap-2 disabled:opacity-60"
              >
                {isProcessing ? (
                  <>
                    <Loader2 className="w-4 h-4 animate-spin" />
                    <span>Processing Dummy Payment...</span>
                  </>
                ) : (
                  <>
                    <ShieldCheck className="w-4 h-4" />
                    <span>Pay {formatMoney(totalAmount)} (Dummy)</span>
                  </>
                )}
              </button>
            </div>
          </div>
        )}

        {/* ============================================================= */}
        {/* Step 3: Success Screen & Confirmation */}
        {/* ============================================================= */}
        {step === 'success' && (
          <div className="p-8 text-center space-y-6 overflow-y-auto">
            {/* Animated Celebration Badge */}
            <div className="w-16 h-16 rounded-full bg-emerald-100 text-[#00A87E] mx-auto flex items-center justify-center shadow-lg border-2 border-emerald-200 animate-in zoom-in-75 duration-300">
              <CheckCircle2 className="w-9 h-9" />
            </div>

            <div>
              <h4 className="text-xl font-black text-slate-900">Order Executed Successfully! 🎉</h4>
              <p className="text-xs text-slate-500 mt-1">
                Your dummy order has been processed and saved to your real MongoDB portfolio.
              </p>
            </div>

            {/* Transaction Receipt */}
            <div className="p-5 bg-slate-50 rounded-2xl border border-slate-100 text-left space-y-3 text-xs">
              <div className="flex justify-between border-b border-slate-100 pb-2">
                <span className="text-slate-500">Order ID</span>
                <span className="font-mono font-bold text-slate-800">{orderId}</span>
              </div>
              <div className="flex justify-between border-b border-slate-100 pb-2">
                <span className="text-slate-500">Stock & Quantity</span>
                <span className="font-bold text-slate-900">
                  {quantity} shares of {selectedStock.symbol}
                </span>
              </div>
              <div className="flex justify-between border-b border-slate-100 pb-2">
                <span className="text-slate-500">Execution Price</span>
                <span className="font-bold text-slate-800">{formatMoney(unitPrice)}</span>
              </div>
              <div className="flex justify-between border-b border-slate-100 pb-2">
                <span className="text-slate-500">Payment Status</span>
                <span className="font-bold text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded-md">
                  COMPLETED (Dummy)
                </span>
              </div>
              <div className="flex justify-between pt-1 text-sm font-extrabold text-slate-900">
                <span>Total Debited</span>
                <span className="text-[#00A87E]">{formatMoney(totalAmount)}</span>
              </div>
            </div>

            {/* Next Step CTAs */}
            <div className="space-y-2.5">
              <button
                type="button"
                onClick={handleViewPortfolio}
                className="w-full py-3.5 px-4 rounded-xl bg-slate-900 hover:bg-slate-800 text-white font-extrabold text-xs md:text-sm transition-all shadow-md active:scale-98 flex items-center justify-center gap-2"
              >
                <Briefcase className="w-4 h-4 text-emerald-400" />
                <span>View in Portfolio Dashboard</span>
              </button>

              <button
                type="button"
                onClick={closeBuyModal}
                className="w-full py-2.5 px-4 rounded-xl text-slate-600 hover:text-slate-900 hover:bg-slate-100 font-bold text-xs transition-colors"
              >
                Done / Trade More
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default StockPurchaseModal;
