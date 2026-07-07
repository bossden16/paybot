import React, { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { client } from '@/lib/api';
import { Card, CardContent, CardHeader, CardTitle, CardFooter } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import {
  ShieldCheck,
  Lock,
  CreditCard,
  Wallet,
  QrCode,
  ArrowRight,
  CheckCircle2,
  Clock,
  AlertCircle,
  ChevronRight,
  ExternalLink,
  Bot
} from 'lucide-react';
import { toast } from 'sonner';
import AppLoadingScreen from '@/components/AppLoadingScreen';
import { APP_NAME } from '@/lib/brand';

interface Transaction {
  id: number;
  transaction_type: string;
  external_id: string;
  amount: number;
  currency: string;
  status: string;
  description: string;
  customer_name: string;
  payment_url: string;
  qr_code_url: string;
  merchant_name?: string;
  created_at: string;
}

export default function Checkout() {
  const { externalId } = useParams<{ externalId: string }>();
  const [txn, setTxn] = useState<Transaction | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function fetchTransaction() {
      if (!externalId) return;
      try {
        setLoading(true);
        // We use a public endpoint if available, otherwise fallback to standard query
        // Since we don't have a specific public 'get by external_id' endpoint in the prompt context,
        // we'll assume we can query the transactions entity or use a specialized route.
        const res = await client.entities.transactions.query({
          query: { external_id: externalId },
          limit: 1
        });

        if (res.data?.items && res.data.items.length > 0) {
          setTxn(res.data.items[0] as Transaction);
        } else {
          setError('Transaction not found');
        }
      } catch (err) {
        console.error('Checkout fetch error:', err);
        setError('Failed to load payment details');
      } finally {
        setLoading(false);
      }
    }
    fetchTransaction();
  }, [externalId]);

  if (loading) return <AppLoadingScreen />;

  if (error || !txn) {
    return (
      <div className="min-h-screen bg-[#080E1A] text-white flex flex-col items-center justify-center p-6 text-center">
        <div className="h-16 w-16 bg-red-500/10 rounded-full flex items-center justify-center mb-6 border border-red-500/20">
          <AlertCircle className="h-8 w-8 text-red-400" />
        </div>
        <h1 className="text-2xl font-bold mb-2">Payment Not Found</h1>
        <p className="text-slate-400 max-w-xs mb-8">{error || "The requested payment link is invalid or has expired."}</p>
        <Button asChild variant="outline" className="rounded-xl border-white/10 bg-white/5 text-slate-300">
          <Link to="/home">Go to {APP_NAME}</Link>
        </Button>
      </div>
    );
  }

  const isPaid = txn.status === 'paid';
  const isExpired = txn.status === 'expired' || txn.status === 'cancelled';
  const isPending = txn.status === 'pending';

  return (
    <div className="min-h-screen bg-[#080E1A] text-white selection:bg-blue-500/30">
      {/* Header */}
      <header className="border-b border-white/[0.05] bg-white/[0.02] backdrop-blur-md sticky top-0 z-50">
        <div className="max-w-4xl mx-auto px-6 h-16 flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <div className="h-8 w-8 bg-blue-600 rounded-lg flex items-center justify-center shadow-lg shadow-blue-600/20">
              <Bot className="h-4.5 w-4.5 text-white" />
            </div>
            <span className="font-bold tracking-tight text-lg">{APP_NAME} <span className="text-blue-400 font-medium">Checkout</span></span>
          </div>
          <div className="flex items-center gap-1.5 text-[10px] uppercase tracking-[0.2em] text-slate-500 font-semibold">
            <ShieldCheck className="h-3 w-3 text-emerald-500" />
            Secure Payment
          </div>
        </div>
      </header>

      <main className="max-w-4xl mx-auto px-6 py-12 md:py-20">
        <div className="grid grid-cols-1 lg:grid-cols-[1fr_0.8fr] gap-8 items-start">

          {/* Main Checkout Section */}
          <div className="space-y-6">
            <div className="space-y-2">
              <h2 className="text-sm font-semibold uppercase tracking-[0.3em] text-slate-500">Order Summary</h2>
              <div className="flex items-baseline gap-2">
                <span className="text-4xl font-black tracking-tight">₱ {txn.amount.toLocaleString('en-PH', { minimumFractionDigits: 2 })}</span>
                <span className="text-slate-400 font-medium">{txn.currency}</span>
              </div>
            </div>

            <Card className="border-white/[0.08] bg-white/[0.03] overflow-hidden rounded-[1.5rem]">
              <div className="h-1.5 w-full bg-gradient-to-r from-blue-600 via-indigo-600 to-cyan-500" />
              <CardContent className="p-8">
                <div className="space-y-6">
                  <div className="flex justify-between items-start border-b border-white/[0.05] pb-6">
                    <div>
                      <p className="text-xs text-slate-500 uppercase tracking-wider mb-1">Merchant</p>
                      <p className="text-lg font-bold text-white">{txn.merchant_name || 'PayBot Merchant'}</p>
                    </div>
                    <Badge className={isPaid ? "bg-emerald-500/20 text-emerald-400 border-emerald-500/30" : "bg-amber-500/20 text-amber-400 border-amber-500/30"}>
                      {isPaid ? <CheckCircle2 className="h-3 w-3 mr-1" /> : <Clock className="h-3 w-3 mr-1" />}
                      {txn.status.toUpperCase()}
                    </Badge>
                  </div>

                  <div className="space-y-4">
                    <div>
                      <p className="text-xs text-slate-500 uppercase tracking-wider mb-2">Description</p>
                      <p className="text-sm text-slate-300 leading-relaxed">
                        {txn.description || "Digital transaction via PayBot Hub"}
                      </p>
                    </div>

                    <div className="grid grid-cols-2 gap-4 pt-2">
                      <div>
                        <p className="text-xs text-slate-500 uppercase tracking-wider mb-1">Reference</p>
                        <code className="text-xs text-blue-300 bg-blue-500/10 px-2 py-0.5 rounded">{txn.external_id}</code>
                      </div>
                      <div>
                        <p className="text-xs text-slate-500 uppercase tracking-wider mb-1">Date</p>
                        <p className="text-xs text-slate-300">{new Date(txn.created_at).toLocaleDateString('en-PH', { month: 'short', day: 'numeric', year: 'numeric' })}</p>
                      </div>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>

            {isPending && (
              <div className="space-y-4">
                <p className="text-sm font-medium text-slate-400 px-1">Complete your payment using:</p>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                  {txn.payment_url && (
                    <a href={txn.payment_url} target="_blank" rel="noopener noreferrer" className="group">
                      <div className="h-full rounded-2xl border border-white/[0.08] bg-white/[0.04] p-5 transition-all hover:bg-blue-600/10 hover:border-blue-500/40">
                        <div className="flex items-center gap-4">
                          <div className="h-10 w-10 rounded-xl bg-blue-500/20 flex items-center justify-center text-blue-400 group-hover:scale-110 transition-transform">
                            <CreditCard className="h-5 w-5" />
                          </div>
                          <div className="flex-1">
                            <p className="font-bold text-white">Direct Payment</p>
                            <p className="text-[11px] text-slate-500">Cards, E-Wallets, Bank Transfer</p>
                          </div>
                          <ChevronRight className="h-4 w-4 text-slate-600 group-hover:text-blue-400 transition-colors" />
                        </div>
                      </div>
                    </a>
                  )}
                  {txn.qr_code_url && (
                    <div className="rounded-2xl border border-white/[0.08] bg-white/[0.04] p-5 cursor-pointer hover:bg-purple-600/10 hover:border-purple-500/40 transition-all group">
                      <div className="flex items-center gap-4">
                        <div className="h-10 w-10 rounded-xl bg-purple-500/20 flex items-center justify-center text-purple-400 group-hover:scale-110 transition-transform">
                          <QrCode className="h-5 w-5" />
                        </div>
                        <div className="flex-1">
                          <p className="font-bold text-white">QR Code</p>
                          <p className="text-[11px] text-slate-500">Scan via any QRPH App</p>
                        </div>
                        <ChevronRight className="h-4 w-4 text-slate-600 group-hover:text-purple-400 transition-colors" />
                      </div>
                    </div>
                  )}
                </div>

                <Button asChild size="lg" className="w-full h-14 rounded-2xl bg-blue-600 text-white hover:bg-blue-500 font-bold text-lg shadow-xl shadow-blue-600/20">
                  <a href={txn.payment_url || "#"} target="_blank" rel="noopener noreferrer">
                    Pay Now <ArrowRight className="h-5 w-5 ml-2" />
                  </a>
                </Button>
              </div>
            )}

            {isPaid && (
              <div className="rounded-[1.5rem] bg-emerald-500/10 border border-emerald-500/20 p-8 text-center space-y-4 animate-fade-in">
                <div className="h-16 w-16 bg-emerald-500/20 rounded-full flex items-center justify-center mx-auto border border-emerald-500/30">
                  <CheckCircle2 className="h-8 w-8 text-emerald-400" />
                </div>
                <div>
                  <h3 className="text-xl font-bold text-white">Payment Successful</h3>
                  <p className="text-slate-400 mt-1">Thank you for your business. Your transaction is complete.</p>
                </div>
                <div className="pt-4 flex justify-center gap-3">
                  <Button variant="outline" className="rounded-xl border-white/10 bg-white/5">
                    View Receipt
                  </Button>
                  <Button asChild className="rounded-xl bg-blue-600">
                    <Link to="/home">Return Home</Link>
                  </Button>
                </div>
              </div>
            )}

            {isExpired && (
              <div className="rounded-[1.5rem] bg-red-500/10 border border-red-500/20 p-8 text-center space-y-4">
                <div className="h-16 w-16 bg-red-500/20 rounded-full flex items-center justify-center mx-auto border border-red-500/30">
                  <Clock className="h-8 w-8 text-red-400" />
                </div>
                <div>
                  <h3 className="text-xl font-bold text-white">Link Expired</h3>
                  <p className="text-slate-400 mt-1">This payment link is no longer active. Please contact the merchant for a new link.</p>
                </div>
                <Button asChild variant="outline" className="rounded-xl border-white/10">
                  <Link to="/home">Go to {APP_NAME}</Link>
                </Button>
              </div>
            )}
          </div>

          {/* Side Info */}
          <div className="space-y-6">
            <Card className="border-white/[0.08] bg-white/[0.02] backdrop-blur rounded-3xl overflow-hidden">
              <CardHeader className="pb-2">
                <CardTitle className="text-xs uppercase tracking-[0.2em] text-slate-500">Security Details</CardTitle>
              </CardHeader>
              <CardContent className="space-y-6 p-6">
                <div className="flex gap-4">
                  <div className="h-10 w-10 shrink-0 rounded-xl bg-white/[0.05] flex items-center justify-center">
                    <Lock className="h-4.5 w-4.5 text-slate-400" />
                  </div>
                  <div>
                    <p className="text-sm font-semibold text-slate-200">End-to-End Encryption</p>
                    <p className="text-[11px] text-slate-500 mt-1">Your data is secured using industry-standard AES-256 encryption protocol.</p>
                  </div>
                </div>
                <div className="flex gap-4">
                  <div className="h-10 w-10 shrink-0 rounded-xl bg-white/[0.05] flex items-center justify-center">
                    <ShieldCheck className="h-4.5 w-4.5 text-slate-400" />
                  </div>
                  <div>
                    <p className="text-sm font-semibold text-slate-200">Verified Gateway</p>
                    <p className="text-[11px] text-slate-500 mt-1">PCI DSS compliant processing through regulated financial channels.</p>
                  </div>
                </div>
              </CardContent>
            </Card>

            <div className="p-6 text-center space-y-4">
              <p className="text-[10px] text-slate-600 uppercase tracking-widest leading-relaxed">
                Licensed and regulated by the Bangko Sentral ng Pilipinas
              </p>
              <div className="flex justify-center items-center gap-4 opacity-30 grayscale hover:opacity-60 transition-opacity cursor-default">
                <img src="/logos/gcash.svg" alt="GCash" className="h-4" />
                <img src="/logos/maya.svg" alt="Maya" className="h-4" />
                <img src="/logos/visa.svg" alt="Visa" className="h-5" />
                <img src="/logos/mastercard.svg" alt="Mastercard" className="h-5" />
              </div>
            </div>
          </div>

        </div>
      </main>

      <footer className="max-w-4xl mx-auto px-6 py-12 border-t border-white/[0.05] text-center">
        <p className="text-xs text-slate-500">
          Powered by <span className="font-bold text-slate-400">{APP_NAME} Philippines</span>
        </p>
        <div className="mt-4 flex justify-center gap-6 text-[10px] font-medium text-slate-600 uppercase tracking-widest">
          <Link to="/policies" className="hover:text-blue-400 transition-colors">Privacy Policy</Link>
          <Link to="/policies" className="hover:text-blue-400 transition-colors">Terms of Service</Link>
          <a href="mailto:support@paybot.ph" className="hover:text-blue-400 transition-colors">Contact Support</a>
        </div>
      </footer>
    </div>
  );
}
