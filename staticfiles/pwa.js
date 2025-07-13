if ('serviceWorker' in navigator) {
  window.addEventListener('load', () => {
    navigator.serviceWorker.register('/serviceworker.js')
      .then(registration => {
        console.log('Service Worker registered: ', registration);
        
        // Check for updates every hour
        setInterval(() => {
          registration.update();
        }, 60 * 60 * 1000);
      })
      .catch(error => {
        console.log('Service Worker registration failed: ', error);
      });
  });
}

// Install prompt handling
let deferredPrompt;
window.addEventListener('beforeinstallprompt', (e) => {
  e.preventDefault();
  deferredPrompt = e;
  
  // Show your custom install button/prompt here
  showInstallPromotion();
});

function showInstallPromotion() {
  // Implement your custom install UI here
  console.log('PWA install available');
}

function installPWA() {
  if (deferredPrompt) {
    deferredPrompt.prompt();
    deferredPrompt.userChoice.then((choiceResult) => {
      if (choiceResult.outcome === 'accepted') {
        console.log('User accepted install');
      }
      deferredPrompt = null;
    });
  }
}

// Check if app is launched from home screen
window.addEventListener('load', () => {
  if (window.matchMedia('(display-mode: standalone)').matches) {
    console.log('Launched as PWA');
    document.documentElement.classList.add('pwa-mode');
  }
});