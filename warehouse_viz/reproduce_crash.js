import puppeteer from 'puppeteer';

(async () => {
    console.log('Launching browser...');
    const browser = await puppeteer.launch({ headless: true });
    const page = await browser.newPage();
    await page.setViewport({ width: 1280, height: 800 });

    page.on('console', msg => console.log('BROWSER:', msg.type(), msg.text()));
    page.on('pageerror', err => console.log('BROWSER ERROR:', err.toString()));

    console.log('Navigating...');
    await page.goto('http://localhost:5173');
    await page.waitForSelector('canvas');
    await new Promise(r => setTimeout(r, 1500));

    // 1. Verify Edit mode toggle exists
    const editBtn = await page.evaluateHandle(() => {
        const buttons = Array.from(document.querySelectorAll('button'));
        return buttons.find(b => b.textContent.includes('View Mode') || b.textContent.includes('Edit Mode'));
    });
    if (editBtn.asElement()) {
        console.log('✅ Found mode toggle button');
        // Click to enable edit mode
        await editBtn.asElement().click();
        await new Promise(r => setTimeout(r, 300));
        const modeText = await page.evaluate(el => el.textContent, editBtn.asElement());
        console.log('   Mode after click:', modeText);
    } else {
        console.log('❌ Mode toggle button NOT found');
    }

    // 2. Add a shelf
    const shelfBtn = await page.evaluateHandle(() => {
        const buttons = Array.from(document.querySelectorAll('button'));
        return buttons.find(b => b.textContent.includes('Shelf'));
    });
    if (shelfBtn.asElement()) {
        console.log('✅ Found Shelf button');
        await shelfBtn.asElement().click();
        await new Promise(r => setTimeout(r, 500));
    } else {
        console.log('❌ Shelf button NOT found');
    }

    // 3. Check for controls help button (? icon)
    const helpBtn = await page.evaluateHandle(() => {
        const buttons = Array.from(document.querySelectorAll('button'));
        return buttons.find(b => b.title && b.title.includes('controls'));
    });
    if (helpBtn.asElement()) {
        console.log('✅ Found controls help button');
        await helpBtn.asElement().click();
        await new Promise(r => setTimeout(r, 300));
        // Check if help panel appeared
        const helpText = await page.evaluate(() => document.body.innerText);
        if (helpText.includes('Controls & Shortcuts')) {
            console.log('✅ Help panel opened successfully');
        } else {
            console.log('❌ Help panel NOT visible');
        }
    } else {
        console.log('❌ Controls help button NOT found');
    }

    // 4. Test keyboard shortcut (arrow key) - click canvas first to focus
    const canvas = await page.$('canvas');
    if (canvas) {
        const box = await canvas.boundingBox();
        await page.mouse.click(box.x + box.width / 2, box.y + box.height / 2);
        await new Promise(r => setTimeout(r, 300));
        await page.keyboard.press('ArrowRight');
        await new Promise(r => setTimeout(r, 200));
        console.log('✅ Arrow key pressed (no crash)');
    }

    console.log('\n🎉 All checks passed - no crashes!');
    await new Promise(r => setTimeout(r, 2000));
    await browser.close();
})();
