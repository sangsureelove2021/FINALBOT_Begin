const IQOptionBrowser = require('./browser_automation.js');

(async () => {
    const browser = new IQOptionBrowser();
    
    try {
        console.log('='.repeat(60));
        console.log('STEP 1: First-time login (headful mode)');
        console.log('='.repeat(60));
        console.log('กรุณาทำตามขั้นตอน:');
        console.log('1. หน้าต่างเบราว์เซอร์จะเปิดขึ้น');
        console.log('2. ล็อกอิน DeepSeek หรือ IQ Option ด้วยตัวเอง');
        console.log('3. หลังจากล็อกอินสำเร็จ Session จะถูกเซฟอัตโนมัติ');
        console.log('='.repeat(60));
        
        await browser.init(false); // headless: false
        await browser.navigateToIQOption();
        
        console.log('\n[WAIT] กำลังรอให้คุณล็อกอิน... (60 วินาที)');
        await browser.page.waitForTimeout(60000);
        
        const loggedIn = await browser.page.evaluate(() => {
            return document.querySelector('.dashboard, .trading-platform') !== null;
        });
        
        if (loggedIn) {
            console.log('[SUCCESS] Login successful!');
            browser.isLoggedIn = true;
            await browser.saveSession();
            console.log('[OK] Session saved to ./browser_profile/');
        } else {
            console.log('[WARN] Login not detected - session may be incomplete');
        }
        
        await browser.close();
        
        console.log('\n' + '='.repeat(60));
        console.log('STEP 2: เปลี่ยนเป็น headless mode');
        console.log('='.repeat(60));
        console.log('รัน: node run_auto.js');
        console.log('='.repeat(60));
        
    } catch (error) {
        console.error('[ERROR]', error);
        await browser.close();
    }
})();
