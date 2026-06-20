/**
 * IQ Option Browser Automation
 * Handles Cloudflare Turnstile bypass using Playwright-extra with stealth
 * รองรับ Persistent Browser Profile สำหรับ VPS
 */

const { chromium } = require('playwright-extra');
const StealthPlugin = require('puppeteer-extra-plugin-stealth');
const path = require('path');
const fs = require('fs').promises;

// Use stealth plugin to avoid detection
chromium.use(StealthPlugin());

class IQOptionBrowser {
    constructor() {
        this.browser = null;
        this.context = null;
        this.page = null;
        this.isLoggedIn = false;
        this.profileDir = './browser_profile';
    }

    /**
     * Initialize browser with stealth settings
     * @param {boolean} headless - เปิดโหมด headless หรือไม่ (ค่าเริ่มต้น false)
     */
    async init(headless = false) {
        console.log('[BROWSER] Launching browser...');
        console.log(`[BROWSER] Headless mode: ${headless}`);
        console.log(`[BROWSER] Profile directory: ${this.profileDir}`);
        
        // สร้างโฟลเดอร์ profile ถ้ายังไม่มี
        try {
            await fs.mkdir(this.profileDir, { recursive: true });
        } catch (e) {
            // ไม่ต้องทำอะไรถ้ามีอยู่แล้ว
        }

        this.browser = await chromium.launch({
            headless: headless,
            args: [
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-blink-features=AutomationControlled',
                '--disable-dev-shm-usage',
                '--disable-web-security',
                '--disable-features=IsolateOrigins,site-per-process',
                '--disable-site-isolation-trials',
                '--disable-features=BlockInsecurePrivateNetworkRequests',
                '--disable-features=OutOfBlinkCors',
            ],
            ignoreDefaultArgs: ['--enable-automation'],
        });

        // ใช้ userDataDir เพื่อ Persistent Session
        this.context = await this.browser.newContext({
            userDataDir: this.profileDir,  // 👈 สำคัญ! เก็บ session/cookies
            viewport: { width: 1280, height: 720 },
            userAgent: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            locale: 'en-US',
            timezoneId: 'America/New_York',
            permissions: ['geolocation'],
            deviceScaleFactor: 1,
            hasTouch: false,
            isMobile: false,
            extraHTTPHeaders: {
                'Accept-Language': 'en-US,en;q=0.9',
                'Accept-Encoding': 'gzip, deflate, br',
                'Upgrade-Insecure-Requests': '1',
            }
        });

        this.page = await this.context.newPage();

        // Inject stealth scripts to hide automation
        await this.page.addInitScript(() => {
            // Override navigator properties
            Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
            Object.defineProperty(navigator, 'plugins', { get: () => [1, 2, 3, 4, 5] });
            Object.defineProperty(navigator, 'languages', { get: () => ['en-US', 'en'] });
            
            // Override Chrome DevTools Protocol
            window.chrome = {
                runtime: {}
            };
            
            // Override permissions
            const originalQuery = window.navigator.permissions.query;
            window.navigator.permissions.query = (parameters) => (
                parameters.name === 'notifications' ?
                    Promise.resolve({ state: Notification.permission }) :
                    originalQuery(parameters)
            );
        });

        console.log('[BROWSER] Browser initialized successfully');
    }

    /**
     * Navigate to IQ Option and wait for Cloudflare Turnstile to be solved
     */
    async navigateToIQOption() {
        if (!this.page) throw new Error('Browser not initialized');

        const url = 'https://iqoption.com/en/login';
        console.log('[BROWSER] Navigating to:', url);

        await this.page.goto(url, {
            waitUntil: 'networkidle',
            timeout: 60000
        });

        // Wait for page to load and detect Turnstile
        console.log('[BROWSER] Waiting for page to load...');
        await this.page.waitForTimeout(3000);

        // Check if Turnstile is present
        const turnstileExists = await this.page.evaluate(() => {
            const iframes = document.querySelectorAll('iframe[src*="cloudflare"], iframe[src*="turnstile"]');
            const turnstileDiv = document.querySelector('.cf-turnstile, [data-sitekey]');
            return iframes.length > 0 || turnstileDiv !== null;
        });

        if (turnstileExists) {
            console.log('[BROWSER] Cloudflare Turnstile detected - waiting for manual solve or automatic bypass...');
            
            const solved = await this.waitForTurnstileResolution(60000);
            
            if (solved) {
                console.log('[BROWSER] Turnstile solved successfully');
            } else {
                console.log('[BROWSER] Turnstile not automatically solved - waiting for manual interaction');
                await this.page.waitForTimeout(30000);
            }
        }

        // Verify we can see the login form
        await this.page.waitForSelector('input[type="email"], input[type="text"], input[name="email"]', {
            timeout: 30000
        }).catch(() => {
            console.log('[BROWSER] Login form not found - possibly still blocked by Turnstile');
        });

        return this.page;
    }

