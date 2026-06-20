const IQOptionBrowser = require('./browser_automation.js');

(async () => {
    const browser = new IQOptionBrowser();
    
    try {
        console.log('[AUTO] Starting automated trading...');
        
        const hasSession = await browser.hasValidSession();
        
        if (!hasSession) {
            console.log('[AUTO] No valid session found. Please run run_headless.js first.');
            process.exit(1);
        }
        
        await browser.init(true); // headless mode
        await browser.navigateToIQOption();
        
        console.log('[AUTO] Using saved session...');
        
        const isLoggedIn = await browser.page.evaluate(() => {
            return document.querySelector('.dashboard, .trading-platform, .account-info') !== null;
        });
        
        if (isLoggedIn) {
            console.log('[AUTO] Already logged in (from saved session)');
            
            const balance = await browser.getBalance();
            console.log('[AUTO] Balance:', balance);
            
            // TODO: ใส่ logic การเทรดของคุณที่นี่
            // await browser.executeTrade('EURUSD', 'CALL', 10, 'M5');
            
        } else {
            console.log('[AUTO] Session expired - please re-run run_headless.js');
        }
        
        await browser.close();
        console.log('[AUTO] Done');
        
    } catch (error) {
        console.error('[AUTO ERROR]', error);
        await browser.close();
    }
})();
