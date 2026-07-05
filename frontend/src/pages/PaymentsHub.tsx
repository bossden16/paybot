import { useState, useEffect } from 'react';
import { useAuth } from '@/contexts/AuthContext';
import { usePaymentEvents } from '@/hooks/usePaymentEvents';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Tabs, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { FileText, QrCode, LinkIcon, Plus, Loader2, CheckCircle, Copy, ExternalLink, CreditCard } from 'lucide-react';
import { toast } from 'sonner';
import Layout from '@/components/Layout';

const tabConfig = {
  invoice: { icon: <FileText className="h-4 w-4" />, label: 'Invoice', color: 'text-blue-400' },
  qr_code: { icon: <QrCode className="h-4 w-4" />, label: 'QR Code', color: 'text-purple-400' },
  payment_link: { icon: <LinkIcon className="h-4 w-4" />, label: 'Payment Link', color: 'text-cyan-400' },
  checkout_session: { icon: <CreditCard className="h-4 w-4" />, label: 'Checkout Session', color: 'text-emerald-400' },
};

export default function PaymentsHub() {
  const { user, permissions, isSuperAdmin } = useAuth();
  const [tab, setTab] = useState('invoice');
  const [amount, setAmount] = useState('');
  const [description, setDescription] = useState('');
  const [customerName, setCustomerName] = useState('');
  const [customerEmail, setCustomerEmail] = useState('');
  const [apiKey, setApiKey] = useState(localStorage.getItem('payment_api_key') || '');
  const [successUrl, setSuccessUrl] = useState('');
  const [cancelUrl, setCancelUrl] = useState('');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<Record<string, unknown> | null>(null);

  usePaymentEvents({ enabled: !!user });
  const canAccessPayments = Boolean(isSuperAdmin || permissions?.can_manage_payments);

  useEffect(() => {
    if (apiKey.trim()) {
      localStorage.setItem('payment_api_key', apiKey.trim());
    }
  }, [apiKey]);

  const resetForm = () => {
    setAmount('');
    setDescription('');
    setCustomerName('');
    setCustomerEmail('');
    setSuccessUrl('');
    setCancelUrl('');
    setResult(null);
  };

  const buildPayload = () => {
    const value = parseFloat(amount);

    if (tab === 'invoice') {
      return {
        endpoint: '/api/v1/magpie/create-invoice',
        payload: { amount: value, description, customer_name: customerName, customer_email: customerEmail },
      };
    }

    if (tab === 'qr_code') {
      return {
        endpoint: '/api/v1/magpie/create-qr-code',
        payload: { amount: value, description },
      };
    }

    if (tab === 'payment_link') {
      return {
        endpoint: '/api/v1/magpie/create-payment-link',
        payload: { amount: value, description, customer_name: customerName, customer_email: customerEmail },
      };
    }

    return {
      endpoint: '/api/v1/magpie/checkout/sessions',
      payload: {
        amount: value,
        payment_method_types: ['card', 'gcash', 'maya'],
        line_items: [{ name: description || 'Payment', amount: Math.round(value * 100), quantity: 1 }],
        mode: 'payment',
        success_url: successUrl || `${window.location.origin}/magpie-success`,
        cancel_url: cancelUrl || `${window.location.origin}/`,
        currency: 'php',
        customer_email: customerEmail,
        description,
      },
    };
  };

  const handleCreate = async () => {
    if (!canAccessPayments) {
      toast.error('You do not have permission to create payments.');
      return;
    }

    const value = parseFloat(amount);
    if (Number.isNaN(value) || value <= 0) {
      toast.error('Enter a valid amount greater than zero.');
      return;
    }

    setLoading(true);
    setResult(null);

    try {
      const { endpoint, payload } = buildPayload();
      const res = await fetch(endpoint, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(localStorage.getItem('auth_token') ? { Authorization: `Bearer ${localStorage.getItem('auth_token')}` } : {}),
          ...(apiKey.trim() ? { 'X-API-Key': apiKey.trim() } : {}),
        },
        body: JSON.stringify(payload),
      });

      const data = await res.json();
      if (!res.ok) {
        toast.error(data?.detail || data?.message || `Error ${res.status}`);
        return;
      }

      if (!data?.success) {
        toast.error(data?.message || 'Payment creation failed.');
        return;
      }

      setResult(data.data || data);
      toast.success(data.message || 'Payment created successfully!');
    } catch (err: unknown) {
      toast.error((err as Error)?.message || 'Failed to create payment.');
    } finally {
      setLoading(false);
    }
  };

  const copyText = (text: string) => {
    navigator.clipboard.writeText(text);
    toast.success('Copied to clipboard');
  };

  if (!canAccessPayments) {
    return (
      <Layout>
        <div className="max-w-3xl mx-auto rounded-3xl border border-red-200 bg-red-50/80 p-10 text-center shadow-sm">
          <h1 className="text-3xl font-semibold text-red-700">Payments Access Restricted</h1>
          <p className="mt-4 text-sm text-red-600">You need payment management permission to use the Payments Hub.</p>
        </div>
      </Layout>
    );
  }

  const activeTab = tabConfig[tab];

  return (
    <Layout>
      <div className="max-w-6xl mx-auto py-8">
        <div className="mb-8 flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
          <div>
            <h1 className="text-3xl font-bold text-foreground">Payments Hub</h1>
            <p className="mt-2 max-w-2xl text-sm text-muted-foreground">
              Create invoices, payment links, QR codes, or checkout sessions for your customers in one place.
            </p>
          </div>
          <div className="rounded-2xl border border-border bg-muted p-4 text-sm text-slate-400">
            Active mode: <span className="font-semibold text-foreground">{activeTab.label}</span>
          </div>
        </div>

        <Tabs value={tab} onValueChange={(value) => { setTab(value); setResult(null); }}>
          <TabsList className="grid grid-cols-2 md:grid-cols-4 gap-2 rounded-3xl border border-border bg-muted p-2">
            {Object.entries(tabConfig).map(([key, cfg]) => (
              <TabsTrigger key={key} value={key} className="flex items-center justify-center gap-2 rounded-2xl px-3 py-3 text-sm font-medium text-muted-foreground data-[state=active]:bg-background data-[state=active]:text-foreground">
                <span className={cfg.color}>{cfg.icon}</span>
                {cfg.label}
              </TabsTrigger>
            ))}
          </TabsList>

          <div className="mt-6 grid gap-6 lg:grid-cols-[1.25fr_0.95fr]">
            <Card className="bg-card border-border">
              <CardHeader>
                <CardTitle className="text-foreground">Create {activeTab.label}</CardTitle>
              </CardHeader>
              <CardContent className="space-y-5">
                <div>
                  <Label className="text-muted-foreground">Amount (PHP)</Label>
                  <Input
                    type="number"
                    step="0.01"
                    min="1"
                    placeholder="100.00"
                    value={amount}
                    onChange={(e) => setAmount(e.target.value)}
                    className="mt-2 bg-muted border-border text-foreground placeholder:text-muted-foreground"
                  />
                </div>

                {(tab === 'invoice' || tab === 'qr_code' || tab === 'payment_link') ? (
                  <div>
                    <Label className="text-muted-foreground">Description</Label>
                    <Textarea
                      placeholder="Payment description..."
                      value={description}
                      onChange={(e) => setDescription(e.target.value)}
                      className="mt-2 bg-muted border-border text-foreground placeholder:text-muted-foreground resize-none"
                      rows={3}
                    />
                  </div>
                ) : (
                  <div className="space-y-4">
                    <div>
                      <Label className="text-muted-foreground">Session description</Label>
                      <Textarea
                        placeholder="Checkout session description"
                        value={description}
                        onChange={(e) => setDescription(e.target.value)}
                        className="mt-2 bg-muted border-border text-foreground placeholder:text-muted-foreground resize-none"
                        rows={3}
                      />
                    </div>
                    <div>
                      <Label className="text-muted-foreground">Success URL</Label>
                      <Input
                        placeholder="https://your-app.example.com/magpie-success"
                        value={successUrl}
                        onChange={(e) => setSuccessUrl(e.target.value)}
                        className="mt-2 bg-muted border-border text-foreground placeholder:text-muted-foreground"
                      />
                      <p className="text-xs text-muted-foreground mt-2">If empty, defaults to <code>{`${window.location.origin}/magpie-success`}</code>.</p>
                    </div>
                    <div>
                      <Label className="text-muted-foreground">Cancel URL</Label>
                      <Input
                        placeholder="https://your-app.example.com/cancel"
                        value={cancelUrl}
                        onChange={(e) => setCancelUrl(e.target.value)}
                        className="mt-2 bg-muted border-border text-foreground placeholder:text-muted-foreground"
                      />
                      <p className="text-xs text-muted-foreground mt-2">If empty, this defaults to your app root.</p>
                    </div>
                  </div>
                )}

                <div>
                  <Label className="text-muted-foreground">Magpie / Xend API Key (optional)</Label>
                  <Input
                    placeholder="xend_live_..."
                    value={apiKey}
                    onChange={(e) => setApiKey(e.target.value)}
                    className="mt-2 bg-muted border-border text-foreground placeholder:text-muted-foreground"
                  />
                  <p className="text-xs text-muted-foreground mt-2">Optional key for direct Magpie auth. Leave blank to use the session token.</p>
                </div>

                {(tab === 'invoice' || tab === 'payment_link') && (
                  <div className="grid gap-4 md:grid-cols-2">
                    <div>
                      <Label className="text-muted-foreground">Customer Name</Label>
                      <Input
                        placeholder="John Doe"
                        value={customerName}
                        onChange={(e) => setCustomerName(e.target.value)}
                        className="mt-2 bg-muted border-border text-foreground placeholder:text-muted-foreground"
                      />
                    </div>
                    <div>
                      <Label className="text-muted-foreground">Customer Email</Label>
                      <Input
                        type="email"
                        placeholder="john@example.com"
                        value={customerEmail}
                        onChange={(e) => setCustomerEmail(e.target.value)}
                        className="mt-2 bg-muted border-border text-foreground placeholder:text-muted-foreground"
                      />
                    </div>
                  </div>
                )}

                <div className="flex flex-col gap-3 sm:flex-row">
                  <Button onClick={handleCreate} disabled={loading} className="flex-1 bg-blue-600 hover:bg-blue-700 text-white">
                    {loading ? <><Loader2 className="h-4 w-4 mr-2 animate-spin" />Creating...</> : <><Plus className="h-4 w-4 mr-2" />Create payment</>}
                  </Button>
                  <Button variant="secondary" onClick={resetForm} disabled={loading} className="border-muted text-foreground">
                    Reset form
                  </Button>
                </div>
              </CardContent>
            </Card>

            <Card className="bg-card border-border">
              <CardHeader>
                <CardTitle className="text-foreground">Result</CardTitle>
              </CardHeader>
              <CardContent>
                {!result ? (
                  <div className="text-center py-16">
                    <CreditCard className="h-16 w-16 text-muted-foreground mx-auto mb-4" />
                    <p className="text-sm text-muted-foreground">Your payment details will appear here after creation.</p>
                  </div>
                ) : (
                  <div className="space-y-5">
                    <div className="rounded-2xl border border-emerald-500/20 bg-emerald-500/5 p-4 text-emerald-600">
                      <div className="flex items-center gap-2 font-semibold">
                        <CheckCircle className="h-5 w-5" /> Payment created successfully
                      </div>
                    </div>
                    <div className="space-y-4">
                      {Object.entries(result).map(([key, value]) => {
                        if (!value || key === 'success') return null;
                        const stringValue = String(value);
                        const isUrl = stringValue.startsWith('http');
                        return (
                          <div key={key} className="space-y-1 rounded-2xl border border-border bg-muted p-3">
                            <div className="text-xs uppercase tracking-[0.25em] text-muted-foreground">{key.replace(/_/g, ' ')}</div>
                            <div className="flex flex-wrap items-center gap-2">
                              {isUrl ? (
                                <a href={stringValue} target="_blank" rel="noopener noreferrer" className="break-all text-sm text-blue-400 hover:text-blue-300 underline">
                                  {stringValue}
                                </a>
                              ) : (
                                <code className="break-all text-sm font-mono text-foreground">{stringValue}</code>
                              )}
                              <Button variant="ghost" size="icon" onClick={() => copyText(stringValue)}>
                                <Copy className="h-4 w-4" />
                              </Button>
                              {isUrl && (
                                <a
                                  href={stringValue}
                                  target="_blank"
                                  rel="noopener noreferrer"
                                  title="Open link in new tab"
                                  className="text-muted-foreground hover:text-foreground"
                                >
                                  <ExternalLink className="h-4 w-4" />
                                </a>
                              )}
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>
          </div>
        </Tabs>
      </div>
    </Layout>
  );
}
