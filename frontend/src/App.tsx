import { Toaster } from '@/components/ui/sonner';
import { TooltipProvider } from '@/components/ui/tooltip';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { BrowserRouter, Routes, Route, useLocation, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from '@/contexts/AuthContext';
import { ThemeProvider } from '@/contexts/ThemeContext';
import { LanguageProvider } from '@/contexts/LanguageContext';
import React, { useEffect, useState, Suspense } from 'react';
import TopProgressBar from '@/components/TopProgressBar';
import AppLoadingScreen from '@/components/AppLoadingScreen';

// Lazy load all pages to isolate the main bundle from page-level errors
const Dashboard = React.lazy(() => import('./pages/Dashboard'));
const Wallet = React.lazy(() => import('./pages/Wallet'));
const Transactions = React.lazy(() => import('./pages/Transactions'));
const CreatePayment = React.lazy(() => import('./pages/CreatePayment'));
const QRCodesPage = React.lazy(() => import('./pages/QRCodesPage'));
const ScanQRPH = React.lazy(() => import('./pages/ScanQRPH'));
const DisbursementsPage = React.lazy(() => import('./pages/DisbursementsPage'));
const ReportsPage = React.lazy(() => import('./pages/ReportsPage'));
const BotSettings = React.lazy(() => import('./pages/BotSettings'));
const Settings = React.lazy(() => import('./pages/Settings'));
const MessengerPage = React.lazy(() => import('./pages/MessengerPage'));
const AdminManagement = React.lazy(() => import('./pages/AdminManagement'));
const BotMessagesPage = React.lazy(() => import('./pages/BotMessagesPage'));
const TopupRequestsPage = React.lazy(() => import('./pages/TopupRequestsPage'));
const UsdtSendRequestsPage = React.lazy(() => import('./pages/UsdtSendRequestsPage'));
const BankDepositsPage = React.lazy(() => import('./pages/BankDepositsPage'));
const KybRegistrationsPage = React.lazy(() => import('./pages/KybRegistrationsPage'));
const KycVerificationsPage = React.lazy(() => import('./pages/KycVerificationsPage'));
const RolesPage = React.lazy(() => import('./pages/RolesPage'));
const Policies = React.lazy(() => import('./pages/Policies'));
const Compliance = React.lazy(() => import('./pages/Compliance'));
const Features = React.lazy(() => import('./pages/Features'));
const Pricing = React.lazy(() => import('./pages/Pricing'));
const Login = React.lazy(() => import('./pages/Login'));
const Register = React.lazy(() => import('./pages/Register'));
const AuthCallback = React.lazy(() => import('./pages/AuthCallback'));
const AuthError = React.lazy(() => import('./pages/AuthError'));
const LogoutCallbackPage = React.lazy(() => import('./pages/LogoutCallbackPage'));
const NotFound = React.lazy(() => import('./pages/NotFound'));
const MaintenancePage = React.lazy(() => import('./pages/MaintenancePage'));
const BotIntro = React.lazy(() => import('./pages/BotIntro'));
const HomePage = React.lazy(() => import('./pages/Index'));
const MagpieSuccess = React.lazy(() => import('./pages/MagpieSuccess'));
const Checkout = React.lazy(() => import('./pages/Checkout'));

const RequireSuperAdmin = React.lazy(() => import('./components/RequireSuperAdmin'));
const RequireDeveloperRole = React.lazy(() => import('./components/RequireDeveloperRole'));
const ProtectedAdminRoute = React.lazy(() => import('./components/ProtectedAdminRoute'));

const queryClient = new QueryClient();

// Paths that should remain accessible even during maintenance
const MAINTENANCE_EXEMPT_PATHS = ['/home', '/intro', '/login', '/register', '/features', '/pricing', '/auth/callback', '/auth/error', '/logout-callback', '/maintenance', '/checkout'];

function MaintenanceGuard({ children }: { children: React.ReactNode }) {
  const [maintenanceMode, setMaintenanceMode] = useState(false);
  const location = useLocation();

  useEffect(() => {
    fetch('/api/v1/app-settings/maintenance')
      .then((r) => r.json())
      .then((data) => {
        setMaintenanceMode(!!data.maintenance_mode);
      })
      .catch((err) => {
        console.warn('Maintenance mode check failed:', err);
        setMaintenanceMode(false);
      });
  }, [location.pathname]);

  const isExempt = MAINTENANCE_EXEMPT_PATHS.some((p) => location.pathname === p || location.pathname.startsWith(p + '/'));

  if (maintenanceMode && !isExempt) {
    return <Navigate to="/maintenance" replace />;
  }

  return <>{children}</>;
}

// Wraps children in a div that re-mounts (and fades in) on every route change
function PageFade({ children }: { children: React.ReactNode }) {
  const location = useLocation();
  return (
    <div key={location.key} className="page-enter">
      {children}
    </div>
  );
}

/**
 * Renders the full app shell only after the initial auth check completes.
 * Must be rendered inside BrowserRouter so TopProgressBar / PageFade can call useLocation().
 * The AppLoadingScreen plays an exit animation before it is unmounted.
 */
function AuthAwareShell() {
  const { loading } = useAuth();
  const [showLoader, setShowLoader] = useState(true);
  const [exitingLoader, setExitingLoader] = useState(false);

  useEffect(() => {
    if (!loading && showLoader && !exitingLoader) {
      // Start the exit animation, then unmount after it completes.
      setExitingLoader(true);
      const t = setTimeout(() => setShowLoader(false), 450);
      return () => clearTimeout(t);
    }
  }, [loading, showLoader, exitingLoader]);

  if (showLoader) return <AppLoadingScreen exiting={exitingLoader} />;

  return (
    <>
      <TopProgressBar />
      {/* MaintenanceGuard is intentionally outside PageFade so it does not
          remount (and re-fetch) on every navigation. */}
      <MaintenanceGuard>
        <PageFade>
          <Suspense fallback={<AppLoadingScreen />}>
            <Routes>
              <Route path="/home" element={<HomePage />} />
              <Route path="/intro" element={<BotIntro />} />
              <Route path="/login" element={<Login />} />
              <Route path="/register" element={<Register />} />
              <Route path="/features" element={<Features />} />
              <Route path="/pricing" element={<Pricing />} />
              <Route path="/auth/callback" element={<AuthCallback />} />
              <Route path="/auth/error" element={<AuthError />} />
              <Route path="/logout-callback" element={<LogoutCallbackPage />} />
              <Route path="/maintenance" element={<MaintenancePage />} />
              <Route path="/" element={<Dashboard />} />
              <Route path="/wallet" element={<Wallet />} />
              <Route path="/transactions" element={<Transactions />} />
              <Route path="/payments" element={<CreatePayment />} />
              <Route path="/create-payment" element={<CreatePayment />} />
              <Route path="/qr-codes" element={<QRCodesPage />} />
              <Route path="/scan-qrph" element={<ScanQRPH />} />
              <Route path="/disbursements" element={<DisbursementsPage />} />
              <Route path="/reports" element={<ReportsPage />} />
              <Route path="/bot-settings" element={<BotSettings />} />
              <Route path="/settings" element={<Settings />} />
              <Route path="/messenger" element={<MessengerPage />} />
              <Route path="/developer-experience" element={<DeveloperExperience />} />
              <Route path="/api-docs" element={<ApiDocsPage />} />
              <Route path="/admin-management" element={<AdminManagement />} />
              <Route path="/bot-messages" element={<BotMessagesPage />} />
              <Route path="/topup-requests" element={<TopupRequestsPage />} />
              <Route path="/usdt-send-requests" element={<UsdtSendRequestsPage />} />
              <Route path="/bank-deposits" element={<BankDepositsPage />} />
              <Route path="/kyb-registrations" element={<KybRegistrationsPage />} />
              <Route path="/kyc-verifications" element={<KycVerificationsPage />} />
              <Route path="/roles" element={<RolesPage />} />
              <Route path="/policies" element={<Policies />} />
              <Route path="/compliance" element={<Compliance />} />
              <Route path="/magpie-success" element={<MagpieSuccess />} />
              <Route path="/checkout/:identifier" element={<Checkout />} />
              <Route path="*" element={<NotFound />} />
            </Routes>
          </Suspense>
        </PageFade>
      </MaintenanceGuard>
    </>
  );
}

const App = () => (
  <QueryClientProvider client={queryClient}>
    <ThemeProvider>
      <LanguageProvider>
        <AuthProvider>
        <TooltipProvider>
          <Toaster />
          <BrowserRouter>
            <AuthAwareShell />
          </BrowserRouter>
        </TooltipProvider>
        </AuthProvider>
      </LanguageProvider>
    </ThemeProvider>
  </QueryClientProvider>
);

export default App;

const App = () => (
  <QueryClientProvider client={queryClient}>
    <ThemeProvider>
      <LanguageProvider>
        <AuthProvider>
        <TooltipProvider>
          <Toaster />
          <BrowserRouter>
            <AuthAwareShell />
          </BrowserRouter>
        </TooltipProvider>
        </AuthProvider>
      </LanguageProvider>
    </ThemeProvider>
  </QueryClientProvider>
);

export default App;