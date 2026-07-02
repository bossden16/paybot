import Layout from '../components/Layout';
import { POSTerminalAdminPanel } from '../components/POSTerminalAdmin';

export default function POSTerminalsPage() {
  return (
    <Layout>
      <div className="mx-auto w-full max-w-7xl p-4">
        <POSTerminalAdminPanel />
      </div>
    </Layout>
  );
}
