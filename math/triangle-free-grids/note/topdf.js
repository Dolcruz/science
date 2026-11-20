const { chromium } = require('playwright');
(async () => {
  const [,, inp, out] = process.argv;
  const b = await chromium.launch(); const p = await b.newPage();
  await p.goto('file://' + inp); await p.waitForSelector('body[data-ready]', {timeout: 30000});
  await p.pdf({ path: out, format: 'A4', margin: {top:'16mm',bottom:'16mm',left:'14mm',right:'14mm'}, printBackground: true });
  await b.close();
})();