    /**
     * Wait for Cloudflare Turnstile to be resolved
     */
    async waitForTurnstileResolution(timeout = 60000) {
        const startTime = Date.now();
        
        while (Date.now() - startTime < timeout) {
            const result = await this.page.evaluate(() => {
                const turnstileIframe = document.querySelector('iframe[src*="cloudflare"], iframe[src*="turnstile"]');
                if (!turnstileIframe) {
                    return true;
                }
                
                const successElement = document.querySelector('.cf-turnstile-success, [data-turnstile-status="solved"]');
                if (successElement) {
                    return true;
                }
                
                const loginForm = document.querySelector('input[type="email"], input[type="text"]');
                if (loginForm && loginForm.offsetParent !== null) {
                    return true;
                }
                
                return false;
            });

            if (result) {
                console.log('[BROWSER] Turnstile solved');
                return true;
            }

            await this.page.waitForTimeout(2000);
        }

        return false;
    }

    /**
     * Log in to IQ Option
     */
    async login(email, password) {
        if (!this.page) throw new Error('Browser not initialized');

        console.log('[BROWSER] Attempting login...');

        try {
            const emailInput = await this.page.waitForSelector('input[type="email"], input[name="email"], input[type="text"]', {
                timeout: 10000
            });
            await emailInput.fill(email);

            const passwordInput = await this.page.waitForSelector('input[type="password"]', {
                timeout: 5000
            });
            await passwordInput.fill(password);

            const loginButton = await this.page.waitForSelector('button[type="submit"], button:has-text("Login"), button:has-text("Sign in")', {
                timeout: 5000
            });
            await loginButton.click();

            console.log('[BROWSER] Login form submitted');

            await this.page.waitForNavigation({
                waitUntil: 'networkidle',
                timeout: 30000
            });

            await this.page.waitForTimeout(3000);

            const loggedIn = await this.page.evaluate(() => {
                const dashboard = document.querySelector('.dashboard, .trading-platform, [data-testid="dashboard"]');
                return dashboard !== null;
            });

            if (loggedIn) {
                console.log('[BROWSER] Login successful');
                this.isLoggedIn = true;
                await this.saveSession();
                return true;
            } else {
                console.log('[BROWSER] Login may have failed - check for errors');
                return false;
            }

        } catch (error) {
            console.error('[BROWSER] Login error:', error.message);
            return false;
        }
    }

    /**
     * Execute a trade directly through the browser
     */
    async executeTrade(symbol, direction, amount, expiry) {
        if (!this.page || !this.isLoggedIn) {
            throw new Error('Not logged in or browser not initialized');
        }

        console.log(`[TRADE] Executing ${direction} ${symbol} ${amount} ${expiry}`);

        await this.page.goto('https://iqoption.com/en/trading', {
            waitUntil: 'networkidle'
        });

        await this.page.waitForTimeout(5000);

        const assetSelector = `[data-asset="${symbol}"], .asset-${symbol}`;
        await this.page.waitForSelector(assetSelector, { timeout: 10000 }).catch(() => {
            console.log(`[TRADE] Asset ${symbol} not found in list`);
        });

        const directionSelector = direction === 'CALL' ? '.call-button, [data-direction="call"]' : '.put-button, [data-direction="put"]';
        await this.page.click(directionSelector);

        const amountInput = await this.page.waitForSelector('input[type="number"], .amount-input');
        await amountInput.fill(String(amount));

        const expirySelector = `[data-expiry="${expiry}"], .expiry-${expiry}`;
        await this.page.click(expirySelector);

        const buyButton = await this.page.waitForSelector('button:has-text("Buy"), button:has-text("Sell"), .confirm-trade');
        await buyButton.click();

        console.log(`[TRADE] Trade executed: ${direction} ${symbol} ${amount} ${expiry}`);

        return {
            success: true,
            timestamp: new Date().toISOString(),
            symbol,
            direction,
            amount,
            expiry
        };
    }

