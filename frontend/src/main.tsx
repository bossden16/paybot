if (window.XEND_LOG) window.XEND_LOG('loading_dependencies');

import './lib/api';
import { createRoot } from 'react-dom/client';
import App from './App';
import './index.css';

if (window.XEND_LOG) window.XEND_LOG('mounting_application');

function clearCurtain() {
  const curtain = document.getElementById('boot-console');
  if (curtain) {
    curtain.style.opacity = '0';
    setTimeout(() => curtain.remove(), 600);
  }
}

try {
  const rootElement = document.getElementById('root');
  if (!rootElement) throw new Error('DOM_ROOT_MISSING');

  const root = createRoot(rootElement);
  root.render(<App />);

  if (window.XEND_LOG) window.XEND_LOG('system_ready');

  // Short delay to allow first paint
  setTimeout(clearCurtain, 1200);

} catch (error) {
  if (window.XEND_FATAL) {
      window.XEND_FATAL('REACT_MOUNT_FAILED', error as Error);
  }
}
