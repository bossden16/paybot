import { useLocation, Link } from 'react-router-dom';
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from '@/components/ui/card';
import { Button } from '@/components/ui/button';

function useQuery() {
  const { search } = useLocation();
  return React.useMemo(() => new URLSearchParams(search), [search]);
}

import React from 'react';

export default function MagpieSuccess() {
  const query = useQuery();
  const session = query.get('session_id') || query.get('checkout_id') || query.get('external_id') || '';
  const paymentUrl = query.get('payment_url') || query.get('checkout_url') || '';
  const amount = query.get('amount') || '';

  return (
    <div className="min-h-screen bg-[#0F172A] flex items-center justify-center p-6">
      <Card className="max-w-xl w-full">
        <CardHeader>
          <CardTitle>Payment Successful</CardTitle>
          <CardDescription>Thanks — we received your payment. Below are the details.</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="text-sm text-slate-300 space-y-3">
            {session && <div><strong className="text-white">Session</strong>: {session}</div>}
            {amount && <div><strong className="text-white">Amount</strong>: {amount}</div>}
            {paymentUrl && (
              <div>
                <strong className="text-white">Payment URL</strong>: <a className="text-blue-400 hover:underline" href={paymentUrl} target="_blank" rel="noreferrer">Open</a>
              </div>
            )}
          </div>
        </CardContent>
        <CardFooter>
          <div className="flex gap-3 w-full">
            {paymentUrl ? (
              <a href={paymentUrl} target="_blank" rel="noreferrer" className="flex-1">
                <Button className="w-full">Open Payment Page</Button>
              </a>
            ) : (
              <Link to="/" className="flex-1">
                <Button className="w-full">Return to Dashboard</Button>
              </Link>
            )}
            <Link to="/" className="flex-1">
              <Button variant="outline" className="w-full">Go Home</Button>
            </Link>
          </div>
        </CardFooter>
      </Card>
    </div>
  );
}