    /**
     * Get account balance from browser
     */
    async getBalance() {
        if (!this.page || !this.isLoggedIn) {
            throw new Error('Not logged in or browser not initialized');
        }

        const balance = await this.page.evaluate(() => {
            const balanceElement = document.querySelector('.balance, .account-balance, [data-testid="balance"]');
            if (balanceElement) {
                const text = balanceElement.textContent;
                const match = text.match(/[\d,]+\.?\d*/);
                if (match) {
                    return parseFloat(match[0].replace(/,/g, ''));
                }
            }
            return null;
        });

        return balance;
    }

    /**
     * Save session data (cookies and metadata)
     */
    async saveSession() {
        try {
            if (!this.context) {
                console.log('[BROWSER] No context to save');
                return;
            }

            const cookies = await this.context.cookies();
            const sessionData = {
                cookies: cookies,
                timestamp: new Date().toISOString(),
                url: this.page ? this.page.url() : null,
                isLoggedIn: this.isLoggedIn
            };

            const sessionFile = path.join(this.profileDir, 'session_data.json');
            await fs.writeFile(sessionFile, JSON.stringify(sessionData, null, 2));
            console.log('[BROWSER] Session saved successfully to:', sessionFile);
            
        } catch (error) {
            console.error('[BROWSER] Error saving session:', error.message);
        }
    }

    /**
     * Load session data (check if session exists)
     */
    async loadSession() {
        try {
            const sessionFile = path.join(this.profileDir, 'session_data.json');
            const data = await fs.readFile(sessionFile, 'utf8');
            const sessionData = JSON.parse(data);
            console.log('[BROWSER] Session loaded from:', sessionFile);
            console.log(`[BROWSER] Session created: ${sessionData.timestamp}`);
            return sessionData;
        } catch (error) {
            console.log('[BROWSER] No existing session found');
            return null;
        }
    }

    /**
     * Check if session is valid (not expired)
     */
    async hasValidSession() {
        const session = await this.loadSession();
        if (!session) return false;
        
        // Check if session is less than 30 days old
        const sessionAge = Date.now() - new Date(session.timestamp).getTime();
        const maxAge = 30 * 24 * 60 * 60 * 1000; // 30 days
        return sessionAge < maxAge && session.isLoggedIn === true;
    }

    /**
     * Close browser and save session
     */
    async close() {
        await this.saveSession();
        if (this.browser) {
            await this.browser.close();
            console.log('[BROWSER] Browser closed');
        }
    }

    /**
     * Take screenshot for debugging
     */
    async screenshot(filename = 'screenshot.png') {
        if (this.page) {
            const screenshotPath = path.join(__dirname, 'screenshots', filename);
            await fs.mkdir(path.dirname(screenshotPath), { recursive: true });
            await this.page.screenshot({ path: screenshotPath, fullPage: true });
            console.log('[BROWSER] Screenshot saved:', screenshotPath);
            return screenshotPath;
        }
    }
}

// Export for use in other modules
module.exports = IQOptionBrowser;

// Example usage
if (require.main === module) {
    (async () => {
        const browser = new IQOptionBrowser();
        try {
            // ตรวจสอบว่ามี session อยู่แล้วหรือไม่
            const hasSession = await browser.hasValidSession();
            
            if (hasSession) {
                console.log('[INFO] Found valid session! Loading...');
                await browser.init(true); // headless mode
                await browser.navigateToIQOption();
                
                // ใช้ session เดิม
                const balance = await browser.getBalance();
                console.log('[INFO] Balance:', balance);
                
                await browser.close();
            } else {
                console.log('[INFO] No valid session found. Starting in headful mode for login...');
                await browser.init(false); // headful mode
                await browser.navigateToIQOption();
                
                console.log('\n[INFO] Please log in manually in the browser window.');
                console.log('[INFO] The browser will stay open for 60 seconds.');
                console.log('[INFO] After login, the session will be saved automatically.\n');
                
                await browser.page.waitForTimeout(60000);
                
                // ตรวจสอบว่า login สำเร็จหรือไม่
                const loggedIn = await browser.page.evaluate(() => {
                    return document.querySelector('.dashboard, .trading-platform, .account-info') !== null;
                });
                
                if (loggedIn) {
                    browser.isLoggedIn = true;
                    await browser.saveSession();
                    console.log('[SUCCESS] Login detected! Session saved.');
                } else {
                    console.log('[WARN] Login not detected. Session may be incomplete.');
                }
                
                await browser.close();
            }
            
        } catch (error) {
            console.error('Error:', error);
            await browser.close();
        }
    })();
}
